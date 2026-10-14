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
publica en **Discord** y corre en **Northflank**. Desde el 2026-10-08 lleva además, en
prueba, dos estrategias para el **Nasdaq (USTEC)**: la "zona de ruido" (desde el 2026-10-08) y la
"R1" de solo compras (desde el 2026-10-09) (ver Decisiones).

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

- 2026-10-09 — **Nasdaq R1, SOLO COMPRAS, EN PRUEBA (demo)** (`NASDAQ_R1_ACTIVO = True`), del
  vídeo de TikTok de @hobbiecode que mandó el usuario: pivotes clásicos con la **sesión de
  ayer del QQQ** (P = (máx + mín + cierre)/3, R1 = 2P − mín); la primera vez en el día que
  **3 velas M15 seguidas** (desde las 09:30 NY) tienen el mínimo por encima del R1 → compra al
  cierre de la tercera (como tarde a las 15:00 NY), **SL −0,2 %** ("30 puntos" con el Nasdaq a
  15.000), **TP +0,5 %** (2,5:1), cierre al final de la sesión si no toca nada; una al día.
  Avisos 📊 (📊🟢 compra, 📊✅ TP, 📊❌ SL, 📊⏹️ cerrar), con una nota si la zona de ruido está
  comprada a la vez. Laboratorio (NAS100, coste 0,8 pb): +0,12 / +0,19 / +0,27 R por operación
  en 2010–15 / 2016–20 / 2026 (pivotes de la sesión; con pivotes del día completo +0,15 /
  +0,30 / +0,41 R y 11/11 años positivos), ~1 por semana, peor caída ~−10 R; gana a "comprar
  siempre a la misma hora" y con 2–4 velas y SL/TP de 0,15–0,30 %. **Las ventas (espejo bajo
  el S1) pierden** (+0,07 / −0,15 / −0,24 R): el usuario decidió solo compras. De los otros
  tres vídeos (vela de las 10:00 NY, primera vela M15 de NY con retesteo, acumulación antes
  de las 09:30) ninguno pasa; "15 de cada 21 días sigue la dirección de la vela de las 10"
  sale un 48–52 % — decisión del usuario.
- 2026-10-08 — **Nasdaq (USTEC) "zona de ruido", EN PRUEBA (demo), conviviendo con la FVG
  del oro** (`NASDAQ_ACTIVO = True`). Estudio *Beat the Market* (Zarattini, Aziz y Barbon,
  2024), versión banda + VWAP, replicada en GitHub (`Chris-ZZX/spy-intraday-momentum`,
  `codecat-ops/zarattini-2024-momentum-spy`…). Reglas: ruido a cada hora = media de
  |cierre a esa hora / apertura − 1| de las 14 sesiones anteriores; UB = máx(apertura, cierre
  de ayer)×(1+ruido), LB = mín(apertura, cierre de ayer)×(1−ruido); solo a las :00/:30 NY
  desde las 10:00, con la vela de 5 min recién cerrada: cierre > máx(UB, VWAP) → comprado,
  < mín(LB, VWAP) → vendido, entre medias → fuera; todo se cierra a las 16:00 NY (22:00
  Madrid). Datos del ETF **QQQ** (Twelve Data); avisos con distancias en % para aplicarlas a
  USTEC: 📈🟢/🔴 entrada con stop de referencia, 📈🔁 mover stop (si cambia ≥ 0,05 %), 📈⏹️
  cerrar con resultado en %. Laboratorio (2026-10-08, NAS100 Oanda 2010–20 y 2026, coste
  0,8 pb): +4,9 / +5,6 / +5,3 % al año sin apalancar, ~4 operaciones por semana, acierto
  ~37 %; las 9 combinaciones de ventana/multiplicador probadas ganan en 2010–15 y 2016–20.
  El **S&P 500 se descartó** (+5,0 / +1,0 / −6,2 %: la ventaja se ha apagado) y también el
  ORB de 5 min (gana solo en algunos años). Margen fino: con un spread de USTEC de más de
  ~3 puntos la ventaja casi desaparece — decisión del usuario.
- 2026-10-06 — **Estrategia FVG del usuario, en modo EXPERIMENTAL** (`ESTRATEGIA_SENALES =
  "fvg"`, para cuenta demo; la lógica clásica queda desactivada y vuelve con `"clasica"`):
  sesgo del día (EMA20 diaria + dirección del día) → FVG a favor sin rellenar en H1 y M30
  (24 h) → entrada al rechazo de un FVG M15 (últimas 4 h). Continuación tras cerrar fuera del
  máximo/mínimo de ayer y giro tras un barrido de esos niveles. SL tras el FVG M15 + 0,5×ATR,
  TP 2R, 07–20 UTC, máx. 1 al día (antes 3; ver abajo), una a la vez. Es la variante V4 del laboratorio
  (`BOT_ATLAS/backtest`, ronda 4), que **no pasa con costes** (−0,05/−0,10 R en 2012–17 y
  2018–22; +0,23 R en 2026): se deja correr para observarla en vivo — decisión del usuario.
- 2026-10-07 — **FVG: máximo 1 señal al día** (`FVG_MAX_POR_DIA = 1`; como mucho 5 por
  semana; antes 3 al día). Es un tope, no un mínimo: los días sin condiciones no hay señal.
  Backtest con el tope: ~2,4 señales por semana (señal en ~48 % de los días), −0,12 R en
  2012–17, −0,03 R en 2018–22, +0,04 R en 2026 (con 3/día: −0,06 / −0,09 / +0,23 R) —
  decisión del usuario.
- 2026-10-06 — **`!stats` como el de ATLAS**: separa la estrategia FVG de la clásica, con
  acierto, Profit Factor, resultado acumulado y drawdown en R, desglose por tipo de evento y
  señales abiertas — decisión del usuario.
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
- 2026-10-12 — **Avisos del Nasdaq con niveles de USTEC orientativos**: entrada "a mercado ahora,
  USTEC ≈ X" y SL/TP/stop/resultado también en **puntos de USTEC** (≈, con
  `NASDAQ_RATIO_USTEC_QQQ` = 41,15: USTEC ~30.700 con QQQ 746,10 el 12/10). La zona de ruido
  explica que **no tiene TP** (se sale con 📈⏹️ CERRAR o a las 22:00) y que un stop en el
  bróker conviene ponerlo más lejos (p. ej. 0,2 %). Motivo: el usuario no veía entrada ni TP
  en el aviso — decisión del usuario.
- 2026-10-12 — **"ORO -- estado" una vez por hora** (`INTERVALO_ORO_MINUTOS = 60`, antes 10) y
  solo en el horario operativo (09:00–22:00 Madrid), con los precios redondeados a 2
  decimales. Motivo: salía cada 10 minutos (también de noche) con el precio sin redondear
  (p. ej. 4167.53561) — decisión del usuario.
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

- ~~Redondear el Entry a 2 decimales~~: hecho en "ORO -- estado" (2026-10-12); la FVG ya redondea
  (la lógica clásica, desactivada, no).
- Idea comentada: que ATLAS confirme señales de este bot y de fusión (confirmación entre bots).
- Revisar dentro de unas semanas los resultados de la FVG experimental (`!stats`) frente
  al backtest.
- Nasdaq: ~~confirmar que Twelve Data da el QQQ~~ (confirmado el 2026-10-12: llegó el primer
  aviso 📈 VENTA); comprobar el spread real de
  USTEC en el bróker de 15:30 a 22:00 Madrid; comparar `!stats` con el laboratorio
  (+0,02 % por operación de media, unas 4 por semana). Volver a probar el S&P 500 con datos
  nuevos dentro de unos meses.
- Nasdaq R1: comparar `!stats` con el laboratorio (+0,12 a +0,27 R por operación, ~1 por
  semana, acierto ~43 %).
- **Prueba manual del usuario: "📦 Nasdaq 16:30"** (desde 2026-10-11, NO está en el bot). Regla
  (USTEC M15, hora Madrid): marcar máximo/mínimo de la vela de las **15:00**; si la vela de las
  **16:30** cierra **fuera** de ese rango con un cuerpo **≥ 2× el cuerpo medio** de las velas
  anteriores → entrar en esa dirección (compra o venta); **stop 0,2 %**; salir al cierre de la
  **5.ª vela** (~18:00); si no cumple, ese día no se opera. El usuario apunta cada operación
  (fecha, lado, entrada, stop, salida, resultado y si había aviso 📈/📊 a favor) y las manda
  tras 10–15 operaciones. Si van en línea con el laboratorio → añadirla al bot como
  "📦 NASDAQ 16:30". Laboratorio (NAS100 2010–15 / 2016–20 / 2026, coste 0,8 pb): +0,07 /
  +0,28 / +0,79 R por operación (2026 solo 12 operaciones), acierto 45–58 %, ~1 por semana.
  Descartado de su mismo patrón (decisión del usuario tras ver los datos): entrar en la
  ruptura de la vela de las **15:15** (−0,05 / +0,26 / −0,17 R) y cualquier ruptura de la vela
  de las 15:00 sin la confirmación de las 16:30 (la dirección sale ~50 %: el impulso de la
  apertura va igual de fuerte a favor que en contra).
  - **2026-10-12 — OJO CON LA HORA:** el MetaTrader del usuario muestra la **hora del servidor
    = Nueva York + 7 h = Madrid + 1 h** (lo vimos en su captura: móvil 16:28, vela en curso
    17:15). Las horas que dice el usuario son las **de su gráfico**: "vela de las 15:00" = 08:00
    NY (14:00 Madrid) y "vela de las 16:30" = **09:30 NY, la apertura de Wall Street** (15:30
    Madrid). Rehecho con esas horas (stop 0,2 %, 5 velas): vela de apertura con cuerpo ≥ 1,5×
    +0,05 / +0,08 / +0,10 R (≥ 2×: 0,00 / +0,11 / +0,12 R); la entrada A (vela 15:15 del gráfico)
    pierde (−0,13 / −0,09 / −0,13 R). Los +0,07 / +0,28 / +0,79 R de arriba son de la vela de
    las 10:30 NY = **17:30 en su gráfico** (16:30 Madrid), que sale más fuerte.
  - **Registro de la prueba** (lotes en cuenta demo de 200 €; aviso dado: con 0,5 lotes un
    stop de 0,2 % es ~15 % de la cuenta → recomendado 1 posición de ≤ 0,1 lotes):

    | Fecha | Vela confirmación (gráfico) | Lado | Operaciones | Resultado |
    |---|---|---|---|---|
    | 2026-10-12 | 16:30 (apertura), cuerpo grande | Venta | 3 (0,5 + 0,3 + 0,3 lotes; la 1.ª antes de la confirmación) | +58,84 € |
    | 2026-10-13 | 16:30 (apertura): vela verde enorme que cierra muy por encima de la caja → **COMPRA** | — (no la tomó) | 2 ventas en la vela de las 16:15, antes de la confirmación | Pérdida (importe pendiente). **Según el usuario la estrategia sí habría servido** (dirección correcta; con su TP de 30 € y margen de 5 velas para entrar); con la regla escrita (entrada al cierre de las 16:30, stop 0,2 %, salida a la 5.ª vela) habría quedado cerca del stop (~−1 R). Lección del usuario: no entrar antes del cierre de la vela de las 16:30 y confiar en la señal. |

    Nota (2026-10-14): con la entrada al cierre de las 16:30, un TP pequeño sube el acierto pero
    pierde en 10 años (TP 0,1 % ≈ 30 pts: 66 % de acierto, −0,05 / −0,04 / +0,08 R); lo que gana
    es dejar correr (5.ª vela: +0,05 / +0,08 / +0,10 R; TP 0,4 % = 2:1: +0,02 / +0,06 / +0,22 R).
    Mejor fijar el TP en puntos/% y no en € (depende del lote).
- **Segunda prueba manual del usuario: "🌙 caja de las 22:45"** (desde 2026-10-13, NO está en el bot).
  Hora de su gráfico: vela de las **22:45** = 15:45 NY (última media hora antes del cierre de
  Wall Street); caja con esa vela (y las siguientes) y ruptura con cuerpo durante la noche →
  entrar a favor. Ejemplos del usuario: 8, 9 y 12/10 (dos al alza y uno a la baja; los tres
  ganadores). Laboratorio (NAS100 M15 24 h, coste 0,8 pb, 12 versiones: caja de 1/2/4 velas,
  salida a 4 h/8 h, TP 2R o SL 0,2 %/TP 0,5 %): **ninguna gana en los tres tramos** (p. ej.
  caja 22:45, SL al otro lado, salida a 4 h: −0,05 / −0,04 / −0,19 R); tras la ruptura el
  recorrido a favor y en contra es el mismo (días con más a favor 39–51 %). Se le recomendó no
  operarla en real (spread nocturno más alto); el usuario la prueba en demo igualmente y
  apunta stop y salida fijados de antemano. Las velas de 22:30/22:45 tampoco muestran patrón
  de dirección (mismo color 46–51 %, siguen la dirección del día 48–51 %).
  - **Registro de la prueba 🌙:**

    | Fecha (noche) | Ruptura de la caja | Operación | Resultado |
    |---|---|---|---|
    | 2026-10-13 → 14 | Al alza (caja ~30.535–30.570) | Compra ~30.585 → cierre ~30.652 (madrugada del 14) | ✅ Ganadora, ~+67 puntos (importe pendiente) |

## Arquitectura

Un solo archivo: `senal_trading_xauusd.py` (bot de Discord con `discord.py`, bucle cada
`INTERVALO_REVISION_MINUTOS` = 5 min, servidor HTTP de salud en `PORT`).

Flujo de `revisar_senal()`: fin de semana / horario → velas M15 (Twelve Data, respaldo
Alpha Vantage; 500 velas con la FVG) → solo cerradas → `_seguir_senales_abiertas()`
(WIN/LOSS/TIMEOUT y aviso a Discord) → si hay vela nueva: con la FVG, `_revisar_fvg()`
(rejuega `fvg_simular()` sobre las 500 velas + diarias cacheadas 1 h y, si la última vela da
entrada y no hay otra FVG abierta, envía "🧪 FVG EXPERIMENTAL" + seguimiento + CSV); con la
clásica, tendencia combinada → patrones, banderas, barrido, estructura → score → enviar.
`fvg_simular()` da exactamente las mismas entradas que el laboratorio (verificado en
2019–2020 y 2026).

Nasdaq: bucle propio `revisar_nasdaq_periodicamente` (cada 5 min, lun–vie, 10:00–16:30 NY,
independiente del horario y de la pausa del oro). `revisar_nasdaq()` solo pide datos cuando
cerró una vela M15 (:00/:15/:30/:45) o terminó la sesión (~26 consultas al día: 1300 velas
de 5 min del QQQ en hora de Nueva York), rejuega el día con `ruido_simular_dia()` (decide a
las :00/:30) y con `r1_simular_dia()` (`_procesar_r1`, avisos en `avisados_r1`) y manda
los avisos que falten. Solo guarda qué avisos se mandaron (`nasdaq_estado.json`): tras un
reinicio sigue avisando de los stops y del cierre de una operación ya avisada, y no avisa
entradas de hace más de 20 min **ni las decididas más de 5 min antes de arrancar el proceso**
(`_entrada_antigua`): el disco de Northflank no guarda `nasdaq_estado.json` entre despliegues
y el 12/10 un redeploy repitió la VENTA de las 16:30 a las 16:47. Cada operación cerrada va a `historial_nasdaq.csv`
(resultado en %). `ruido_simular_dia()` da las mismas operaciones que el laboratorio
(1266 / 907 / 95 en 2010–15 / 2016–20 / 2026); `r1_simular_dia()` también (453 / 356 / 48,
+0,13 / +0,20 / +0,27 R). Cada operación R1 cerrada va a `historial_nasdaq_r1.csv` (en R).

Archivos de estado (en el directorio de trabajo, o donde digan las variables):
- `historial_senales.csv` — una fila por señal con `resultado` PENDIENTE/WIN/LOSS/TIMEOUT.
- `senales_abiertas.json` — señales que aún no tocaron SL/TP (sobrevive a reinicios si
  el disco es persistente).
- `historial_nasdaq.csv` — una fila por operación del Nasdaq cerrada (entrada, salida, % y motivo).
- `nasdaq_estado.json` — avisos del Nasdaq ya mandados hoy (zona de ruido y R1).
- `historial_nasdaq_r1.csv` — una fila por operación R1 cerrada (TP/SL/CIERRE y resultado en R).

## Configuración / variables de entorno

| Variable | Para qué | Obligatoria |
|---|---|---|
| `DISCORD_BOT_TOKEN` | Token del bot de Discord | Sí |
| `DISCORD_CHANNEL_ID` | Canal donde publica | Sí |
| `TWELVE_DATA_API_KEY` | Velas XAU/USD (clave propia de este bot) | Sí |
| `ALPHA_VANTAGE_API_KEY` | Respaldo de velas | No |
| `TWELVE_DATA_BACKUP_API_KEY` | Segunda clave de Twelve Data | No |
| `ARCHIVO_HISTORIAL` / `ARCHIVO_SENALES_ABIERTAS` | Rutas de los archivos de estado | No |
| `ARCHIVO_HISTORIAL_NASDAQ` / `ARCHIVO_ESTADO_NASDAQ` / `ARCHIVO_HISTORIAL_NASDAQ_R1` | Rutas de los archivos del Nasdaq | No |
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
- 2026-10-06 — Estrategia FVG experimental (ESTRATEGIA_SENALES = "fvg"), `!stats` como el de
  ATLAS y `PYTHONUNBUFFERED=1` en el Dockerfile.
- 2026-10-07 — FVG experimental: máximo 1 señal al día.
- 2026-10-08 — Nasdaq (USTEC) "zona de ruido" en prueba, con datos del QQQ, avisos propios
  (📈) y apartado en `!stats`.
- 2026-10-09 — Nasdaq R1 (solo compras) en prueba: avisos 📊, historial en R y apartado en
  `!stats`; el QQQ se pide en cada vela M15 (~26 consultas al día).
- 2026-10-12 — "ORO -- estado" cada hora (antes cada 10 min), solo en horario operativo y con
  el precio redondeado. Confirmado en vivo: Twelve Data da el QQQ con la clave gratis (primer
  aviso 📈 VENTA a las 16:30 Madrid).
- 2026-10-12 — Nasdaq: avisos con USTEC ≈ y puntos; sin avisos repetidos tras un redeploy.
- 2026-10-11 — Laboratorio del patrón del usuario (vela de las 15:00 / confirmación a las
  16:30): queda como prueba manual del usuario (ver "Pendiente"); sin cambios en el código.
