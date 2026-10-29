# CLAUDE.md — senal-xau-trading (bot de señales XAU/USD en M15)

Este archivo es la **memoria del proyecto**. Claude lo lee al empezar cada sesión.
Regla principal: **cada cambio de código que tome una decisión nueva se refleja
aquí en el mismo commit** (sección "Decisiones" y/o "Historial de cambios").
El usuario no debería tener que repetir nada que ya esté escrito aquí.

## Cómo trabajar en este repo

- Idioma: todo en **español** (conversación, comentarios, mensajes de Discord, commits).
- **Respuestas cortas y concretas** (pedido del usuario el 2026-10-22): lo esencial, sin rodeos.
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

- 2026-10-29 — **FVG: hasta 5 señales al día** (`FVG_MAX_POR_DIA = 5`, antes 1). El usuario pidió
  mínimo 5 al día; la FVG no da tantas (con tope 1 salían ~2,4 por semana) y ninguna regla que gane
  en el laboratorio da 5 al día, así que se sube el tope: saldrán todas las que cumplan, sin
  rellenar con señales malas (backtest con 3/día: −0,06 / −0,09 / +0,23 R) — decisión del usuario.

- 2026-10-29 — **Nasdaq del bot apartado**: `NASDAQ_ACTIVO = False` y `NASDAQ_R1_ACTIVO = False`
  (zona de ruido y R1 ya no avisan ni piden datos del QQQ; el código y sus historiales se quedan
  para volver a activarlos). Señales se centra **solo en el oro** (FVG experimental). `!USTEC` (las
  operaciones manuales del usuario) sigue funcionando. Motivo: casi no daban avisos y el usuario
  gana más con su propia regla — decisión del usuario.

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
  TP 2R, 07–20 UTC, máx. 5 al día (antes 1 y 3; ver abajo), una a la vez. Es la variante V4 del laboratorio
  (`BOT_ATLAS/backtest`, ronda 4), que **no pasa con costes** (−0,05/−0,10 R en 2012–17 y
  2018–22; +0,23 R en 2026): se deja correr para observarla en vivo — decisión del usuario.
- 2026-10-07 — **FVG: máximo 1 señal al día** (`FVG_MAX_POR_DIA = 1`; como mucho 5 por
  semana; antes 3 al día). Es un tope, no un mínimo: los días sin condiciones no hay señal.
  Backtest con el tope: ~2,4 señales por semana (señal en ~48 % de los días), −0,12 R en
  2012–17, −0,03 R en 2018–22, +0,04 R en 2026 (con 3/día: −0,06 / −0,09 / +0,23 R) —
  decisión del usuario.
- 2026-10-16 — **Estadísticas siempre disponibles**: botón **📊 Estadísticas** junto al de
  monitorear (mismo informe que `!stats`; funciona aunque el bot no tenga el intent *Message
  Content*) y **respaldo del historial en Discord** como en fusión: el disco de Northflank se
  borra en cada redeploy, así que `historial_senales.csv`, `senales_abiertas.json`,
  `historial_nasdaq.csv`, `historial_nasdaq_r1.csv` y `nasdaq_estado.json` se guardan como
  adjuntos de **un mensaje fijado** ("📦 Respaldo de datos del bot de senales (no borrar)") que
  se edita cuando algo cambia (`respaldo_periodicamente`, cada 5 min) y se recuperan al arrancar
  si el disco viene vacío. Necesita el permiso **Fijar mensajes** — decisión del usuario.
- 2026-10-21 — **Comando `!USTEC`** (también `!nasdaq` y botón 📈 USTEC) con las operaciones
  **manuales** del usuario en el Nasdaq (regla de la caja: 📦 apertura y 🌙 noche): una línea por
  día ("Oct21/26: 4 operaciones -- profit 2 · loss 2 · 50 % · −13,34 € (acumulado 76 %)") y el
  total (operaciones, profit/loss, % de acierto, días positivos/negativos, resultado y media por
  día, y desglose apertura/noche). Los datos están en **`operaciones_ustec.csv`** (una fila por
  operación; un grupo sin desglose lleva `operaciones` > 1). **Claude añade ahí cada operación que
  el usuario manda** (además de anotarla abajo, en "Pendiente"); el bot lee el archivo de `main`
  en GitHub (repo público), así que se actualiza al aceptar el PR **sin redeploy**; si GitHub no
  responde, usa la copia del despliegue — decisión del usuario.
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
  - **Registro de la prueba** (cuenta demo de **700 €** según su historial del 15/10, no 200 €;
    USTEC ≈ 0,89 €/punto por lote; con 0,5 lotes un stop de 0,2 % (~60 pts) son ~27 € ≈ 4 % de la
    cuenta → recomendado ≤ 0,2 lotes y **siempre con stop**):

    | Fecha | Vela confirmación (gráfico) | Lado | Operaciones | Resultado |
    |---|---|---|---|---|
    | 2026-10-12 | 16:30 (apertura), cuerpo grande | Venta | 3 (0,5 + 0,3 + 0,3 lotes; la 1.ª antes de la confirmación) | +58,84 € |
    | 2026-10-13 | 16:30 (apertura): vela verde enorme que cierra muy por encima de la caja → **COMPRA** | — (no la tomó) | 2 ventas en la vela de las 16:15, antes de la confirmación | **−57 € entre las dos** (el usuario dice 0,03 lotes; por el valor del punto de su cuenta, ~0,9 €/punto por lote, encaja mejor con 0,3). **Según el usuario la estrategia sí habría servido** (dirección correcta; con su TP de 30 € y margen de 5 velas para entrar); con la regla escrita (entrada al cierre de las 16:30, stop 0,2 %, salida a la 5.ª vela) habría quedado cerca del stop (~−1 R). Lección del usuario: no entrar antes del cierre de la vela de las 16:30 y confiar en la señal. |
    | 2026-10-14 | 16:30 (apertura): según la captura, vela verde de cuerpo normal (no ≥ 2× la media) que cierra por debajo de la caja → **sin señal, día sin operar** con la regla | — | **Compra 0,5** en 30.437,3 por la vela de las **14:30** (leyó mal la hora); la vela de las 15:30 del gráfico (08:30 NY, hora de datos de EE. UU.) bajó ~270 puntos; cerrada en 30.003,9 a las 19:24 (**−434 puntos, sin stop**) | ❌ **−194,98 €**. Lección: operar solo con la vela de las 16:30 del gráfico y **siempre con stop** (con el de 0,2 % habrían sido ~−27 €). |

    Acumulado 📦 hasta el 14/10: **−193,14 €** (+58,84 − 57 − 194,98); las dos pérdidas, por entrar
    fuera de la regla (antes de la confirmación o con la vela equivocada).

    2026-10-15 (cuenta en la regla; ver "misma regla" en la prueba 🌙): 2 ventas de 0,5 antes de la
    confirmación (cerradas a las 16:35, +18,06 €) y 2 compras de 0,5 tras el cierre de la vela de
    las 16:30 (~29.632 → ~29.717, cerradas a las 18:02 = 5.ª vela, +76,08 €) → **+94,14 €**; con
    eso el acumulado 📦 queda en **−99,00 €**. Fuera de la regla: 2 compras de 0,2 a las
    21:38/21:46 (+1,36 €) y una compra de 0,3 el 13/10 a las 22:14 (+0,37 €).

    2026-10-16: **3 ventas** (lotes de 0,2, ya más pequeños): 29.688,3 → 29.681,0 cerrada a las
    16:38 (+1,30 €) y 29.738,3 / 29.723,1 → ~29.651 cerradas a las **17:56 (5.ª vela)** (+15,55 y
    +12,81 €) → **+29,66 €**; acumulado 📦 **−69,34 €**. (La de las 16:38 se cerró antes del cierre
    de la vela de las 16:30, así que probablemente entró antes de la confirmación.)

    2026-10-19: **5 compras** (0,5 + 0,5 + 0,5 + 0,1 + 0,1 = **1,7 lotes a la vez**): 29.507,1 →
    29.578,0 (+31,61 €), 29.586,9 → 29.661,6 (+33,30 €), 29.588,1 → 29.663,2 (+33,48 €), 29.586,2 →
    29.664,0 (+6,94 €), 29.588,2 → 29.670,5 (+7,34 €), cerradas entre las 17:13 y las 17:18 (antes de
    la 5.ª vela) → **+112,67 €** (~+70–80 pts cada una); acumulado 📦 **+43,33 €**. El balance de su
    cuenta subió ese día de 824,82 € a 1.038,26 € (+213,44 €): los ~+100,77 € que no salen en la
    captura son **operaciones de oro** (según el usuario), fuera de esta prueba.

    2026-10-20: la vela de las **16:15** rompió la caja (15:00–15:15, ~29.300–29.410) a la baja y
    vendió en esa vela (**antes de la confirmación**): 2 ventas de 0,1 en 29.216,9 / 29.231,9. La
    vela de las **16:30** fue verde enorme y cerró ~29.440, **por encima** de la caja → la regla
    decía **COMPRA**. Sin stop, mantuvo las ventas hasta la 01:24 del 21/10 (29.772,1 / 29.771,7,
    **~−550 pts**) → ❌ **−97,49 €** (−49,43 y −48,06). Con el stop de 0,2 % (~58 pts) habrían sido
    ~−10 €; la compra de la regla (cierre de las 16:30 → 5.ª vela, ~29.440 → ~29.560) daba ~+120
    pts. Es el mismo error del 13/10 (entrar antes de la confirmación) y del 14/10 (sin stop).
    Acumulado 📦 **−54,16 €**; las pérdidas por saltarse la regla suman −349,47 €
    (13/10 −57, 14/10 −194,98, 20/10 −97,49).

    2026-10-21: **2 compras de 0,1** en 29.716,6 / 29.722,8 → 29.863,4 / 29.869,1, cerradas a las
    18:45 / 18:50 (~+147 pts, después de la 5.ª vela) → ✅ **+26,12 €** (+13,08 y +13,04);
    acumulado 📦 **−28,04 €**. Ese día también 2 ventas de oro (+11,41 y +30,39 €), fuera de la prueba.

    2026-10-22: compra 0,1 29.391,3 → 29.306,1 cerrada a las 17:13 (❌ −7,61 €, −85 pts) y 2 ventas de
    0,1 en 29.261,4 / 29.255,7 → 29.092,0 / 29.095,0 cerradas a las 18:46 (✅ +15,12 y +14,34 €,
    ~+165 pts) → **+21,85 €**; acumulado 📦 **−6,19 €**. Oro ese día: +45,28 €, fuera de la prueba.

    2026-10-23: 2 compras de 0,1 (~28.982 → ~29.063, cerradas a las 18:11) → ✅ **+14,54 €**.
    2026-10-26 (**primer día tras el cambio de hora de Europa**; esta semana su gráfico = Madrid + 2 h):
    no sabía qué vela tomar, hizo la caja en otra hora y vendió 2 × 0,5 en 29.048,2 / 29.044,4 **sin
    stop**, cerradas a las 19:08 en ~29.327 (**~−280 pts**) → ❌ **−250,87 €** (−123,40 y −127,47). Con
    el stop de 0,2 % (~58 pts) habrían sido ~−52 €. Se le aclaró que el gráfico sigue a Nueva York
    (caja 15:00 / confirmación 16:30 **del gráfico** siempre; en Madrid 13:00 / 14:30 del 26 al 30/10).
    2026-10-27: 2 compras de 0,5 (~29.444 → ~29.532, cerradas a las 17:55) → ✅ **+78,94 €**.
    Acumulado 📦 **−163,58 €**; pérdidas por saltarse la regla o sin stop: −600,34 €.

    Nota (2026-10-14): con la entrada al cierre de las 16:30, un TP pequeño sube el acierto pero
    pierde en 10 años (TP 0,1 % ≈ 30 pts: 66 % de acierto, −0,05 / −0,04 / +0,08 R); lo que gana
    es dejar correr (5.ª vela: +0,05 / +0,08 / +0,10 R; TP 0,4 % = 2:1: +0,02 / +0,06 / +0,22 R).
    Mejor fijar el TP en puntos/% y no en € (depende del lote).
- **Segunda prueba manual del usuario: "🌙 caja de las 22:45"** (desde 2026-10-13, NO está en el bot).
  **2026-10-15 — según el usuario, 📦 y 🌙 son LA MISMA REGLA aplicada en dos momentos**: marcar
  una caja con una vela y entrar a favor de la vela que la rompe con cuerpo. 📦 = caja de las
  15:00 y confirmación a las 16:30 (apertura de Wall Street); 🌙 = caja de las 22:45 (antes del
  cierre) y ruptura durante la noche. Se evalúan como una sola prueba. Por día (la noche cuenta
  el día en que se cerró): 12/10 +58,84 € · 13/10 −57,00 € · 14/10 −167,58 € (−194,98 + 27,40) ·
  15/10 +138,35 € (+94,14 + 44,21) · 16/10 +73,83 € (+29,66 + 44,17) · 19/10 +190,14 € (+112,67 +
  77,47) · 20/10 −79,65 € (+17,84 🌙 − 97,49 📦) · 21/10 −13,34 € (−39,46 🌙 + 26,12 📦) ·
  22/10 +42,88 € (+21,03 🌙 + 21,85 📦) · 23/10 +14,54 € (📦) · 26/10 −218,26 € (+32,61 🌙 − 250,87 📦) ·
  27/10 +138,19 € (+59,25 🌙 + 78,94 📦) · 29/10 +185,22 € (🌙) → **total +306,16 €** en 52 operaciones
  (📦 −163,58 € + 🌙 +469,74 €); su cuenta demo: 700 € → 1.379,57 € el 29/10 (swap acumulado −14,75 €) (cuadra al céntimo con el historial; la misma cuenta lleva
  también **operaciones de oro** que no cuentan en esta prueba; el 20/10: +43,18, +29,61 y
  +0,32 €). Siguiendo la
  regla completa ganó siempre; las dos pérdidas grandes, por entrar antes de la confirmación o
  con la vela equivocada.
  **2026-10-15 — plan del usuario:** hacer **~100 operaciones** con la regla y valorar el
  laboratorio solo con los **últimos 4 años** (2022–2026: el Nasdaq de antes tenía otras empresas
  y otra volatilidad). Datos gratuitos de 2022–2025 no encontrados (solo muestras de 2026 en
  GitHub y NQ 1 min jul–oct 2026 en `Chief-rich/nasdaq100-data`); opciones: que el usuario exporte
  USTEC M15 desde MetaTrader 5 de escritorio (datos de su bróker, con su hora) o que suba el CSV de
  Kaggle "NQ Futures 1min Bar 2022-2025". En el laboratorio la regla funciona en la
  apertura (+0,05 / +0,08 / +0,10 R) y no en el cierre (ninguna versión nocturna pasa).
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
    | 2026-10-14 (caja de las 22:45 del 13) | Al alza (caja ~30.535–30.570) | Compra ~30.585 a la 01:15 → cierre ~30.652 a las 05:15 del 14 (horas de su gráfico) | ✅ **+27,40 €** (su historial: compra 0,5 en 30.588,6 → 30.650,0, cerrada a las 05:26; ~+61 puntos) |
    | 2026-10-15 (caja de las 22:45 del 14) | A la baja (caja ~29.925–29.980) | Venta ~29.875 en la vela de las 00:00 → cierre ~29.805 en la de las 00:30 (horas de su gráfico) | ✅ **+44,21 €** (su historial: venta **0,8** en 29.869,0 → 29.807,3, cerrada a las 01:31; ~+62 puntos); el precio siguió bajando hasta ~29.690 a las 02:30 |

    | 2026-10-16 (caja de las 22:45 del 15) | A la baja | **2 ventas de 0,3** en 29.897,5 / 29.898,0: una cerrada a las 03:27 en 29.762,0 (+36,26 €, ~+135 pts) y la otra a las 14:39 en 29.868,3 (+7,91 €) | ✅ **+44,17 €** |

    | 2026-10-19 (lunes; caja de las 22:45 anterior, tras el fin de semana) | Al alza | **2 compras de 0,2** en 29.333,4 / 29.329,9: cerradas a las 05:04 en 29.524,6 (+34,05 €, ~+191 pts) y a las 06:24 en 29.573,7 (+43,42 €, ~+244 pts) | ✅ **+77,47 €** |

    | 2026-10-20 (martes; caja de las 22:45 del 19) | A la baja | **2 ventas de 0,1** en 29.525,9 / 29.525,8 → 29.424,2 / 29.427,2, cerradas a las 08:58 (~+100 pts cada una) | ✅ **+17,84 €** (el balance subió 47,25 €: los +29,41 € restantes son una **venta de oro** de 0,07 cerrada el 19/10 a las 23:04, fuera de la prueba) |

    | 2026-10-21 (miércoles; caja de las 22:45 del 20) | Al alza | **2 compras de 0,1** en 29.787,9 / 29.788,7 → 29.566,2 / 29.567,9, cerradas a las 12:03 (**~−221 pts**, sin stop de 0,2 %: con él, ~−11 €) | ❌ **−39,46 €** (−19,77 y −19,69): primera noche perdedora |

    | 2026-10-22 (jueves; caja de las 22:45 del 21) | A la baja | **1 venta de 0,1** en 29.730,7 → 29.494,3, cerrada a las 05:53 (~+236 pts) | ✅ **+21,03 €** |

    | 2026-10-26 (lunes; caja de las 22:45 del viernes 23, abierta el fin de semana) | Al alza | **compras de 0,5 y 0,2** en 29.087,1 / 29.084,7 → 29.138,4 / 29.139,4, cerradas a la 01:00 del lunes | ✅ **+32,61 €** (ojo: el swap del fin de semana restó ~−14,5 €) |
    | 2026-10-27 (martes; caja de las 22:45 del 26) | A la baja | **2 ventas de 0,5** en 29.265,6 / 29.257,2 → 29.204,3 / 29.186,2, cerradas a las 08:28 / 08:30 | ✅ **+59,25 €** |

    | 2026-10-29 (jueves; caja de las 22:45 del 28) | A la baja | **6 ventas de 0,5** en 3 tandas (~+30 € cada una, ~68–70 pts): 29.674,9 / 29.676,5 → 29.606,6 cerradas a las 23:38 del 28; 29.575,6 / 29.572,8 → 29.506,7 / 29.503,9 cerradas a la 01:25; 29.519,8 / 29.512,6 → 29.451,8 / 29.443,6 cerradas a las 04:47 / 04:48 | ✅ **+185,22 €** (+30,62, +31,33, +30,90, +30,90, +30,51, +30,96). Ese día también una venta de oro de 0,5 (+96,50 €), fuera de la prueba |

    Acumulado 🌙 hasta el 29/10: **+469,74 €** (9 de 10 noches ganadoras).

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

Respaldo: `_restaurar_respaldo()` en `on_ready` (antes de los bucles) y `_subir_respaldo()` cada
5 min si cambió la firma (tamaño + fecha) de algún archivo de estado.

Archivos de estado (en el directorio de trabajo, o donde digan las variables; todos van al
respaldo de Discord):
- `historial_senales.csv` — una fila por señal con `resultado` PENDIENTE/WIN/LOSS/TIMEOUT.
- `senales_abiertas.json` — señales que aún no tocaron SL/TP (sobrevive a reinicios si
  el disco es persistente).
- `historial_nasdaq.csv` — una fila por operación del Nasdaq cerrada (entrada, salida, % y motivo).
- `nasdaq_estado.json` — avisos del Nasdaq ya mandados hoy (zona de ruido y R1).
- `historial_nasdaq_r1.csv` — una fila por operación R1 cerrada (TP/SL/CIERRE y resultado en R).
- `operaciones_ustec.csv` (en el repo, no en el disco) — operaciones manuales del usuario para `!USTEC`;
  lo mantiene Claude y el bot lo lee de GitHub (`URL_OPERACIONES_USTEC`).

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
| `DISCORD_CHANNEL_ID_RESPALDO` | Canal del mensaje de respaldo (por defecto, el de señales) | No |
| `PORT` | Puerto del health check (8080) | No |

El bot necesita el intent **Message Content** (para `!stats` y `!USTEC`; los botones 📊 y 📈 funcionan sin él) y el
permiso **Fijar mensajes** (respaldo).

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
- 2026-10-16 — Botón 📊 Estadísticas y respaldo de los historiales en un mensaje fijado de Discord.
- 2026-10-21 — Comando `!USTEC` y botón 📈 con las operaciones manuales del Nasdaq (`operaciones_ustec.csv`).
- 2026-10-29 — Nasdaq del bot (zona de ruido y R1) desactivado; Señales solo con el oro.
- 2026-10-29 — FVG: tope de 5 señales al día (antes 1).
- 2026-10-11 — Laboratorio del patrón del usuario (vela de las 15:00 / confirmación a las
  16:30): queda como prueba manual del usuario (ver "Pendiente"); sin cambios en el código.
