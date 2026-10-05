# CLAUDE.md — senal-xau-trading (bot de señales XAU/USD en M15)

Este archivo es la **memoria del proyecto**. Claude lo lee al empezar cada sesión.
Regla principal: **cada cambio de código que tome una decisión nueva se refleja
aquí en el mismo commit** (sección "Decisiones" y/o "Historial de cambios").
El usuario no debería tener que repetir nada que ya esté escrito aquí.

## Cómo trabajar en este repo

- Idioma: todo en **español** (conversación, comentarios, mensajes de Discord, commits).
- Antes de cambiar algo, leer este archivo completo y respetar las decisiones vigentes.
- Si una petición nueva contradice una decisión anterior, **preguntar** antes de cambiarla
  y, si se confirma, actualizar la decisión aquí (no borrar el historial).
- Flujo de trabajo: los cambios se hacen en la rama `claude/code-review-audit-wx91q6`, se
  abre un PR contra `main` y **el usuario hace el merge**. Nunca push directo a `main`.
- Tras cada merge: **redeploy manual en Northflank** (avisar siempre al usuario).

## Objetivo del bot

Bot de señales **solo técnico** para **XAU/USD** en velas de **15 minutos (M15)**, que
publica en **Discord** y corre en **Northflank**.

Forma parte de una **escalera de temporalidades** con otros dos bots del usuario:

| Bot | Repo | Temporalidad | Despliegue |
|---|---|---|---|
| ATLAS | `BOT_ATLAS` | M5 (señales) + M15 (solo confirma) | Northflank |
| **Señales** | `senal-xau-trading` | **M15** | **Northflank** |
| Fusión | `xauusd-fusion-render` | M30 | Render |

Funciones: estructura (BOS/CHoCH), EQH/EQL, FVG, barridos de liquidez, patrones
chartistas (Doble Techo/Suelo, HCH, banderas/banderines), RSI, ATR, score de confianza,
multi-timeframe (H1/H4/D1), seguimiento WIN/LOSS con aviso en Discord, `!stats` y botón
de consulta del estado.

## Decisiones (vigentes)

Formato: `AAAA-MM-DD — decisión — motivo`.

- 2026-09-30 — **Temporalidad M15** (`GRANULARIDAD = "15min"`). Escalera ATLAS M5 /
  señales M15 / fusión M30 para que dos bots no analicen la misma temporalidad — decisión del usuario.
- 2026-09-30 — **Score mínimo 70**: por debajo la señal se descarta y **no se envía**
  (antes calculaba "DESCARTADA" pero la mandaba igual) — decisión del usuario.
- 2026-10-04 — **Solo se envían las señales ⭐ PREMIUM** (score ≥ 80, `SOLO_PREMIUM = True`).
  Igual en los tres bots — decisión del usuario.
- 2026-10-05 — **Filtro de tendencia = EMA20 diaria Y dirección del día** (apertura del día
  en hora Madrid vs precio actual) **tienen que coincidir**: ambas alcistas → solo BUY;
  ambas bajistas → solo SELL; si no coinciden ("mixta") no sale ninguna señal. Si una de
  las dos no tiene dato, manda la otra. Se aplica a patrones, banderas, barridos y
  estructura; se quitó el CHoCH contra tendencia. Mismo filtro en los tres bots. Motivo:
  el 05/10 fusión dio BUY y ATLAS SELL a la vez — decisión del usuario.
- 2026-10-05 — El aviso en Discord de cambios del filtro de tendencia **solo lo manda
  ATLAS** (aquí no, para no triplicarlo) — decisión del usuario.
- 2026-10-05 — **Resultado de cada señal en Discord**: ✅ WIN (tocó TP), ❌ LOSS (tocó SL),
  ⌛ TIMEOUT (72 h sin tocar ninguno), como ATLAS — decisión del usuario.
- 2026-09-30 — **Una API key de Twelve Data por bot** (compartida, la cuota de 800/día se
  agotaba hacia las 21:00 Madrid). La pone el usuario en Northflank — decisión del usuario.

Decisiones técnicas (tomadas por Claude; el usuario puede cambiarlas):

- 2026-09-26 — Solo se analizan **velas cerradas**; cada ruptura/patrón se evalúa una
  sola vez (clave por timestamp) y solo en la vela que **cruza** el nivel.
- 2026-09-26 — Todo error que va a logs o Discord pasa por `_sin_secretos()` (las URLs de
  requests llevan `?apikey=`). Escritura atómica (`_escribir_atomico`) del historial y del
  JSON de señales abiertas.
- Seguimiento WIN/LOSS con velas M15 cerradas: si una vela toca SL y TP a la vez → LOSS
  (no se sabe cuál fue primero). TIMEOUT a las 72 h (`TIMEOUT_HORAS_SEGUIMIENTO`).
- SL = swing opuesto ± 1.2×ATR(14) (`MULTIPLICADOR_ATR_SL`); TP = zona de liquidez
  (EQH/EQL) o ratio 1:2 si no hay.
- Horario operativo 09:00–22:00 Madrid. Pausa de fin de semana: viernes 22:00 → domingo
  12:00 (Madrid). Tope de estructura: 6 señales/día.
- `MULTIPLICADOR_LIQUIDEZ_VOLUMEN = 1.1` (ATLAS usa 0.5).

## Pendiente / ideas

- Redondear el Entry a 2 decimales en los mensajes (a veces sale p. ej. 4152.53509).
- Idea comentada: que ATLAS confirme señales de este bot y de fusión (confirmación entre bots).
- El `Dockerfile` no tiene `ENV PYTHONUNBUFFERED=1` (fusión y ATLAS sí): sin él, los
  `print` pueden tardar en verse en los logs de Northflank.

## Arquitectura

Un solo archivo: `senal_trading_xauusd.py` (bot de Discord con `discord.py`, bucle cada
`INTERVALO_REVISION_MINUTOS` = 5 min, servidor HTTP de salud en `PORT`).

Flujo de `revisar_senal()`: fin de semana / horario → velas M15 (Twelve Data, respaldo
Alpha Vantage) → solo cerradas → `_seguir_senales_abiertas()` (WIN/LOSS/TIMEOUT y aviso a
Discord) → si hay vela nueva: tendencia combinada → patrones, banderas, barrido,
estructura → score → enviar + abrir seguimiento + CSV.

Archivos de estado (en el directorio de trabajo, o donde digan las variables):
- `historial_senales.csv` — una fila por señal con `resultado` PENDIENTE/WIN/LOSS/TIMEOUT.
- `senales_abiertas.json` — señales que aún no tocaron SL/TP (sobrevive a reinicios si
  el disco es persistente).

## Configuración / variables de entorno

| Variable | Para qué | Obligatoria |
|---|---|---|
| `DISCORD_BOT_TOKEN` | Token del bot de Discord | Sí |
| `DISCORD_CHANNEL_ID` | Canal donde publica | Sí |
| `TWELVE_DATA_API_KEY` | Velas XAU/USD (clave propia de este bot) | Sí |
| `ALPHA_VANTAGE_API_KEY` | Respaldo de velas | No |
| `TWELVE_DATA_BACKUP_API_KEY` | Segunda clave de Twelve Data | No |
| `ARCHIVO_HISTORIAL` / `ARCHIVO_SENALES_ABIERTAS` | Rutas de los archivos de estado | No |
| `PORT` | Puerto del health check (8080) | No |

El bot necesita el intent **Message Content** (para `!stats`).

## Despliegue (Northflank)

- Rama desplegada: `main`. Build por `Dockerfile`.
- Plan gratuito: **sin CD**. Tras cada merge hay que ir a Northflank → *Builds* → último
  build → *Deploy* (lo hace el usuario; Claude no tiene acceso a Northflank).

## Historial de cambios

- 2026-09-26 — PR #1: auditoría (velas cerradas, rupturas por cruce, claves por timestamp,
  `_sin_secretos`, escritura atómica, caché de velas con lock, horario de mercado USA,
  envío a Discord con control de errores).
- 2026-09-30 — PR #2: score mínimo 70; las señales por debajo ya no se envían.
- 2026-10-04 — PR #3: solo PREMIUM (score ≥ 80).
- 2026-10-05 — PR #4: filtro de tendencia EMA20 diaria + dirección del día (deben coincidir).
- 2026-10-05 — PR #5: aviso en Discord cuando una señal toca TP, SL o expira.
- 2026-10-05 — Creado este `CLAUDE.md`.
