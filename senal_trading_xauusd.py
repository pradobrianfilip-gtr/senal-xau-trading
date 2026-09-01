"""
Bot de SENALES TECNICAS (ICT: BOS / CHoCH / EQH / FVG) para XAU/USD -> Discord
================================================================================
Proyecto separado del monitor de noticias. Usa velas REALES (no sinteticas)
de Twelve Data, un proveedor de datos de mercado gratuito (no es un broker,
asi que no tiene restricciones por pais como si las tienen los brokers
regulados -- funciona igual desde cualquier lugar, incluida Espana).

Conceptos que usa (explicados rapido):
  - BOS (Break of Structure): el precio rompe un maximo/minimo importante
    anterior EN LA MISMA direccion de la tendencia -- confirma que la
    tendencia sigue.
  - CHoCH (Change of Character): el precio rompe estructura en direccion
    CONTRARIA a la tendencia que traia -- primera senal de posible cambio
    de direccion.
  - EQH / EQL (Equal Highs / Equal Lows): dos o mas maximos (o minimos)
    casi al mismo nivel -- se interpretan como zonas de liquidez, un
    objetivo comun para el Take Profit.
  - FVG (Fair Value Gap): un hueco de 3 velas donde el precio se movio tan
    rapido que dejo una zona sin operar -- el precio tiende a volver a
    rellenarla. Se reporta como contexto extra en la senal.

Patrones chartistas que tambien reconoce:
  - Doble Techo / Doble Suelo -- con Entry, Stop Loss y Take Profit
    (regla de la "altura del patron" proyectada desde el neckline)
  - Hombro-Cabeza-Hombro (y su version invertida) -- mismo tipo de calculo
  - Triangulos (ascendente, descendente, simetrico) y Cunas (alcista,
    bajista) -- estos se avisan solo como CONTEXTO/SESGO, sin Entry/SL/TP,
    porque necesitan que la persona confirme la ruptura por su cuenta

Boton interactivo en Discord:
  Ademas de las senales automaticas (cada 5 minutos revisa, y solo avisa
  cuando hay algo confirmado), el bot deja un mensaje fijo en el canal con
  un boton "Monitorear compra/venta ahora". Lo puedes presionar en
  cualquier momento y el bot te responde al instante con una foto del
  estado actual (precio, estructura, RSI, tendencia del dia, zonas de
  liquidez y FVG) -- sin esperar a que cierre la siguiente vela.

  IMPORTANTE: para que el boton funcione, este bot ya NO usa un webhook de
  Discord (los webhooks no pueden recibir clics) -- ahora es un bot de
  Discord de verdad, con su propio token. Ver la configuracion mas abajo.

Como conseguir el token del bot (gratis):
  1. Ve a https://discord.com/developers/applications -> "New Application"
  2. Dale un nombre (ej. "Senal XAU") -> "Create"
  3. En el menu de la izquierda, ve a "Bot" -> "Reset Token" -> copialo
     (esto es tu DISCORD_BOT_TOKEN)
  4. En "OAuth2" -> "URL Generator": marca el scope "bot", y en permisos
     marca "Send Messages" y "Embed Links". Copia la URL que se genera
     abajo, abrela en el navegador, y elige tu servidor para invitarlo.
  5. En Discord, activa el "Modo desarrollador" (Ajustes -> Avanzado), luego
     click derecho sobre el canal donde quieres las senales -> "Copiar ID
     del canal" -- eso es tu DISCORD_CHANNEL_ID

De donde salen los datos:
  - Twelve Data (proveedor de datos de mercado, no un broker) via su API
    REST. Da velas reales (Open/High/Low/Close) del simbolo XAU/USD, no
    precios sueltos -- mucho mas preciso que aproximar velas a partir de
    un precio muestreado cada 2 minutos. Plan gratis: 800 consultas al dia
    (el bot usa muchas menos que eso).

Filtro de tendencia diaria:
  Antes de avisar una senal en las velas de 15 minutos, el bot calcula el
  sesgo del dia usando las MISMAS velas de 15 min (no una consulta aparte),
  buscando la primera vela despues de la medianoche de MADRID y comparando
  su apertura contra el precio actual -- asi el "dia" siempre es el dia de
  Madrid, sin depender de en que zona horaria trabaje la API por dentro.
  Si el dia esta alcista, solo avisa senales BUY; si esta bajista, solo
  SELL. Las senales que van en contra del dia se calculan igual por dentro,
  pero no se mandan a Discord.

Filtro de RSI (confirmacion extra, para evitar entradas debiles):
  - BOS/CHoCH: BUY solo se manda si el RSI esta entre 50 y 70 (impulso
    alcista sano, sin estar ya sobrecomprado); SELL solo si esta entre 30
    y 50 (lo mismo al reves).
  - Doble Techo / Hombro-Cabeza-Hombro (patrones de reversion bajista):
    solo se mandan si el RSI estuvo en zona de sobrecompra (>=65) en las
    10 velas antes de confirmarse.
  - Doble Suelo / HCH Invertido (reversion alcista): solo si el RSI estuvo
    en sobreventa (<=35) antes de confirmarse.

Fuente de respaldo:
  Si Twelve Data falla (por ejemplo, se agotan las 800 consultas gratis del
  dia), el bot intenta automaticamente con Alpha Vantage (otra fuente
  gratis, con su propia cuota aparte) antes de rendirse. Avisa a Discord
  una sola vez cuando cambia de fuente, y otra vez cuando Twelve Data
  vuelve a responder -- para no spamear el canal.

Como conseguir la API key de Alpha Vantage (opcional, gratis, solo pide
correo): https://www.alphavantage.co/support/#api-key

Como conseguir la API key (gratis, sin tarjeta, funciona desde Espana):
  1. Ve a https://twelvedata.com y crea una cuenta gratis (solo pide correo)
  2. Tu API key aparece en el panel principal (dashboard) apenas te registras
  3. Pon esa key en la variable de entorno TWELVE_DATA_API_KEY

Mejoras aplicadas (version trader-profesional):
  - RSI con suavizado de Wilder (el metodo real, coincide con TradingView/
    MT4/5) en vez del promedio simple de antes.
  - Stop Loss basado en ATR (volatilidad real de las ultimas 14 velas) en
    vez de un margen fijo -- se adapta a dias tranquilos o movidos.
  - Filtro de tendencia diaria recalculado con velas DIARIAS reales (EMA20)
    en vez de aproximarlo con la apertura/cierre de un solo dia en 15min.
    Se cachea una vez al dia para no gastar consultas de mas.
  - Limite diario de senales de estructura (MAX_SENALES_ESTRUCTURA_POR_DIA)
    para evitar sobre-senalizacion en dias muy choppy.
  - Ventanas de "blackout" configurables para noticias de alto impacto
    (VENTANAS_BLACKOUT_NOTICIAS) -- vacias por defecto, se editan a mano.
  - Historial de senales en CSV local (historial_senales.csv) para poder
    revisar despues el desempeno real del sistema.
  - Filtro de solapamiento de sesiones: las senales de entrada (estructura
    y patrones) solo se mandan durante los 4 solapamientos de mayor
    liquidez (Sidney-Tokio, Tokio-Londres, Londres-Nueva York, Nueva
    York-Sidney). Se puede desactivar con REQUERIR_VENTANA_ALTA_LIQUIDEZ.
  - Confirmacion de liquidez/volumen: usa el volumen real si el proveedor
    lo trae, o la expansion del rango de la vela (proxy) si no -- para
    solo avisar cuando hay participacion real detras del movimiento.

IMPORTANTE -- esto no es asesoria financiera:
  BOS, CHoCH, EQH y FVG son patrones de analisis tecnico (price action /
  "smart money concepts"). Son herramientas de lectura del grafico, no
  garantias. Esta senal es automatica, basada en reglas fijas, y puede
  fallar como cualquier metodo tecnico. Este bot NO ejecuta ninguna orden
  -- solo avisa. La decision de entrar o no es tuya, revisando el grafico.

Requisitos:
    pip install requests discord.py

Configuracion (variables de entorno):
    DISCORD_BOT_TOKEN     -> token de tu bot de Discord (ver arriba)
    DISCORD_CHANNEL_ID    -> ID del canal donde quieres las senales (ver arriba)
    TWELVE_DATA_API_KEY   -> API key gratis de twelvedata.com (ver arriba)
    ALPHA_VANTAGE_API_KEY -> opcional, fuente de respaldo (ver arriba)
"""

import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import discord
from discord.ext import tasks
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "0") or "0")
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "PON_AQUI_TU_API_KEY")

# Fuente de respaldo, opcional: si Twelve Data falla (ej. se agotan las 800
# consultas del dia), el bot intenta con Alpha Vantage antes de rendirse.
# Gratis en https://www.alphavantage.co/support/#api-key (solo pide correo)
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")

TWELVE_DATA_URL = "https://api.twelvedata.com/time_series"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
SIMBOLO = "XAU/USD"

MADRID_TZ = ZoneInfo("Europe/Madrid")

# Cada cuantos minutos revisamos la estructura
INTERVALO_REVISION_MINUTOS = 5

# Granularidad de las velas que pedimos (15min = velas de 15 minutos)
GRANULARIDAD = "15min"
NUM_VELAS = 200  # cuantas velas pedimos cada vez (suficiente historial)

# Estado en memoria: si estamos usando la fuente de respaldo ahora mismo,
# para avisar solo una vez cuando cambia (no cada 5 minutos)
_usando_respaldo = False

# Cuantas velas a cada lado necesita un maximo/minimo para considerarse un
# "swing" confirmado (mientras mas alto, menos swings pero mas confiables)
FUERZA_SWING = 3

# Tolerancia para considerar dos maximos (o minimos) como "iguales" (EQH/EQL)
TOLERANCIA_EQH_PCT = 0.05  # 0.05% de diferencia

# Relacion riesgo:beneficio de respaldo, solo si no se encuentra un nivel
# de liquidez (EQH/EQL) claro para usar como Take Profit
RATIO_RIESGO_BENEFICIO_RESPALDO = 2

# Estado en memoria: tendencia de estructura actual ("alcista"/"bajista"/None)
_tendencia_estructura = None

# Guarda el timestamp de la ultima vela ya procesada, para no repetir la
# misma senal mientras se espera a que cierre la siguiente vela de 15 min
_ultima_vela_procesada = None

# Guarda un identificador de cada patron chartista ya avisado, para no
# repetir el mismo patron una y otra vez mientras sigue vigente
_patrones_ya_avisados = set()

# --- ATR (Average True Range): mide la volatilidad real de las ultimas
# velas. Se usa para poner el Stop Loss a una distancia que respira con el
# mercado (mas lejos si el oro esta moviendose mucho, mas cerca si esta
# tranquilo) en vez de un porcentaje fijo que no se adapta al regimen. ---
PERIODO_ATR = 14
MULTIPLICADOR_ATR_SL = 1.2  # cuantos ATR de colchon se dejan mas alla del swing roto

# --- Control de sobre-senalizacion: limite de senales de estructura (BOS/
# CHoCH) que se mandan por dia, para evitar spam en dias muy choppy. Los
# patrones chartistas y los avisos de contexto no cuentan para este limite. ---
MAX_SENALES_ESTRUCTURA_POR_DIA = 6
_contador_senales_hoy = 0
_fecha_contador_senales = None  # se resetea solo cuando cambia el dia (hora Madrid)

# --- Ventanas de "apagon" por noticias de alto impacto: lista de tuplas
# (dia_semana 0=lunes..6=domingo, hora_inicio, hora_fin) en HORA DE MADRID.
# Mientras el momento actual caiga dentro de una ventana, el bot NO manda
# senales nuevas (evita entrar justo antes/despues de un spike por NFP,
# FOMC, IPC, etc). Esta lista es manual -- edita las fechas/horas segun el
# calendario economico de la semana si quieres usarla; vacia por defecto.
# Ejemplo para bloquear el primer viernes de mes entre 14:15 y 14:45 (NFP
# suele publicarse a las 14:30 hora Madrid en horario de verano de EEUU):
#   VENTANAS_BLACKOUT_NOTICIAS = [(4, "14:15", "14:45")]
VENTANAS_BLACKOUT_NOTICIAS = []


def _en_ventana_blackout_noticias():
    """Revisa si el momento actual (hora Madrid) cae dentro de alguna
    ventana configurada en VENTANAS_BLACKOUT_NOTICIAS."""
    if not VENTANAS_BLACKOUT_NOTICIAS:
        return False
    ahora = datetime.now(MADRID_TZ)
    for dia_semana, hora_inicio, hora_fin in VENTANAS_BLACKOUT_NOTICIAS:
        if ahora.weekday() != dia_semana:
            continue
        inicio = datetime.strptime(hora_inicio, "%H:%M").time()
        fin = datetime.strptime(hora_fin, "%H:%M").time()
        if inicio <= ahora.time() <= fin:
            return True
    return False


def _resetear_contador_si_cambio_el_dia():
    """El contador de senales de estructura se reinicia solo una vez al
    dia, sincronizado con la medianoche de Madrid."""
    global _contador_senales_hoy, _fecha_contador_senales
    hoy = datetime.now(MADRID_TZ).date()
    if _fecha_contador_senales != hoy:
        _fecha_contador_senales = hoy
        _contador_senales_hoy = 0


# --- Solapamientos de sesiones (Sidney / Tokio / Londres / Nueva York) ---
# Son los momentos de MAYOR liquidez real del dia -- cuando dos mercados
# estan abiertos a la vez, hay mas participantes, mas volumen y los
# rompimientos de estructura (BOS/CHoCH) tienen mas probabilidad de ser
# reales en vez de ruido. Horas en UTC (para no depender de si Madrid esta
# en horario de verano o invierno):
#   - Sidney-Tokio:        00:00 - 06:00 UTC
#   - Tokio-Londres:       07:00 - 09:00 UTC
#   - Londres-Nueva York:  12:00 - 16:00 UTC  (el mas liquido de los 4,
#     donde suele moverse mas fuerte el oro)
#   - Nueva York-Sidney:   21:00 - 22:00 UTC  (relevo entre cierre de NY y
#     apertura de Sidney, mas corto que los otros tres)
# NOTA: EEUU y Europa cambian de horario de verano/invierno en fechas
# distintas, asi que estas franjas se pueden correr +-1 hora un par de
# semanas al año. Ajusta los numeros si lo notas desalineado.
VENTANAS_ALTA_LIQUIDEZ_UTC = [
    ("Sidney-Tokio", 0, 6),
    ("Tokio-Londres", 7, 9),
    ("Londres-Nueva York", 12, 16),
    ("Nueva York-Sidney", 21, 22),
]

# Si esta en True, el bot SOLO manda senales de entrada (estructura y
# patrones chartistas) durante alguna de las 4 ventanas de arriba. Si esta
# en False, manda senales a cualquier hora del dia (fuera de fin de semana)
# igual que antes, sin este filtro.
REQUERIR_VENTANA_ALTA_LIQUIDEZ = True


def _sesion_alta_liquidez_actual():
    """Devuelve el nombre del solapamiento de sesiones activo ahora mismo
    (ej. 'Londres-Nueva York'), o None si el momento actual no cae en
    ninguna de las 4 ventanas configuradas."""
    hora_utc = datetime.now(timezone.utc).hour
    for nombre, inicio, fin in VENTANAS_ALTA_LIQUIDEZ_UTC:
        if inicio <= hora_utc < fin:
            return nombre
    return None


# Multiplicador sobre el promedio/ATR que debe superar la vela actual para
# considerarse que hay "empuje real" (liquidez/volumen) detras del movimiento
MULTIPLICADOR_LIQUIDEZ_VOLUMEN = 1.2


def _confirma_liquidez_y_volumen(velas, atr_actual):
    """Confirma que la vela que disparo la senal tiene participacion real
    detras, no solo ruido. Si Twelve Data trae volumen real para el simbolo
    lo usa (comparado contra el promedio de las ultimas 20 velas). Si no hay
    volumen disponible -- lo habitual en XAU/USD via feeds de forex, que no
    tienen un volumen centralizado como una bolsa -- usa como proxy la
    EXPANSION del rango de la vela (High-Low) frente a su propio ATR: una
    vela con rango bien por encima de lo normal es la huella tipica de que
    entro liquidez de verdad (una zona equal highs/lows barrida con fuerza,
    por ejemplo), no un simple parpadeo de precio.
    Devuelve (True/False, texto explicando que se uso)."""
    ultima = velas[-1]
    volumenes_previos = [v["v"] for v in velas[-21:-1] if v.get("v")]

    if ultima.get("v") and volumenes_previos:
        promedio_vol = sum(volumenes_previos) / len(volumenes_previos)
        if promedio_vol > 0:
            confirma = ultima["v"] >= promedio_vol * MULTIPLICADOR_LIQUIDEZ_VOLUMEN
            return confirma, f"Volumen real: {round(ultima['v'], 2)} vs promedio {round(promedio_vol, 2)}"

    # Fallback: expansion del rango de la vela vs su ATR (proxy de liquidez)
    rango_actual = ultima["h"] - ultima["l"]
    if atr_actual:
        confirma = rango_actual >= atr_actual * MULTIPLICADOR_LIQUIDEZ_VOLUMEN
        return confirma, (f"Sin volumen real disponible del proveedor -- usando expansion de rango "
                           f"como proxy: {round(rango_actual, 2)} vs ATR {round(atr_actual, 2)}")

    # Si ni siquiera hay ATR todavia (arranque del bot), no bloqueamos la senal
    return True, "Sin datos suficientes de volumen/ATR todavia -- filtro de liquidez omitido esta vez"


# --- Historial de senales: cada senal de estructura (BOS/CHoCH) que se
# manda queda registrada en un CSV local, para poder revisar despues el
# desempeno real del sistema (cuantas senales, de que tipo, a que precio) --
# esto es lo primero que revisa cualquier trader sistematico antes de
# confiar en un algoritmo. No calcula ganancia/perdida por si solo (para
# eso habria que cruzarlo con precios futuros), pero deja la base lista. ---
ARCHIVO_HISTORIAL = os.environ.get("ARCHIVO_HISTORIAL", "historial_senales.csv")


def _registrar_senal_historial(tipo_evento, direccion, entry, stop_loss, take_profit, rsi, extra=""):
    """Anade una linea al CSV de historial. Si el archivo no existe todavia,
    escribe la cabecera primero. Cualquier error aqui se ignora (no debe
    tumbar el envio de la senal a Discord por un problema de disco)."""
    try:
        existe = os.path.isfile(ARCHIVO_HISTORIAL)
        with open(ARCHIVO_HISTORIAL, "a", encoding="utf-8") as f:
            if not existe:
                f.write("hora_madrid,tipo_evento,direccion,entry,stop_loss,take_profit,rsi,extra\n")
            f.write(f"{hora_madrid()},{tipo_evento},{direccion},{entry},{stop_loss},{take_profit},{rsi},{extra}\n")
    except Exception as e:
        print(f"No se pudo escribir en el historial de senales: {e}")


# --- Cliente de Discord (bot de verdad, no un webhook) ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
_canal = None  # se rellena cuando el bot termina de conectarse (on_ready)


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def hora_madrid():
    return datetime.now(MADRID_TZ).strftime("%d/%m/%Y %H:%M:%S")


def en_pausa_fin_de_semana():
    """XAU/USD (como el resto del mercado) cierra el viernes en la noche y
    no vuelve a abrir hasta el domingo en la noche. En ese lapso no tiene
    sentido gastar consultas de las APIs -- no habria ningun dato nuevo."""
    ahora = datetime.now(MADRID_TZ)
    dia = ahora.weekday()  # lunes=0 ... domingo=6
    hora = ahora.hour
    if dia == 4 and hora >= 22:   # viernes desde las 22:00
        return True
    if dia == 5:                  # sabado, todo el dia
        return True
    if dia == 6 and hora < 12:    # domingo, hasta las 12:00 del mediodia
        return True
    return False


def enviar_discord(titulo, descripcion, color=0xF5A623):
    """Manda un embed al canal configurado, usando el bot (no un webhook).
    Le pega el boton de monitorear a CADA mensaje (no solo al inicial), asi
    la persona siempre tiene el boton a mano en la ultima alerta, sin tener
    que desplazarse hasta el mensaje de arranque.

    Se puede llamar tanto desde codigo sincrono (el chequeo automatico)
    como desde el propio bot -- run_coroutine_threadsafe se encarga de
    programarlo en el hilo correcto sin bloquear nada."""
    if _canal is None:
        print(f"[CANAL NO LISTO TODAVIA] {titulo}: {descripcion}")
        return
    embed = discord.Embed(title=titulo, description=descripcion, color=color)
    embed.set_footer(text=f"Hora Madrid: {hora_madrid()}")
    try:
        asyncio.run_coroutine_threadsafe(_canal.send(embed=embed, view=VistaMonitor()), client.loop)
    except Exception as e:
        print(f"Error enviando a Discord: {e}")


# ---------------------------------------------------------------------------
# DATOS: velas reales, con Twelve Data como fuente principal y Alpha Vantage
# como respaldo automatico si la principal falla
# ---------------------------------------------------------------------------

def _parsear_timestamp_utc(t):
    """Convierte el texto de fecha/hora que manda la API (en UTC) a un
    datetime consciente de zona horaria, para poder pasarlo a hora de Madrid."""
    formatos = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d")
    for fmt in formatos:
        try:
            return datetime.strptime(t, fmt).replace(tzinfo=ZoneInfo("UTC"))
        except ValueError:
            continue
    raise ValueError(f"No se pudo interpretar la fecha: {t}")


def _obtener_velas_twelvedata():
    """Pide velas reales (OHLC) de XAU/USD a Twelve Data, en UTC (para poder
    convertir nosotros mismos a hora de Madrid despues). Devuelve la lista
    en orden CRONOLOGICO (la mas vieja primero, la mas reciente al final)."""
    params = {
        "symbol": SIMBOLO,
        "interval": GRANULARIDAD,
        "outputsize": NUM_VELAS,
        "timezone": "UTC",
        "apikey": TWELVE_DATA_API_KEY,
    }
    r = requests.get(TWELVE_DATA_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    if data.get("status") == "error":
        raise RuntimeError(f"Twelve Data error: {data.get('message')}")

    velas = []
    for v in data.get("values", []):
        volumen_bruto = v.get("volume")
        velas.append({
            "t": v["datetime"],
            "o": float(v["open"]),
            "h": float(v["high"]),
            "l": float(v["low"]),
            "c": float(v["close"]),
            "v": float(volumen_bruto) if volumen_bruto not in (None, "", "0") else None,
        })
    velas.reverse()  # Twelve Data manda lo mas reciente primero, lo invertimos
    return velas


def _obtener_velas_alphavantage():
    """Respaldo si Twelve Data falla (ej. se agotaron las 800 consultas del
    dia). Usa Alpha Vantage, otra fuente gratis con su propia cuota aparte."""
    if not ALPHA_VANTAGE_API_KEY:
        return []

    params = {
        "function": "FX_INTRADAY",
        "from_symbol": "XAU",
        "to_symbol": "USD",
        "interval": GRANULARIDAD,
        "outputsize": "compact",
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    r = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    clave_serie = f"Time Series FX ({GRANULARIDAD})"
    serie = data.get(clave_serie, {})
    if not serie:
        raise RuntimeError(f"Alpha Vantage sin datos: {data.get('Note') or data.get('Error Message') or data}")

    velas = []
    for t, v in serie.items():
        # Alpha Vantage manda la hora en UTC tal cual, sin sufijo
        velas.append({
            "t": t,
            "o": float(v["1. open"]),
            "h": float(v["2. high"]),
            "l": float(v["3. low"]),
            "c": float(v["4. close"]),
            "v": None,
        })
    velas.sort(key=lambda x: x["t"])  # orden cronologico
    return velas


def _obtener_velas():
    """Intenta Twelve Data primero; si falla, intenta Alpha Vantage. Avisa a
    Discord (una sola vez, no cada 5 minutos) cuando cambia de fuente."""
    global _usando_respaldo

    try:
        velas = _obtener_velas_twelvedata()
        if _usando_respaldo:
            _usando_respaldo = False
            enviar_discord(
                "Volvimos a la fuente principal (Twelve Data)",
                "Twelve Data respondio de nuevo con normalidad. El bot deja "
                "de usar la fuente de respaldo.",
                color=0x639922
            )
        return velas

    except Exception as e:
        print(f"Twelve Data fallo ({e}), probando la fuente de respaldo...")
        try:
            velas = _obtener_velas_alphavantage()
            if velas and not _usando_respaldo:
                _usando_respaldo = True
                enviar_discord(
                    "Usando fuente de respaldo (Alpha Vantage)",
                    f"Twelve Data no respondio ({e}). El bot sigue funcionando "
                    f"con Alpha Vantage mientras tanto.",
                    color=0xEF9F27
                )
            return velas
        except Exception as e2:
            print(f"La fuente de respaldo tambien fallo: {e2}")
            return []


def _obtener_velas_diarias():
    """Pide velas DIARIAS reales de XAU/USD a Twelve Data (una consulta
    aparte, pero solo se hace una vez por dia gracias al cache de abajo --
    el plan gratis de 800 consultas/dia sobra de sobra). Se usan para medir
    la tendencia de fondo con una referencia de verdad, en vez de aproximarla
    con las velas de 15 minutos."""
    params = {
        "symbol": SIMBOLO,
        "interval": "1day",
        "outputsize": 30,
        "timezone": "UTC",
        "apikey": TWELVE_DATA_API_KEY,
    }
    r = requests.get(TWELVE_DATA_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("status") == "error":
        raise RuntimeError(f"Twelve Data error (velas diarias): {data.get('message')}")

    velas = []
    for v in data.get("values", []):
        velas.append({"t": v["datetime"], "c": float(v["close"])})
    velas.reverse()  # cronologico: la mas vieja primero
    return velas


def _ema(valores, periodo):
    """EMA (media movil exponencial) simple, sin dependencias externas."""
    if len(valores) < periodo:
        return None
    k = 2 / (periodo + 1)
    ema_actual = sum(valores[:periodo]) / periodo
    for v in valores[periodo:]:
        ema_actual = v * k + ema_actual * (1 - k)
    return ema_actual


# Cache: solo se pide la tendencia diaria (via velas diarias) una vez por
# dia de Madrid, no en cada revision de 5 minutos -- evita gastar consultas
# de la API sin necesidad, ya que la tendencia de fondo no cambia cada rato.
_cache_tendencia_diaria = {"fecha": None, "tendencia": None}


def _obtener_tendencia_diaria(velas_intradia=None):
    """Calcula el sesgo de fondo comparando el precio actual contra la
    EMA de 20 periodos de las velas DIARIAS -- una referencia de tendencia
    real (la que usaria cualquier trader al mirar el grafico diario), en
    vez de aproximarla con la apertura/cierre de un solo dia en velas de
    15 minutos. Devuelve 'alcista', 'bajista' o None si no hay datos
    suficientes. Se recalcula como mucho una vez por dia (cache)."""
    global _cache_tendencia_diaria
    hoy = datetime.now(MADRID_TZ).date()

    if _cache_tendencia_diaria["fecha"] == hoy:
        return _cache_tendencia_diaria["tendencia"]

    try:
        velas_diarias = _obtener_velas_diarias()
        cierres = [v["c"] for v in velas_diarias]
        ema20 = _ema(cierres, 20)
        if ema20 is None or not cierres:
            tendencia = None
        else:
            precio_referencia = cierres[-1]
            if precio_referencia > ema20:
                tendencia = "alcista"
            elif precio_referencia < ema20:
                tendencia = "bajista"
            else:
                tendencia = None
    except Exception as e:
        print(f"No se pudo calcular la tendencia diaria con velas diarias ({e}).")
        tendencia = _cache_tendencia_diaria["tendencia"]  # mantener la ultima conocida antes que fallar en seco

    _cache_tendencia_diaria = {"fecha": hoy, "tendencia": tendencia}
    return tendencia


# ---------------------------------------------------------------------------
# RSI (Relative Strength Index) -- usado como confirmacion extra antes de
# mandar una senal, para filtrar entradas debiles
# ---------------------------------------------------------------------------

PERIODO_RSI = 14
RSI_ZONA_SOBRECOMPRA = 70
RSI_ZONA_SOBREVENTA = 30


def _calcular_serie_rsi(precios, periodo=PERIODO_RSI):
    """Calcula el RSI para cada vela usando el suavizado de Wilder (el
    metodo original y el que usan TradingView, MT4/5 y la mayoria de
    plataformas) -- asi el RSI que ve el bot coincide con el que ve la
    persona en su plataforma de graficos, en vez de dar numeros distintos
    por usar un promedio simple. Devuelve una lista del mismo largo que
    'precios', con None en las posiciones donde todavia no hay suficiente
    historial para calcularlo."""
    rsis = [None] * len(precios)
    if len(precios) < periodo + 1:
        return rsis

    cambios = [precios[i] - precios[i - 1] for i in range(1, len(precios))]
    ganancias = [max(c, 0) for c in cambios]
    perdidas = [max(-c, 0) for c in cambios]

    # Primer promedio: simple, sobre los primeros 'periodo' cambios (punto
    # de partida estandar del metodo de Wilder)
    promedio_ganancia = sum(ganancias[:periodo]) / periodo
    promedio_perdida = sum(perdidas[:periodo]) / periodo

    def _rsi_desde_promedios(pg, pp):
        if pp == 0:
            return 100.0
        rs = pg / pp
        return round(100 - (100 / (1 + rs)), 2)

    # El indice 'periodo' en 'cambios' corresponde al indice 'periodo + 1'
    # en 'precios' (cambios[0] es precios[1]-precios[0])
    rsis[periodo] = _rsi_desde_promedios(promedio_ganancia, promedio_perdida)

    # Resto de la serie: suavizado de Wilder (cada nuevo valor pesa 1/periodo
    # y arrastra el promedio anterior, en vez de recalcular sobre una
    # ventana fija) -- esto es lo que hace que sea "Wilder" y no una media movil comun
    for i in range(periodo + 1, len(cambios) + 1):
        g = ganancias[i - 1]
        p = perdidas[i - 1]
        promedio_ganancia = (promedio_ganancia * (periodo - 1) + g) / periodo
        promedio_perdida = (promedio_perdida * (periodo - 1) + p) / periodo
        rsis[i] = _rsi_desde_promedios(promedio_ganancia, promedio_perdida)

    return rsis


# ---------------------------------------------------------------------------
# ATR (Average True Range) -- volatilidad real, usada para el Stop Loss
# ---------------------------------------------------------------------------

def _calcular_serie_atr(velas, periodo=PERIODO_ATR):
    """Calcula el ATR (suavizado de Wilder, igual que el RSI de arriba) a
    partir del 'True Range' de cada vela: la mayor distancia entre el
    rango de la vela actual (high-low) y los gaps contra el cierre
    anterior. Devuelve una lista del mismo largo que 'velas', con None
    donde todavia no hay suficiente historial."""
    n = len(velas)
    atrs = [None] * n
    if n < periodo + 1:
        return atrs

    true_ranges = []
    for i in range(1, n):
        alto, bajo, cierre_prev = velas[i]["h"], velas[i]["l"], velas[i - 1]["c"]
        tr = max(alto - bajo, abs(alto - cierre_prev), abs(bajo - cierre_prev))
        true_ranges.append(tr)

    atr_actual = sum(true_ranges[:periodo]) / periodo
    atrs[periodo] = round(atr_actual, 4)

    for i in range(periodo + 1, len(true_ranges) + 1):
        atr_actual = (atr_actual * (periodo - 1) + true_ranges[i - 1]) / periodo
        atrs[i] = round(atr_actual, 4)

    return atrs


# ---------------------------------------------------------------------------
# DETECCION DE ESTRUCTURA: swings, BOS, CHoCH
# ---------------------------------------------------------------------------

def _detectar_swings(velas, fuerza=FUERZA_SWING):
    """Un swing high es una vela cuyo maximo es mas alto que las 'fuerza'
    velas anteriores Y las 'fuerza' velas siguientes (lo mismo para swing
    low, con minimos). Devuelve lista de (indice, 'high'/'low', precio)."""
    swings = []
    n = len(velas)
    for i in range(fuerza, n - fuerza):
        es_swing_high = all(velas[i]["h"] > velas[i - k]["h"] for k in range(1, fuerza + 1)) and \
                        all(velas[i]["h"] > velas[i + k]["h"] for k in range(1, fuerza + 1))
        es_swing_low = all(velas[i]["l"] < velas[i - k]["l"] for k in range(1, fuerza + 1)) and \
                       all(velas[i]["l"] < velas[i + k]["l"] for k in range(1, fuerza + 1))
        if es_swing_high:
            swings.append((i, "high", velas[i]["h"]))
        if es_swing_low:
            swings.append((i, "low", velas[i]["l"]))
    return swings


def _detectar_evento_estructura(velas, swings):
    """Compara el cierre de la ULTIMA vela contra el swing high y el swing
    low confirmados mas recientes, para detectar BOS o CHoCH.

    Devuelve None (sin evento) o un dict con el tipo de evento, la
    direccion, y el nivel de estructura que se rompio (util para el Stop Loss).
    """
    global _tendencia_estructura

    if not swings:
        return None

    ultimo_swing_high = next((s for s in reversed(swings) if s[1] == "high"), None)
    ultimo_swing_low = next((s for s in reversed(swings) if s[1] == "low"), None)

    ultima_vela = velas[-1]
    cierre = ultima_vela["c"]

    evento = None

    if ultimo_swing_high and cierre > ultimo_swing_high[2]:
        tipo = "CHoCH" if _tendencia_estructura != "alcista" else "BOS"
        evento = {
            "tipo": tipo,
            "direccion": "alcista",
            "nivel_roto": ultimo_swing_high[2],
            "swing_opuesto": ultimo_swing_low[2] if ultimo_swing_low else None,
        }
        _tendencia_estructura = "alcista"

    elif ultimo_swing_low and cierre < ultimo_swing_low[2]:
        tipo = "CHoCH" if _tendencia_estructura != "bajista" else "BOS"
        evento = {
            "tipo": tipo,
            "direccion": "bajista",
            "nivel_roto": ultimo_swing_low[2],
            "swing_opuesto": ultimo_swing_high[2] if ultimo_swing_high else None,
        }
        _tendencia_estructura = "bajista"

    return evento


# ---------------------------------------------------------------------------
# PATRONES CHARTISTAS: Doble Techo/Suelo, Hombro-Cabeza-Hombro,
# Triangulos y Cunas -- usando los mismos swings de arriba
# ---------------------------------------------------------------------------

TOLERANCIA_PATRON_PCT = 0.15  # cuanto pueden diferir dos picos para considerarse "al mismo nivel"
UMBRAL_PENDIENTE_PLANA_PCT = 0.05  # por debajo de esto, una linea se considera "plana"


def _detectar_doble_techo_suelo(swings, velas):
    """Doble Techo: dos maximos casi iguales con un valle (neckline) entre
    ellos; se confirma cuando el precio cierra por debajo del valle.
    Doble Suelo es la imagen espejo (dos minimos, ruptura hacia arriba)."""
    highs = [s for s in swings if s[1] == "high"]
    lows = [s for s in swings if s[1] == "low"]
    cierre_actual = velas[-1]["c"]
    patrones = []

    # --- Doble Techo (bajista) ---
    if len(highs) >= 2:
        h1, h2 = highs[-2], highs[-1]
        diferencia_pct = abs(h2[2] - h1[2]) / h1[2] * 100
        valle_entre = [l for l in lows if h1[0] < l[0] < h2[0]]
        if diferencia_pct <= TOLERANCIA_PATRON_PCT and valle_entre:
            neckline = min(v[2] for v in valle_entre)
            clave = f"doble_techo_{h2[0]}"
            if cierre_actual < neckline and clave not in _patrones_ya_avisados:
                _patrones_ya_avisados.add(clave)
                altura = h2[2] - neckline
                patrones.append({
                    "nombre": "Doble Techo",
                    "direccion": "bajista",
                    "entry": cierre_actual,
                    "stop_loss": round(h2[2] * 1.001, 2),
                    "take_profit": round(neckline - altura, 2),
                    "detalle": f"Dos maximos cerca de {round(h1[2],2)} y {round(h2[2],2)}, "
                               f"neckline en {round(neckline,2)}",
                    "indice": h2[0]
                })

    # --- Doble Suelo (alcista) ---
    if len(lows) >= 2:
        l1, l2 = lows[-2], lows[-1]
        diferencia_pct = abs(l2[2] - l1[2]) / l1[2] * 100
        pico_entre = [h for h in highs if l1[0] < h[0] < l2[0]]
        if diferencia_pct <= TOLERANCIA_PATRON_PCT and pico_entre:
            neckline = max(p[2] for p in pico_entre)
            clave = f"doble_suelo_{l2[0]}"
            if cierre_actual > neckline and clave not in _patrones_ya_avisados:
                _patrones_ya_avisados.add(clave)
                altura = neckline - l2[2]
                patrones.append({
                    "nombre": "Doble Suelo",
                    "direccion": "alcista",
                    "entry": cierre_actual,
                    "stop_loss": round(l2[2] * 0.999, 2),
                    "take_profit": round(neckline + altura, 2),
                    "detalle": f"Dos minimos cerca de {round(l1[2],2)} y {round(l2[2],2)}, "
                               f"neckline en {round(neckline,2)}",
                    "indice": l2[0]
                })

    return patrones


def _detectar_hch(swings, velas):
    """Hombro-Cabeza-Hombro: tres maximos donde el del medio (cabeza) es el
    mas alto y los dos de los lados (hombros) son similares entre si, con
    dos valles formando el neckline. HCH invertido es la imagen espejo."""
    highs = [s for s in swings if s[1] == "high"]
    lows = [s for s in swings if s[1] == "low"]
    cierre_actual = velas[-1]["c"]
    patrones = []

    # --- HCH normal (bajista) ---
    if len(highs) >= 3:
        h_izq, cabeza, h_der = highs[-3], highs[-2], highs[-1]
        hombros_similares = abs(h_der[2] - h_izq[2]) / h_izq[2] * 100 <= TOLERANCIA_PATRON_PCT * 3
        cabeza_mas_alta = cabeza[2] > h_izq[2] and cabeza[2] > h_der[2]
        valles = [l for l in lows if h_izq[0] < l[0] < h_der[0]]

        if hombros_similares and cabeza_mas_alta and len(valles) >= 2:
            neckline = sum(v[2] for v in valles) / len(valles)
            clave = f"hch_{h_der[0]}"
            if cierre_actual < neckline and clave not in _patrones_ya_avisados:
                _patrones_ya_avisados.add(clave)
                altura = cabeza[2] - neckline
                patrones.append({
                    "nombre": "Hombro-Cabeza-Hombro",
                    "direccion": "bajista",
                    "entry": cierre_actual,
                    "stop_loss": round(h_der[2] * 1.001, 2),
                    "take_profit": round(neckline - altura, 2),
                    "detalle": f"Cabeza en {round(cabeza[2],2)}, neckline aprox {round(neckline,2)}",
                    "indice": h_der[0]
                })

    # --- HCH invertido (alcista) ---
    if len(lows) >= 3:
        l_izq, cabeza, l_der = lows[-3], lows[-2], lows[-1]
        hombros_similares = abs(l_der[2] - l_izq[2]) / l_izq[2] * 100 <= TOLERANCIA_PATRON_PCT * 3
        cabeza_mas_baja = cabeza[2] < l_izq[2] and cabeza[2] < l_der[2]
        picos = [h for h in highs if l_izq[0] < h[0] < l_der[0]]

        if hombros_similares and cabeza_mas_baja and len(picos) >= 2:
            neckline = sum(p[2] for p in picos) / len(picos)
            clave = f"hch_inv_{l_der[0]}"
            if cierre_actual > neckline and clave not in _patrones_ya_avisados:
                _patrones_ya_avisados.add(clave)
                altura = neckline - cabeza[2]
                patrones.append({
                    "nombre": "Hombro-Cabeza-Hombro Invertido",
                    "direccion": "alcista",
                    "entry": cierre_actual,
                    "stop_loss": round(l_der[2] * 0.999, 2),
                    "take_profit": round(neckline + altura, 2),
                    "detalle": f"Cabeza en {round(cabeza[2],2)}, neckline aprox {round(neckline,2)}",
                    "indice": l_der[0]
                })

    return patrones


def _detectar_triangulos_cunas(swings):
    """Analiza la pendiente de los ultimos 3 maximos y los ultimos 3 minimos
    para clasificar el patron. Esto es una aproximacion por pendientes, no
    un ajuste geometrico exacto -- se reporta como CONTEXTO/SESGO, sin
    Entry/SL/TP inventados, porque estos patrones necesitan que la persona
    confirme la ruptura por su cuenta."""
    highs = [s for s in swings if s[1] == "high"][-3:]
    lows = [s for s in swings if s[1] == "low"][-3:]

    if len(highs) < 3 or len(lows) < 3:
        return None

    pendiente_highs_pct = (highs[-1][2] - highs[0][2]) / highs[0][2] * 100
    pendiente_lows_pct = (lows[-1][2] - lows[0][2]) / lows[0][2] * 100

    highs_planos = abs(pendiente_highs_pct) <= UMBRAL_PENDIENTE_PLANA_PCT
    lows_planos = abs(pendiente_lows_pct) <= UMBRAL_PENDIENTE_PLANA_PCT

    if highs_planos and pendiente_lows_pct > UMBRAL_PENDIENTE_PLANA_PCT:
        nombre, sesgo = "Triangulo Ascendente", "alcista (tipicamente)"
    elif lows_planos and pendiente_highs_pct < -UMBRAL_PENDIENTE_PLANA_PCT:
        nombre, sesgo = "Triangulo Descendente", "bajista (tipicamente)"
    elif pendiente_highs_pct < -UMBRAL_PENDIENTE_PLANA_PCT and pendiente_lows_pct > UMBRAL_PENDIENTE_PLANA_PCT:
        nombre, sesgo = "Triangulo Simetrico", "neutral, esperar ruptura"
    elif pendiente_highs_pct > UMBRAL_PENDIENTE_PLANA_PCT and pendiente_lows_pct > UMBRAL_PENDIENTE_PLANA_PCT:
        nombre, sesgo = "Cuna Alcista (rising wedge)", "bajista (tipicamente, patron de reversion)"
    elif pendiente_highs_pct < -UMBRAL_PENDIENTE_PLANA_PCT and pendiente_lows_pct < -UMBRAL_PENDIENTE_PLANA_PCT:
        nombre, sesgo = "Cuna Bajista (falling wedge)", "alcista (tipicamente, patron de reversion)"
    else:
        return None

    clave = f"{nombre}_{highs[-1][0]}_{lows[-1][0]}"
    if clave in _patrones_ya_avisados:
        return None
    _patrones_ya_avisados.add(clave)

    return {
        "nombre": nombre,
        "sesgo": sesgo,
        "detalle": f"Pendiente maximos: {round(pendiente_highs_pct,2)}% | "
                   f"Pendiente minimos: {round(pendiente_lows_pct,2)}%"
    }


# ---------------------------------------------------------------------------
# EQH / EQL: zonas de liquidez (maximos/minimos casi iguales)
# ---------------------------------------------------------------------------

def _detectar_liquidez(swings):
    """Busca pares de swing highs (o lows) muy cercanos entre si -- eso se
    interpreta como una 'zona de liquidez' (EQH o EQL). Devuelve dos listas
    de niveles de precio: [eqh...], [eql...]."""
    highs = sorted([s[2] for s in swings if s[1] == "high"])
    lows = sorted([s[2] for s in swings if s[1] == "low"])

    eqh = []
    for i in range(len(highs) - 1):
        diferencia_pct = abs(highs[i + 1] - highs[i]) / highs[i] * 100
        if diferencia_pct <= TOLERANCIA_EQH_PCT:
            eqh.append(round((highs[i] + highs[i + 1]) / 2, 2))

    eql = []
    for i in range(len(lows) - 1):
        diferencia_pct = abs(lows[i + 1] - lows[i]) / lows[i] * 100
        if diferencia_pct <= TOLERANCIA_EQH_PCT:
            eql.append(round((lows[i] + lows[i + 1]) / 2, 2))

    return eqh, eql


# ---------------------------------------------------------------------------
# FVG: Fair Value Gap (huecos de 3 velas)
# ---------------------------------------------------------------------------

def _detectar_fvg_recientes(velas, max_resultados=2):
    """Revisa las velas en tripletes consecutivos para encontrar FVGs, y
    devuelve solo los que todavia estan 'sin rellenar' (el precio no ha
    vuelto a tocar esa zona desde que se formo)."""
    zonas = []
    n = len(velas)

    for i in range(2, n):
        vela_1 = velas[i - 2]
        vela_3 = velas[i]

        if vela_1["h"] < vela_3["l"]:
            zonas.append({"tipo": "alcista", "desde": vela_1["h"], "hasta": vela_3["l"], "indice": i})
        elif vela_1["l"] > vela_3["h"]:
            zonas.append({"tipo": "bajista", "desde": vela_3["h"], "hasta": vela_1["l"], "indice": i})

    # Marcar como "rellenado" cualquier FVG que una vela posterior ya haya vuelto a tocar
    sin_rellenar = []
    for z in zonas:
        rellenado = False
        for vela_post in velas[z["indice"] + 1:]:
            if vela_post["l"] <= z["hasta"] and vela_post["h"] >= z["desde"]:
                rellenado = True
                break
        if not rellenado:
            sin_rellenar.append(z)

    return sin_rellenar[-max_resultados:]


# ---------------------------------------------------------------------------
# LOGICA PRINCIPAL DE LA SENAL
# ---------------------------------------------------------------------------

def revisar_senal():
    global _ultima_vela_procesada, _contador_senales_hoy

    if en_pausa_fin_de_semana():
        print("En pausa de fin de semana -- se salta revisar_senal()")
        return

    _resetear_contador_si_cambio_el_dia()

    if _en_ventana_blackout_noticias():
        print("Dentro de una ventana de blackout por noticias -- no se mandan senales nuevas de estructura.")
        # Nota: se sigue dejando pasar el chequeo para no perder el registro de
        # patrones/estructura internamente, pero el envio de la senal principal
        # se corta mas abajo con el mismo chequeo antes de avisar por Discord.

    try:
        velas = _obtener_velas()
        if len(velas) < (FUERZA_SWING * 2 + 5):
            print("Senal XAU/USD: no hay suficientes velas todavia.")
            return

        # Si la ultima vela cerrada es la misma que ya procesamos, no hacer nada
        # (evita repetir la misma senal mientras se espera a que cierre la siguiente)
        timestamp_ultima_vela = velas[-1]["t"]
        if timestamp_ultima_vela == _ultima_vela_procesada:
            return
        _ultima_vela_procesada = timestamp_ultima_vela

        swings = _detectar_swings(velas)
        serie_rsi = _calcular_serie_rsi([v["c"] for v in velas])
        rsi_actual = serie_rsi[-1]
        serie_atr = _calcular_serie_atr(velas)
        atr_actual = serie_atr[-1]

        # Si estamos en ventana de blackout por noticias, no mandamos ninguna
        # senal nueva con Entry/SL/TP (ni patrones ni estructura) -- solo se
        # deja pasar el aviso de contexto de triangulos/cunas, que no invita
        # a entrar de inmediato.
        en_blackout = _en_ventana_blackout_noticias()

        # Ventana de alta liquidez: solo se mandan senales de entrada durante
        # los 4 solapamientos de sesiones (Sidney-Tokio, Tokio-Londres,
        # Londres-Nueva York, Nueva York-Sidney), que es cuando de verdad hay
        # participacion suficiente para confiar en una ruptura de estructura.
        sesion_activa = _sesion_alta_liquidez_actual()
        fuera_de_ventana = REQUERIR_VENTANA_ALTA_LIQUIDEZ and sesion_activa is None

        # Confirmacion de liquidez/volumen sobre la vela que dispara la senal
        # (misma vela para patrones y estructura en este ciclo de revision)
        confirma_liquidez, texto_liquidez = _confirma_liquidez_y_volumen(velas, atr_actual)

        no_enviar_entradas = en_blackout or fuera_de_ventana or not confirma_liquidez
        if fuera_de_ventana:
            print("Fuera de las ventanas de solapamiento de sesiones (Sidney/Tokio/Londres/NY) -- no se mandan entradas.")
        if not confirma_liquidez:
            print(f"Liquidez/volumen insuficiente en la vela actual ({texto_liquidez}) -- no se mandan entradas.")

        # --- Patrones chartistas (independientes del BOS/CHoCH) ---
        for patron in ([] if no_enviar_entradas else (_detectar_doble_techo_suelo(swings, velas) + _detectar_hch(swings, velas))):
            # Confirmacion por RSI: un techo (bajista) vale mas si el RSI
            # estuvo en sobrecompra antes de formarse; un suelo (alcista)
            # vale mas si el RSI estuvo en sobreventa.
            idx = patron["indice"]
            ventana_rsi = [r for r in serie_rsi[max(0, idx - 10):idx + 1] if r is not None]

            if patron["direccion"] == "bajista":
                rsi_confirma = bool(ventana_rsi) and max(ventana_rsi) >= RSI_ZONA_SOBRECOMPRA - 5
            else:
                rsi_confirma = bool(ventana_rsi) and min(ventana_rsi) <= RSI_ZONA_SOBREVENTA + 5

            if not rsi_confirma:
                print(f"Patron {patron['nombre']} detectado, pero el RSI no lo confirma -- no se manda.")
                continue

            tipo_senal_patron = "BUY" if patron["direccion"] == "alcista" else "SELL"
            color_patron = 0x5DCAA5 if patron["direccion"] == "alcista" else 0xE24B4A
            enviar_discord(
                f"{patron['nombre']} -- posible entrada {tipo_senal_patron}",
                f"Direccion: {tipo_senal_patron} ({patron['direccion']})\n"
                f"Precio actual: {patron['entry']} USD/oz (velas {GRANULARIDAD})\n"
                f"Entry sugerido: {patron['entry']}\n"
                f"Stop Loss: {patron['stop_loss']}\n"
                f"Take Profit: {patron['take_profit']} (altura del patron proyectada)\n"
                f"RSI de confirmacion: {round(max(ventana_rsi) if patron['direccion']=='bajista' else min(ventana_rsi), 2)}\n"
                f"Sesion activa: {sesion_activa} (alta liquidez)\n"
                f"Liquidez/volumen: {texto_liquidez}\n\n"
                f"{patron['detalle']}\n\n"
                f"IMPORTANTE: los patrones chartistas son herramientas de "
                f"analisis tecnico, no garantias. Este bot NO ejecuta ninguna "
                f"orden. Revisa el grafico y decide tu si te conviene entrar.",
                color=color_patron
            )

        patron_geometrico = _detectar_triangulos_cunas(swings)
        if patron_geometrico:
            enviar_discord(
                f"Patron chartista formandose: {patron_geometrico['nombre']}",
                f"Sesgo tipico: {patron_geometrico['sesgo']}\n"
                f"{patron_geometrico['detalle']}\n\n"
                f"Este es un aviso de CONTEXTO -- todavia no hay ruptura "
                f"confirmada, asi que no doy Entry/Stop Loss/Take Profit. "
                f"Vigila el grafico para ver hacia donde rompe.",
                color=0xEF9F27
            )

        evento = _detectar_evento_estructura(velas, swings)

        if evento is None:
            return  # sin cambio de estructura en esta vela, no hay nada mas que avisar

        if no_enviar_entradas:
            razon = ("blackout por noticias" if en_blackout else
                      "fuera de ventana de solapamiento de sesiones" if fuera_de_ventana else
                      f"liquidez/volumen insuficiente ({texto_liquidez})")
            print(f"Senal XAU/USD: {evento['tipo']} {evento['direccion']} detectado, pero {razon} -- no se manda.")
            return

        if _contador_senales_hoy >= MAX_SENALES_ESTRUCTURA_POR_DIA:
            print(f"Senal XAU/USD: {evento['tipo']} {evento['direccion']} detectado, pero ya se "
                  f"alcanzo el limite de {MAX_SENALES_ESTRUCTURA_POR_DIA} senales de estructura hoy -- no se manda.")
            return

        # Filtro de tendencia diaria: solo avisamos si la senal va a favor del dia
        tendencia_diaria = _obtener_tendencia_diaria(velas)
        if tendencia_diaria is not None and tendencia_diaria != evento["direccion"]:
            print(
                f"Senal XAU/USD: {evento['tipo']} {evento['direccion']} detectado, "
                f"pero el dia esta {tendencia_diaria} -- no se manda (va en contra del dia)."
            )
            return

        # Filtro de RSI: BUY solo si hay impulso alcista sano (entre 50 y 70,
        # ni plano ni ya sobrecomprado); SELL solo si hay impulso bajista sano
        if rsi_actual is not None:
            if evento["direccion"] == "alcista":
                rsi_confirma = 50 <= rsi_actual < RSI_ZONA_SOBRECOMPRA
            else:
                rsi_confirma = RSI_ZONA_SOBREVENTA < rsi_actual <= 50

            if not rsi_confirma:
                print(
                    f"Senal XAU/USD: {evento['tipo']} {evento['direccion']} detectado, "
                    f"pero el RSI ({rsi_actual}) no confirma -- no se manda."
                )
                return

        precio_actual = velas[-1]["c"]
        eqh, eql = _detectar_liquidez(swings)
        fvgs = _detectar_fvg_recientes(velas)

        # Colchon del Stop Loss: si hay ATR disponible, se usa un multiplo de
        # la volatilidad real (mas lejos en dias movidos, mas cerca en dias
        # tranquilos); si todavia no hay suficiente historial para el ATR,
        # se cae al margen fijo de antes como respaldo.
        colchon = (MULTIPLICADOR_ATR_SL * atr_actual) if atr_actual else None

        if evento["direccion"] == "alcista":
            tipo_senal = "BUY"
            # Stop Loss: debajo del swing que confirmo la estructura, menos un
            # colchon de ATR (o el margen fijo de respaldo si no hay ATR)
            if evento["swing_opuesto"]:
                stop_loss = round(evento["swing_opuesto"] - colchon, 2) if colchon else round(evento["swing_opuesto"] * 0.999, 2)
            else:
                stop_loss = round(precio_actual - colchon, 2) if colchon else round(precio_actual * 0.995, 2)
            # Take Profit: el EQH mas cercano por encima del precio actual, si existe
            objetivos = sorted([n for n in eqh if n > precio_actual])
            take_profit = objetivos[0] if objetivos else round(precio_actual + (precio_actual - stop_loss) * RATIO_RIESGO_BENEFICIO_RESPALDO, 2)
            fuente_tp = "zona de liquidez EQH" if objetivos else f"respaldo 1:{RATIO_RIESGO_BENEFICIO_RESPALDO}"
            color = 0x5DCAA5
        else:
            tipo_senal = "SELL"
            if evento["swing_opuesto"]:
                stop_loss = round(evento["swing_opuesto"] + colchon, 2) if colchon else round(evento["swing_opuesto"] * 1.001, 2)
            else:
                stop_loss = round(precio_actual + colchon, 2) if colchon else round(precio_actual * 1.005, 2)
            objetivos = sorted([n for n in eql if n < precio_actual], reverse=True)
            take_profit = objetivos[0] if objetivos else round(precio_actual - (stop_loss - precio_actual) * RATIO_RIESGO_BENEFICIO_RESPALDO, 2)
            fuente_tp = "zona de liquidez EQL" if objetivos else f"respaldo 1:{RATIO_RIESGO_BENEFICIO_RESPALDO}"
            color = 0xE24B4A

        lineas_fvg = []
        for z in fvgs:
            lineas_fvg.append(f"FVG {z['tipo']} sin rellenar: {round(z['desde'],2)} - {round(z['hasta'],2)}")
        texto_fvg = "\n".join(lineas_fvg) if lineas_fvg else "Sin FVG relevantes sin rellenar cerca."
        texto_atr = f"{round(atr_actual, 2)} USD (SL con colchon de {MULTIPLICADOR_ATR_SL}x ATR)" if atr_actual else "sin dato suficiente todavia (usando margen fijo de respaldo)"

        enviar_discord(
            f"{evento['tipo']} {evento['direccion'].upper()} -- posible entrada {tipo_senal}",
            f"Precio actual: {precio_actual} USD/oz (velas {GRANULARIDAD})\n"
            f"Entry sugerido: {precio_actual}\n"
            f"Stop Loss: {stop_loss} (mas alla del swing que confirmo la estructura)\n"
            f"Take Profit: {take_profit} ({fuente_tp})\n"
            f"ATR (14): {texto_atr}\n"
            f"Sesion activa: {sesion_activa} (alta liquidez)\n"
            f"Liquidez/volumen: {texto_liquidez}\n\n"
            f"Evento de estructura: {evento['tipo']} -- rompio el nivel {round(evento['nivel_roto'],2)}\n"
            f"Va a favor de la tendencia diaria ({tendencia_diaria or 'sin dato claro'}).\n"
            f"RSI de confirmacion (Wilder): {rsi_actual}\n\n"
            f"{texto_fvg}\n\n"
            f"Senal {_contador_senales_hoy + 1} de {MAX_SENALES_ESTRUCTURA_POR_DIA} permitidas hoy.\n\n"
            f"IMPORTANTE: BOS/CHoCH/EQH/FVG son patrones de analisis tecnico, "
            f"no garantias. Este bot NO ejecuta ninguna orden. Revisa el "
            f"grafico y decide tu si te conviene entrar.",
            color=color
        )

        _contador_senales_hoy += 1
        _registrar_senal_historial(
            evento["tipo"], evento["direccion"], precio_actual, stop_loss, take_profit,
            rsi_actual, extra=f"ATR={atr_actual}"
        )

    except Exception as e:
        print(f"Error revisando senal XAU/USD: {e}")


# ---------------------------------------------------------------------------
# REPORTE BAJO DEMANDA: lo que se manda cuando alguien presiona el boton
# ---------------------------------------------------------------------------

def generar_reporte_bajo_demanda():
    """Genera una 'foto' del estado actual del mercado, sin esperar a que
    cierre una vela ni a que se cumpla ningun filtro -- para cuando la
    persona quiere saber YA si hay algo interesante pasando. No modifica
    ningun estado interno (no interfiere con las alertas automaticas)."""
    if en_pausa_fin_de_semana():
        return discord.Embed(
            title="El mercado esta cerrado (fin de semana)",
            description=(
                "XAU/USD no opera de viernes en la noche a domingo en la noche "
                "(hora Madrid). Los datos de este momento estarian desactualizados "
                "o vacios. El bot vuelve a revisar solo apenas reabra el mercado."
            ),
            color=0xEF9F27
        )
    try:
        velas = _obtener_velas()
        if len(velas) < (FUERZA_SWING * 2 + 5):
            return discord.Embed(
                title="Todavia no hay suficientes datos",
                description="Intenta de nuevo en unos minutos.",
                color=0xEF9F27
            )

        swings = _detectar_swings(velas)
        serie_rsi = _calcular_serie_rsi([v["c"] for v in velas])
        rsi_actual = serie_rsi[-1]
        serie_atr = _calcular_serie_atr(velas)
        atr_actual = serie_atr[-1]
        tendencia_diaria = _obtener_tendencia_diaria(velas)
        precio_actual = velas[-1]["c"]

        highs = [s for s in swings if s[1] == "high"]
        lows = [s for s in swings if s[1] == "low"]
        ultimo_high = highs[-1][2] if highs else None
        ultimo_low = lows[-1][2] if lows else None

        if ultimo_high and precio_actual > ultimo_high:
            sesgo = (f"El precio ({precio_actual}) ya esta por ENCIMA del ultimo "
                     f"maximo relevante ({round(ultimo_high,2)}) -- sesgo ALCISTA activo.")
            color = 0x5DCAA5
        elif ultimo_low and precio_actual < ultimo_low:
            sesgo = (f"El precio ({precio_actual}) ya esta por DEBAJO del ultimo "
                     f"minimo relevante ({round(ultimo_low,2)}) -- sesgo BAJISTA activo.")
            color = 0xE24B4A
        else:
            sesgo = (f"El precio ({precio_actual}) esta DENTRO del rango, entre el "
                     f"soporte ({round(ultimo_low,2) if ultimo_low else 'sin dato'}) y "
                     f"la resistencia ({round(ultimo_high,2) if ultimo_high else 'sin dato'}). "
                     f"Sin ruptura confirmada ahora mismo.")
            color = 0xEF9F27

        if rsi_actual is None:
            zona_rsi = "sin dato suficiente todavia"
        elif rsi_actual >= RSI_ZONA_SOBRECOMPRA:
            zona_rsi = f"{rsi_actual} -- sobrecompra"
        elif rsi_actual <= RSI_ZONA_SOBREVENTA:
            zona_rsi = f"{rsi_actual} -- sobreventa"
        else:
            zona_rsi = f"{rsi_actual} -- zona neutral"

        eqh, eql = _detectar_liquidez(swings)
        fvgs = _detectar_fvg_recientes(velas)
        lineas_fvg = [f"FVG {z['tipo']}: {round(z['desde'],2)} - {round(z['hasta'],2)}" for z in fvgs]

        texto_atr = f"{round(atr_actual, 2)} USD" if atr_actual else "sin dato suficiente todavia"
        sesion_activa = _sesion_alta_liquidez_actual()
        confirma_liquidez, texto_liquidez = _confirma_liquidez_y_volumen(velas, atr_actual)

        descripcion = (
            f"**Precio actual:** {precio_actual} USD/oz (velas {GRANULARIDAD})\n"
            f"**Estructura:** {sesgo}\n"
            f"**RSI (Wilder):** {zona_rsi}\n"
            f"**ATR (14):** {texto_atr}\n"
            f"**Tendencia del dia (EMA20 diaria):** {tendencia_diaria or 'sin dato claro'}\n"
            f"**Sesion de alta liquidez ahora:** {sesion_activa or 'ninguna (fuera de solapamiento)'}\n"
            f"**Liquidez/volumen de la vela actual:** {texto_liquidez}\n"
            f"**Senales de estructura enviadas hoy:** {_contador_senales_hoy}/{MAX_SENALES_ESTRUCTURA_POR_DIA}\n\n"
            f"**Zonas de liquidez (EQH):** " +
            (", ".join(str(round(x, 2)) for x in eqh) if eqh else "ninguna detectada") + "\n"
            f"**Zonas de liquidez (EQL):** " +
            (", ".join(str(round(x, 2)) for x in eql) if eql else "ninguna detectada") + "\n"
            f"**FVG sin rellenar:**\n" + ("\n".join(lineas_fvg) if lineas_fvg else "ninguno relevante") + "\n\n"
            f"Esto es una foto del momento, generada bajo demanda -- no espera "
            f"a que cierre una vela. Las senales automaticas confirmadas (con "
            f"Entry/Stop Loss/Take Profit) te siguen llegando solas cuando se "
            f"cumplen todos los filtros. Esto NO es asesoria financiera, la "
            f"decision es tuya."
        )

        embed = discord.Embed(title="Estado actual de XAU/USD (bajo demanda)", description=descripcion, color=color)
        embed.set_footer(text=f"Hora Madrid: {hora_madrid()}")
        return embed

    except Exception as e:
        return discord.Embed(title="Error generando el reporte", description=str(e), color=0xE24B4A)


class VistaMonitor(discord.ui.View):
    """El boton fijo que se queda en el canal. timeout=None para que no
    caduque nunca, y custom_id fijo para que siga funcionando aunque el
    bot se reinicie (Render lo reinicia de vez en cuando)."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Monitorear compra/venta ahora", style=discord.ButtonStyle.primary,
                        emoji="🔍", custom_id="monitorear_ahora_xauusd")
    async def boton_monitorear(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)
        embed = await asyncio.to_thread(generar_reporte_bajo_demanda)
        await interaction.followup.send(embed=embed)


# ---------------------------------------------------------------------------
# MINI SERVIDOR WEB (para hosts gratuitos tipo Render + UptimeRobot)
# ---------------------------------------------------------------------------

def iniciar_servidor_web():
    puerto = int(os.environ.get("PORT", 8080))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot de senales ICT XAU/USD activo")

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()

        def log_message(self, format, *args):
            pass

    servidor = HTTPServer(("0.0.0.0", puerto), Handler)
    servidor.serve_forever()


# ---------------------------------------------------------------------------
# EVENTOS DEL BOT DE DISCORD
# ---------------------------------------------------------------------------

@tasks.loop(minutes=INTERVALO_REVISION_MINUTOS)
async def revisar_periodicamente():
    # revisar_senal() hace peticiones de red (bloqueantes) -- lo mandamos a
    # un hilo aparte para no congelar la conexion del bot con Discord
    await asyncio.to_thread(revisar_senal)


@client.event
async def on_ready():
    global _canal
    _canal = client.get_channel(DISCORD_CHANNEL_ID)
    client.add_view(VistaMonitor())  # para que el boton siga vivo tras reinicios

    print(f"Bot conectado como {client.user}. Hora Madrid: {hora_madrid()}")

    if _canal is not None:
        await _canal.send(
            content=(
                "**Bot de senales ICT XAU/USD iniciado.**\n"
                f"Vigilando con velas reales ({GRANULARIDAD}), filtradas por la "
                f"tendencia del dia y confirmadas por RSI. Te aviso solo cuando "
                f"detecte algo confirmado -- y puedes presionar el boton de abajo "
                f"para revisar el estado cuando quieras, sin esperar."
            ),
            view=VistaMonitor()
        )
    else:
        print("ATENCION: no se encontro el canal -- revisa DISCORD_CHANNEL_ID.")

    if not revisar_periodicamente.is_running():
        revisar_periodicamente.start()


# ---------------------------------------------------------------------------
# PROGRAMACION
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    threading.Thread(target=iniciar_servidor_web, daemon=True).start()
    client.run(DISCORD_BOT_TOKEN)
