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
import csv
import json
import statistics
from collections import deque
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

# --- Integracion V3 (fusion): API keys nuevas, todas opcionales -- si no se
# configuran, las funciones que las usan simplemente no hacen nada (no
# rompen el resto del bot). ---
# Segunda cuenta de Twelve Data, solo para las velas H1/H4/D1 del
# multi-timeframe -- si falla la cuenta principal, se prueba esta.
TWELVE_DATA_BACKUP_API_KEY = os.environ.get("TWELVE_DATA_BACKUP_API_KEY", "")
# Alpaca (cuenta de bróker, puede ser de paper trading/demo): necesaria para
# la correlacion con el dolar (UUP), el oro via ETF (GLD) y la liquidez del
# SPY. Gratis en https://alpaca.markets/
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "PON_AQUI_TU_API_KEY")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY", "PON_AQUI_TU_SECRET_KEY")

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
FUERZA_SWING = 2

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


# =============================================================================
# === INTEGRACION V3 (fusion) -- BLOQUE AGREGADO =============================
# Todo lo de aqui en adelante (hasta el marcador de cierre) es nuevo, portado
# de bot_xauusd_fusion_v3.py a peticion del usuario. Nada de lo que hay
# ARRIBA de este bloque se modifico. Se integraron 3 piezas:
#   1) Score de confianza (PREMIUM/NORMAL) + confirmacion multi-timeframe H1/H4/D1
#   2) Horario operativo fijo + cache de velas (menos consultas a la API)
#   3) Patrones nuevos: Bandera/Banderin + Barrido de liquidez (sweep)
#   4) Correlacion via Alpaca: dolar (UUP), oro via ETF (GLD), liquidez (SPY)
# El modulo de noticias/macro (FRED, EIA, Finnhub, GDELT) del archivo
# original NO se incluyo -- el usuario pidio dejar el bot enfocado solo en
# XAU/USD para eso.
# =============================================================================

# --- 1) Score de confianza: umbrales de clasificacion por calidad ---
SCORE_UMBRAL_PREMIUM = 80
SCORE_UMBRAL_NORMAL = 65

# --- 1) Multi-timeframe: bonus de confianza si H1/H4/D1 coinciden con la
# direccion de la senal (M15) ---
BONUS_MULTI_TIMEFRAME = 20
_cache_velas_htf = {"h1": {"datos": None, "momento": None},
                     "h4": {"datos": None, "momento": None},
                     "d1": {"datos": None, "momento": None}}
# H1/H4/D1 no cambian de tendencia de un minuto a otro, asi que se cachean
# 60 minutos -- evita gastar 3 consultas extra de la API en cada revision
# de 5 minutos.
CACHE_HTF_MAX_MINUTOS = 60

# --- 2) Horario operativo fijo: fuera de esta ventana (hora Madrid),
# revisar_senal() no hace ninguna consulta nueva a la API -- ahorra cuota
# de verdad, a diferencia del filtro de sesion activa que ya existia (ese
# si consulta, solo que despues no manda la entrada). Por defecto cubre el
# solapamiento Londres-Nueva York con margen. ---
HORA_INICIO_OPERATIVA = "09:00"
HORA_FIN_OPERATIVA = "22:00"

# --- 2) Cache de velas M15: para que las funciones de correlacion (oro via
# GLD, etc.) no vuelvan a pedirle velas a Twelve Data si ya se pidieron
# hace pocos minutos para otra cosa. ---
CACHE_VELAS_MAX_MINUTOS = 6
_cache_velas_m15 = {"datos": None, "momento": None}

# --- 3) Bandera/Banderin (patrones de continuacion) ---
VENTANA_IMPULSO_BANDERA = 6         # velas que forman el "asta" (impulso previo)
VENTANA_CONSOLIDACION_BANDERA = 5   # velas que forman la bandera/banderin (sin la de confirmacion)
UMBRAL_IMPULSO_BANDERA_PCT = 0.5    # movimiento minimo del asta para considerarse impulso real
RATIO_CONSOLIDACION_MAX = 0.5       # la consolidacion debe ser <= 50% del rango del asta

# --- 4) Correlacion via Alpaca: dolar (UUP), oro via ETF (GLD), liquidez (SPY) ---
SIMBOLO_DOLAR = "UUP"
UMBRAL_CAIDA_DOLAR = 1.0
UMBRAL_SUBIDA_DOLAR = 0.1
SIMBOLO_ORO_ETF = "GLD"
INTERVALO_ORO_MINUTOS = 10
SIMBOLO_LIQUIDEZ = "SPY"
UMBRAL_SPREAD = 1.8
UMBRAL_VOLUMEN = 2.0
_historial_spread = deque(maxlen=20)
_historial_volumen = deque(maxlen=20)
# Dedup para no repetir el mismo aviso de correlacion una y otra vez
_ya_notificado_v3 = set()


def _obtener_velas_htf(intervalo, cantidad=60):
    """Pide velas de un timeframe superior (1h, 4h, 1day) a Twelve Data,
    para el multi-timeframe."""
    params = {
        "symbol": SIMBOLO, "interval": intervalo, "outputsize": cantidad,
        "timezone": "UTC", "apikey": TWELVE_DATA_API_KEY,
    }
    r = requests.get(TWELVE_DATA_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("status") == "error":
        raise RuntimeError(f"Twelve Data error ({intervalo}): {data.get('message')}")
    velas = []
    for v in data.get("values", []):
        velas.append({
            "t": v["datetime"], "o": float(v["open"]), "h": float(v["high"]),
            "l": float(v["low"]), "c": float(v["close"]),
        })
    velas.reverse()
    return velas


def _obtener_velas_htf_respaldo(intervalo, cantidad=60):
    """Copia de _obtener_velas_htf() usando la segunda cuenta de Twelve Data
    (TWELVE_DATA_BACKUP_API_KEY) -- opcional, si no esta configurada
    simplemente no hay respaldo para las velas H1/H4/D1."""
    if not TWELVE_DATA_BACKUP_API_KEY:
        return []
    params = {
        "symbol": SIMBOLO, "interval": intervalo, "outputsize": cantidad,
        "timezone": "UTC", "apikey": TWELVE_DATA_BACKUP_API_KEY,
    }
    r = requests.get(TWELVE_DATA_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("status") == "error":
        raise RuntimeError(f"Twelve Data (respaldo) error ({intervalo}): {data.get('message')}")
    velas = []
    for v in data.get("values", []):
        velas.append({
            "t": v["datetime"], "o": float(v["open"]), "h": float(v["high"]),
            "l": float(v["low"]), "c": float(v["close"]),
        })
    velas.reverse()
    return velas


def _obtener_velas_htf_con_respaldo(intervalo, cantidad=60):
    try:
        return _obtener_velas_htf(intervalo, cantidad)
    except Exception as e:
        print(f"[V3] Twelve Data ({intervalo}, cuenta principal) fallo ({e}), probando cuenta de respaldo...")
        try:
            return _obtener_velas_htf_respaldo(intervalo, cantidad)
        except Exception as e2:
            print(f"[V3] Twelve Data ({intervalo}, respaldo) tambien fallo: {e2}")
            return []


def _obtener_velas_htf_cacheadas(clave_cache, intervalo):
    """Devuelve las velas del timeframe pedido usando cache (60 min)."""
    ahora = datetime.now(MADRID_TZ)
    entrada = _cache_velas_htf[clave_cache]
    if entrada["datos"] is not None and entrada["momento"] is not None:
        if (ahora - entrada["momento"]).total_seconds() < CACHE_HTF_MAX_MINUTOS * 60:
            return entrada["datos"]
    try:
        velas = _obtener_velas_htf_con_respaldo(intervalo)
    except Exception as e:
        print(f"[V3] No se pudieron obtener velas {clave_cache.upper()} para multi-timeframe: {e}")
        velas = entrada["datos"] or []
    _cache_velas_htf[clave_cache] = {"datos": velas, "momento": ahora}
    return velas


def _tendencia_simple_htf(velas, periodo_ema=20):
    """Tendencia simple de un timeframe superior: precio actual vs EMA del
    periodo pedido sobre los cierres. Devuelve 'alcista', 'bajista' o None."""
    if not velas:
        return None
    cierres = [v["c"] for v in velas]
    ema = _ema(cierres, periodo_ema)
    if ema is None:
        return None
    if cierres[-1] > ema:
        return "alcista"
    elif cierres[-1] < ema:
        return "bajista"
    return None


def _confirmacion_multi_timeframe(direccion_senal):
    """Comprueba la tendencia en H1, H4 y D1. Si las 3 coinciden con la
    direccion de la senal (M15), otorga un bonus de confianza -- no bloquea
    la senal si no coinciden, solo suma puntos extra cuando hay alineacion
    total. Devuelve (bonus, detalle_texto)."""
    velas_h1 = _obtener_velas_htf_cacheadas("h1", "1h")
    velas_h4 = _obtener_velas_htf_cacheadas("h4", "4h")
    velas_d1 = _obtener_velas_htf_cacheadas("d1", "1day")

    tendencia_h1 = _tendencia_simple_htf(velas_h1)
    tendencia_h4 = _tendencia_simple_htf(velas_h4)
    tendencia_d1 = _tendencia_simple_htf(velas_d1)

    coinciden = (
        tendencia_h1 == direccion_senal and
        tendencia_h4 == direccion_senal and
        tendencia_d1 == direccion_senal
    )

    detalle = (f"M15: {direccion_senal} | H1: {tendencia_h1 or 'sin dato'} | "
               f"H4: {tendencia_h4 or 'sin dato'} | D1: {tendencia_d1 or 'sin dato'}")

    if coinciden:
        return BONUS_MULTI_TIMEFRAME, detalle
    return 0, detalle


def _calcular_score_confianza(factores):
    """Recibe una lista de tuplas (nombre_factor, cumple: bool, puntos: int)
    y devuelve (score_total, lista_texto_con_checks). El score se limita a
    0-100."""
    score = 0
    lineas = []
    for nombre, cumple, puntos in factores:
        if cumple:
            score += puntos
            lineas.append(f"✅ {nombre}")
        else:
            lineas.append(f"❌ {nombre}")
    score = max(0, min(100, score))
    return score, lineas


def _clasificar_calidad_senal(score):
    """Clasifica la senal segun el score de confianza: >=80 -> PREMIUM,
    >=65 -> NORMAL, menos -> DESCARTADA."""
    if score >= SCORE_UMBRAL_PREMIUM:
        return "PREMIUM"
    elif score >= SCORE_UMBRAL_NORMAL:
        return "NORMAL"
    return "DESCARTADA"


def _etiqueta_calidad_y_score(direccion, factores_base):
    """Junta el bonus de multi-timeframe con los factores base de la senal
    (los que ya paso para llegar hasta aqui) y devuelve una etiqueta lista
    para anteponer al titulo del mensaje, ej. 'BUY ⭐ PREMIUM (92/100)'."""
    bonus_mtf, detalle_mtf = _confirmacion_multi_timeframe(direccion)
    score, _lineas = _calcular_score_confianza(factores_base)
    score = max(0, min(100, score + bonus_mtf))
    calidad = _clasificar_calidad_senal(score)
    etiqueta = "⭐ PREMIUM" if calidad == "PREMIUM" else "NORMAL"
    return etiqueta, score, detalle_mtf


def _dentro_de_horario_operativo():
    """True si la hora actual de Madrid cae dentro de la ventana operativa
    (por defecto 09:00-22:00). Fuera de esta ventana, revisar_senal() no
    hace ninguna consulta nueva a la API."""
    ahora = datetime.now(MADRID_TZ).time()
    inicio = datetime.strptime(HORA_INICIO_OPERATIVA, "%H:%M").time()
    fin = datetime.strptime(HORA_FIN_OPERATIVA, "%H:%M").time()
    return inicio <= ahora <= fin


def _obtener_velas_cacheadas():
    """Devuelve las velas M15 usando cache (unos pocos minutos) -- para que
    las funciones de correlacion (estado del oro, etc.) no gasten una
    consulta nueva a Twelve Data si el ciclo principal ya las pidio hace
    poco. Usa _obtener_velas(), la misma funcion (con su propio respaldo a
    Alpha Vantage) que ya usa revisar_senal() -- no se toca esa funcion."""
    ahora = datetime.now(MADRID_TZ)
    entrada = _cache_velas_m15
    if entrada["datos"] is not None and entrada["momento"] is not None:
        if (ahora - entrada["momento"]).total_seconds() < CACHE_VELAS_MAX_MINUTOS * 60:
            return entrada["datos"]
    try:
        velas = _obtener_velas()
    except Exception as e:
        print(f"[V3] No se pudieron obtener velas M15 cacheadas: {e}")
        velas = entrada["datos"] or []
    _cache_velas_m15["datos"] = velas
    _cache_velas_m15["momento"] = ahora
    return velas


def _detectar_barrido_liquidez(velas, eqh, eql):
    """Revisa si la ultima o penultima vela supero una zona de liquidez
    conocida (EQH/EQL) pero la ultima vela ya cerro revirtiendo hacia el
    otro lado -- eso sugiere que el movimiento fue a cazar stops antes de
    girar, no una ruptura real. Devuelve una senal independiente del
    BOS/CHoCH normal, o None."""
    if len(velas) < 2:
        return None
    ultima = velas[-1]
    anterior = velas[-2]

    for nivel in eqh:
        margen = nivel * (TOLERANCIA_EQH_PCT / 100)
        supero = anterior["h"] > nivel or ultima["h"] > nivel
        revierte = ultima["c"] < nivel - margen
        if supero and revierte:
            clave = f"barrido_eqh_{round(nivel, 2)}"
            if clave in _patrones_ya_avisados:
                continue
            _patrones_ya_avisados.add(clave)
            return {
                "direccion": "bajista",
                "nivel": nivel,
                "entry": ultima["c"],
                "stop_loss": round(max(anterior["h"], ultima["h"]) * 1.001, 2),
            }

    for nivel in eql:
        margen = nivel * (TOLERANCIA_EQH_PCT / 100)
        supero = anterior["l"] < nivel or ultima["l"] < nivel
        revierte = ultima["c"] > nivel + margen
        if supero and revierte:
            clave = f"barrido_eql_{round(nivel, 2)}"
            if clave in _patrones_ya_avisados:
                continue
            _patrones_ya_avisados.add(clave)
            return {
                "direccion": "alcista",
                "nivel": nivel,
                "entry": ultima["c"],
                "stop_loss": round(min(anterior["l"], ultima["l"]) * 0.999, 2),
            }

    return None


def _detectar_banderas_banderines(velas):
    """Detecta banderas (consolidacion en canal) y banderines (consolidacion
    que converge) tras un movimiento impulsivo, confirmados cuando el
    precio rompe la consolidacion continuando en la direccion del impulso
    previo. Devuelve una lista de patrones (normalmente 0 o 1) con el mismo
    formato que los demas detectores de patrones (nombre, direccion, entry,
    stop_loss, take_profit, detalle, indice)."""
    total_ventana = VENTANA_IMPULSO_BANDERA + VENTANA_CONSOLIDACION_BANDERA + 1
    if len(velas) < total_ventana:
        return []

    velas_asta = velas[-total_ventana:-(VENTANA_CONSOLIDACION_BANDERA + 1)]
    velas_consolidacion = velas[-(VENTANA_CONSOLIDACION_BANDERA + 1):-1]
    vela_confirmacion = velas[-1]

    if not velas_asta or not velas_consolidacion:
        return []

    precio_inicio_asta = velas_asta[0]["o"]
    precio_fin_asta = velas_asta[-1]["c"]
    if precio_inicio_asta == 0:
        return []
    impulso_pct = (precio_fin_asta - precio_inicio_asta) / precio_inicio_asta * 100
    impulso_abs = abs(precio_fin_asta - precio_inicio_asta)

    if abs(impulso_pct) < UMBRAL_IMPULSO_BANDERA_PCT or impulso_abs == 0:
        return []

    direccion_impulso = "alcista" if impulso_pct > 0 else "bajista"

    maximo_consolidacion = max(v["h"] for v in velas_consolidacion)
    minimo_consolidacion = min(v["l"] for v in velas_consolidacion)
    rango_consolidacion = maximo_consolidacion - minimo_consolidacion

    if rango_consolidacion > impulso_abs * RATIO_CONSOLIDACION_MAX:
        return []

    mitad = max(1, len(velas_consolidacion) // 2)
    primera_mitad = velas_consolidacion[:mitad]
    segunda_mitad = velas_consolidacion[mitad:] or primera_mitad
    rango_primera_mitad = max(v["h"] for v in primera_mitad) - min(v["l"] for v in primera_mitad)
    rango_segunda_mitad = max(v["h"] for v in segunda_mitad) - min(v["l"] for v in segunda_mitad)

    if rango_primera_mitad > 0 and rango_segunda_mitad <= rango_primera_mitad * 0.6:
        nombre = "Banderin (pennant)"
    else:
        nombre = "Bandera (flag)"

    cierre_confirmacion = vela_confirmacion["c"]
    patrones = []

    if direccion_impulso == "alcista" and cierre_confirmacion > maximo_consolidacion:
        clave = f"bandera_alcista_{len(velas)}_{round(maximo_consolidacion, 2)}"
        if clave not in _patrones_ya_avisados:
            _patrones_ya_avisados.add(clave)
            patrones.append({
                "nombre": nombre,
                "direccion": "alcista",
                "entry": cierre_confirmacion,
                "stop_loss": round(minimo_consolidacion * 0.999, 2),
                "take_profit": round(cierre_confirmacion + impulso_abs, 2),
                "detalle": (f"Asta previo de {round(impulso_pct, 2)}% "
                            f"({round(precio_inicio_asta,2)} -> {round(precio_fin_asta,2)}), "
                            f"consolidacion entre {round(minimo_consolidacion,2)} y "
                            f"{round(maximo_consolidacion,2)}, ruptura al alza confirmada."),
                "indice": len(velas) - 1,
            })

    elif direccion_impulso == "bajista" and cierre_confirmacion < minimo_consolidacion:
        clave = f"bandera_bajista_{len(velas)}_{round(minimo_consolidacion, 2)}"
        if clave not in _patrones_ya_avisados:
            _patrones_ya_avisados.add(clave)
            patrones.append({
                "nombre": nombre,
                "direccion": "bajista",
                "entry": cierre_confirmacion,
                "stop_loss": round(maximo_consolidacion * 1.001, 2),
                "take_profit": round(cierre_confirmacion - impulso_abs, 2),
                "detalle": (f"Asta previo de {round(impulso_pct, 2)}% "
                            f"({round(precio_inicio_asta,2)} -> {round(precio_fin_asta,2)}), "
                            f"consolidacion entre {round(minimo_consolidacion,2)} y "
                            f"{round(maximo_consolidacion,2)}, ruptura a la baja confirmada."),
                "indice": len(velas) - 1,
            })

    return patrones


# --- Correlacion via Alpaca: dolar (UUP) ---

def _obtener_dolar_datos():
    headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}
    desde = (datetime.now(MADRID_TZ) - timedelta(days=7)).strftime("%Y-%m-%d")
    url_bars = f"https://data.alpaca.markets/v2/stocks/{SIMBOLO_DOLAR}/bars"
    params = {"timeframe": "1Day", "start": desde, "limit": 10}
    data_bars = requests.get(url_bars, headers=headers, params=params, timeout=10).json()
    barras = data_bars.get("bars", [])
    if not barras:
        return None

    maximo_semanal = max(b["h"] for b in barras)
    maximo_previo = max((b["h"] for b in barras[:-1]), default=barras[0]["h"])

    url_snap = f"https://data.alpaca.markets/v2/stocks/{SIMBOLO_DOLAR}/snapshot"
    snap = requests.get(url_snap, headers=headers, timeout=10).json()
    precio_actual = snap["latestTrade"]["p"]

    return precio_actual, maximo_semanal, maximo_previo


def revisar_dolar_maximo_semanal():
    """Avisa cuando el dolar (proxy UUP) cae o rompe su maximo semanal --
    util como contexto de correlacion inversa con el oro. Requiere
    ALPACA_API_KEY/ALPACA_SECRET_KEY configuradas; si no lo estan, no hace
    nada."""
    if en_pausa_fin_de_semana():
        return
    if "PON_AQUI" in ALPACA_API_KEY:
        return
    try:
        datos = _obtener_dolar_datos()
        if datos is None:
            return
        precio_actual, maximo_semanal, maximo_previo = datos
        hoy = datetime.now(MADRID_TZ).strftime("%Y-%m-%d")

        caida_pct = round((maximo_semanal - precio_actual) / maximo_semanal * 100, 2)
        clave_caida = f"usd_caida_{hoy}_{int(caida_pct)}"
        if caida_pct >= UMBRAL_CAIDA_DOLAR and clave_caida not in _ya_notificado_v3:
            _ya_notificado_v3.add(clave_caida)
            enviar_discord(
                "DOLAR -- caida desde el maximo semanal",
                f"{SIMBOLO_DOLAR} (proxy del indice dolar)\n"
                f"Maximo de la semana: {maximo_semanal}\n"
                f"Precio actual: {precio_actual}\n"
                f"Caida: {caida_pct}%\n\n"
                f"El dolar debil suele ser favorable para el oro (correlacion inversa).",
                color=0x5DCAA5
            )

        subida_pct = round((precio_actual - maximo_previo) / maximo_previo * 100, 2)
        clave_subida = f"usd_subida_{hoy}_{int(subida_pct)}"
        if precio_actual > maximo_previo and subida_pct >= UMBRAL_SUBIDA_DOLAR and clave_subida not in _ya_notificado_v3:
            _ya_notificado_v3.add(clave_subida)
            enviar_discord(
                "DOLAR -- ruptura del maximo semanal",
                f"{SIMBOLO_DOLAR} (proxy del indice dolar)\n"
                f"Maximo previo de la semana: {maximo_previo}\n"
                f"Precio actual: {precio_actual}\n"
                f"Nueva subida: {subida_pct}%\n\n"
                f"El dolar fuerte suele presionar al oro a la baja (correlacion inversa).",
                color=0xE24B4A
            )
    except Exception as e:
        print(f"[V3] Error Alpaca dolar: {e}")


# --- Correlacion via Alpaca: oro via ETF (GLD), como segunda fuente ---

def _obtener_gld_alpaca():
    if "PON_AQUI" in ALPACA_API_KEY:
        return None, None
    try:
        headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}
        url = f"https://data.alpaca.markets/v2/stocks/{SIMBOLO_ORO_ETF}/snapshot"
        snap = requests.get(url, headers=headers, timeout=10).json()
        precio = snap["latestTrade"]["p"]
        cierre_anterior = snap["prevDailyBar"]["c"]
        cambio_pct = round((precio - cierre_anterior) / cierre_anterior * 100, 2)
        return precio, cambio_pct
    except Exception as e:
        print(f"[V3] Error Alpaca GLD: {e}")
        return None, None


def revisar_estado_oro():
    """Estado del oro combinando Twelve Data (fuente principal, la misma de
    las senales) + Alpaca GLD como segunda referencia. Requiere
    ALPACA_API_KEY/ALPACA_SECRET_KEY; sin ellas, solo muestra Twelve Data."""
    if en_pausa_fin_de_semana():
        return
    try:
        velas = _obtener_velas_cacheadas()
        if not velas:
            return
        precio_actual = velas[-1]["c"]
        tendencia_diaria = _obtener_tendencia_diaria(velas)

        lineas = [
            f"Fuente 1 -- Twelve Data (precio real, mismo dato de las senales):\n"
            f"XAU/USD: {precio_actual} USD por onza troy\n"
            f"Tendencia del dia: {tendencia_diaria or 'sin dato claro'}"
        ]

        precio_gld, cambio_gld = _obtener_gld_alpaca()
        if precio_gld is not None:
            cambio_txt = f" ({'+' if cambio_gld > 0 else ''}{cambio_gld}% hoy)" if cambio_gld is not None else ""
            lineas.append(f"\nFuente 2 -- Alpaca (ETF {SIMBOLO_ORO_ETF}, referencia adicional):\n{precio_gld} USD{cambio_txt}")

        enviar_discord("ORO -- estado (Twelve Data + Alpaca)", "\n".join(lineas), color=0xE8B84B)
    except Exception as e:
        print(f"[V3] Error estado oro: {e}")


# --- Correlacion via Alpaca: liquidez del SPY (spread + volumen) ---

def revisar_liquidez_spy():
    """Avisa cuando el spread bid-ask o el volumen del SPY se disparan muy
    por encima de su media reciente -- señal de que algo se esta moviendo
    en el mercado en general. Requiere ALPACA_API_KEY/ALPACA_SECRET_KEY."""
    if en_pausa_fin_de_semana():
        return
    if "PON_AQUI" in ALPACA_API_KEY:
        return

    url = f"https://data.alpaca.markets/v2/stocks/{SIMBOLO_LIQUIDEZ}/snapshot"
    headers = {"APCA-API-KEY-ID": ALPACA_API_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY}
    try:
        data = requests.get(url, headers=headers, timeout=10).json()
        quote = data["latestQuote"]
        bar = data["minuteBar"]

        spread_actual = round(quote["ap"] - quote["bp"], 4)
        volumen_actual = bar["v"]

        media_spread = statistics.mean(_historial_spread) if _historial_spread else None
        media_volumen = statistics.mean(_historial_volumen) if _historial_volumen else None

        spread_disparado = media_spread and spread_actual > media_spread * UMBRAL_SPREAD
        volumen_disparado = media_volumen and volumen_actual > media_volumen * UMBRAL_VOLUMEN

        if spread_disparado or volumen_disparado:
            detalle = []
            if spread_disparado:
                detalle.append(f"Spread bid-ask: {spread_actual} (media reciente: {round(media_spread, 4)})")
            if volumen_disparado:
                detalle.append(f"Volumen del minuto: {volumen_actual} (media reciente: {round(media_volumen)})")

            enviar_discord(
                "LIQUIDEZ SPY -- movimiento fuera de lo normal",
                f"{SIMBOLO_LIQUIDEZ}\n" + "\n".join(detalle) +
                "\n\nPuede ser una noticia, un movimiento tecnico, o ruido -- revisa el contexto.",
                color=0xEF9F27
            )

        _historial_spread.append(spread_actual)
        _historial_volumen.append(volumen_actual)

    except Exception as e:
        print(f"[V3] Error Alpaca liquidez SPY: {e}")


# =============================================================================
# === FIN INTEGRACION V3 (fusion) ============================================
# =============================================================================


def _resetear_contador_si_cambio_el_dia():
    """El contador de senales de estructura se reinicia solo una vez al
    dia, sincronizado con la medianoche de Madrid."""
    global _contador_senales_hoy, _fecha_contador_senales
    hoy = datetime.now(MADRID_TZ).date()
    if _fecha_contador_senales != hoy:
        _fecha_contador_senales = hoy
        _contador_senales_hoy = 0


# --- Sesiones de mercado (Sidney / Tokio / Londres / Nueva York) ---
# Horario COMPLETO de cada sesion en UTC (no solo el solapamiento) -- entre
# las 4 cubren casi toda la jornada, asi que el bot ya no se salta la mayor
# parte del dia como pasaba solo mirando solapamientos. Sidney cruza la
# medianoche UTC (empieza un dia y termina al siguiente).
SESIONES_HORARIO_UTC = {
    "Sidney": (22, 7),      # 22:00 UTC -> 07:00 UTC del dia siguiente
    "Tokio": (0, 9),        # 00:00 - 09:00 UTC
    "Londres": (7, 16),     # 07:00 - 16:00 UTC
    "Nueva York": (12, 21),  # 12:00 - 21:00 UTC
}
# NOTA: EEUU y Europa cambian de horario de verano/invierno en fechas
# distintas, asi que estas franjas se pueden correr +-1 hora un par de
# semanas al año. Ajusta los numeros si lo notas desalineado. Con estos
# horarios solo queda "muerta" la franja 21:00-22:00 UTC (entre el cierre
# de Nueva York y la apertura de Sidney) -- el lapso mas flojo del dia.

# Si esta en True, el bot solo manda senales de entrada (estructura y
# patrones chartistas) mientras haya AL MENOS UNA sesion abierta -- es
# decir, casi todo el dia salvo esa hora muerta. Si esta en False, manda
# senales a cualquier hora (fuera de fin de semana), sin este filtro.
REQUERIR_SESION_ACTIVA = True


def _sesiones_activas_ahora():
    """Devuelve la lista de sesiones abiertas ahora mismo (puede haber mas
    de una a la vez -- eso es justo un solapamiento de alta liquidez)."""
    hora = datetime.now(timezone.utc).hour
    activas = []
    for nombre, (inicio, fin) in SESIONES_HORARIO_UTC.items():
        if inicio < fin:
            if inicio <= hora < fin:
                activas.append(nombre)
        else:  # la sesion cruza la medianoche UTC (caso de Sidney)
            if hora >= inicio or hora < fin:
                activas.append(nombre)
    return activas


# --- Veredicto del dia por apertura de sesiones ---
# En vez de mirar solo la apertura/cierre de un candle, esto sigue el
# precio contra la apertura de CADA sesion (Tokio, Londres, Nueva York y
# Sidney) a medida que van abriendo durante el dia -- asi el bot va
# "leyendo" como se comporta el precio sesion tras sesion, igual que lo
# haria un trader discrecional siguiendo el dia en vivo, y da un veredicto
# de mayoria (cuantas sesiones ya abiertas quedaron por encima o por debajo
# de su propia apertura).
SESIONES_APERTURA_UTC = [("Tokio", 0), ("Londres", 8), ("Nueva York", 13), ("Sidney", 22)]


def _sesgo_por_apertura_sesiones(velas):
    """Devuelve (detalle, veredicto). 'detalle' es un dict {sesion: sesgo},
    donde sesgo es 'alcista', 'bajista', 'sin cambio' o 'aun no abre hoy'.
    'veredicto' es 'ALCISTA', 'BAJISTA' o 'MIXTO' segun la mayoria de las
    sesiones que ya abrieron hoy (dia UTC)."""
    if not velas:
        return {}, None

    hoy_utc = datetime.now(timezone.utc).date()
    precio_actual = velas[-1]["c"]
    detalle = {}
    votos_alcista = 0
    votos_bajista = 0

    for nombre, hora_inicio in SESIONES_APERTURA_UTC:
        apertura = None
        for v in velas:
            try:
                momento = _parsear_timestamp_utc(v["t"])
            except ValueError:
                continue
            if momento.date() == hoy_utc and momento.hour >= hora_inicio:
                apertura = v["o"]
                break

        if apertura is None:
            detalle[nombre] = "aun no abre hoy"
            continue

        if precio_actual > apertura:
            detalle[nombre] = "alcista"
            votos_alcista += 1
        elif precio_actual < apertura:
            detalle[nombre] = "bajista"
            votos_bajista += 1
        else:
            detalle[nombre] = "sin cambio"

    if votos_alcista > votos_bajista:
        veredicto = "ALCISTA"
    elif votos_bajista > votos_alcista:
        veredicto = "BAJISTA"
    else:
        veredicto = "MIXTO"  # empate, o ninguna sesion con datos todavia

    return detalle, veredicto


def _texto_veredicto_sesiones(detalle, veredicto):
    lineas = [f"{nombre}: {sesgo}" for nombre, sesgo in detalle.items()]
    return f"Veredicto del dia: {veredicto} ({' | '.join(lineas)})"


# Multiplicador sobre el promedio/ATR que debe superar la vela actual para
# considerarse que hay "empuje real" (liquidez/volumen) detras del movimiento
MULTIPLICADOR_LIQUIDEZ_VOLUMEN = 1.1


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


# --- Historial de senales + seguimiento automatico de resultados ---
# Cada senal de estructura (BOS/CHoCH) o patron que se manda queda registrada
# en un CSV local con un id unico y resultado="PENDIENTE". Mientras la senal
# sigue abierta, en cada revision (cada 5 minutos) se comparan las velas
# nuevas contra el Stop Loss y el Take Profit para saber si ya se resolvio.
# Si no toca ninguno de los dos en un tiempo razonable, se marca TIMEOUT.
# Esto es lo primero que revisa cualquier trader sistematico antes de confiar
# en un algoritmo: saber de verdad cuantas senales ganan y cuantas pierden.
ARCHIVO_HISTORIAL = os.environ.get("ARCHIVO_HISTORIAL", "historial_senales.csv")
ARCHIVO_SENALES_ABIERTAS = os.environ.get("ARCHIVO_SENALES_ABIERTAS", "senales_abiertas.json")
CAMPOS_HISTORIAL = ["id", "hora_madrid", "tipo_evento", "direccion", "entry",
                     "stop_loss", "take_profit", "rsi", "extra", "resultado"]

# Cuantas horas se espera a que una senal toque TP o SL antes de darla por
# expirada (TIMEOUT). XAU/USD en 15min puede tardar en desarrollarse, asi
# que se deja un margen amplio -- ajustable segun lo que observes en la practica.
TIMEOUT_HORAS_SEGUIMIENTO = 72

# Estado en memoria (y en disco, via ARCHIVO_SENALES_ABIERTAS) de las senales
# que todavia no tocaron ni TP ni SL. Cada una: id, direccion, stop_loss,
# take_profit, abierta_en (ISO UTC), ultima_vela_revisada (timestamp de la
# API, para no re-revisar las mismas velas en cada ciclo).
_senales_abiertas = []
_siguiente_id_senal = 1


def _cargar_senales_abiertas():
    """Recupera las senales abiertas al arrancar el bot, para que un reinicio
    del contenedor (Northflank) no pierda el seguimiento en curso."""
    global _senales_abiertas, _siguiente_id_senal
    try:
        if os.path.isfile(ARCHIVO_SENALES_ABIERTAS):
            with open(ARCHIVO_SENALES_ABIERTAS, "r", encoding="utf-8") as f:
                datos = json.load(f)
                _senales_abiertas = datos.get("abiertas", [])
                _siguiente_id_senal = datos.get("siguiente_id", 1)
    except Exception as e:
        print(f"No se pudo cargar el estado de senales abiertas: {e}")


def _guardar_senales_abiertas():
    try:
        with open(ARCHIVO_SENALES_ABIERTAS, "w", encoding="utf-8") as f:
            json.dump({"abiertas": _senales_abiertas, "siguiente_id": _siguiente_id_senal}, f)
    except Exception as e:
        print(f"No se pudo guardar el estado de senales abiertas: {e}")


def _registrar_senal_historial(id_senal, tipo_evento, direccion, entry, stop_loss, take_profit,
                                rsi, extra="", resultado="PENDIENTE"):
    """Anade una linea al CSV de historial (con cabecera si no existia).
    Cualquier error aqui se ignora -- no debe tumbar el envio de la senal a
    Discord por un problema de disco."""
    try:
        existe = os.path.isfile(ARCHIVO_HISTORIAL)
        with open(ARCHIVO_HISTORIAL, "a", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            if not existe:
                escritor.writerow(CAMPOS_HISTORIAL)
            escritor.writerow([id_senal, hora_madrid(), tipo_evento, direccion, entry,
                                stop_loss, take_profit, rsi, extra, resultado])
    except Exception as e:
        print(f"No se pudo escribir en el historial de senales: {e}")


def _actualizar_resultado_historial(id_senal, resultado):
    """Reescribe la fila del historial que corresponde a id_senal con el
    resultado final (WIN/LOSS/TIMEOUT), una vez que la senal se resuelve."""
    try:
        if not os.path.isfile(ARCHIVO_HISTORIAL):
            return
        with open(ARCHIVO_HISTORIAL, "r", newline="", encoding="utf-8") as f:
            filas = list(csv.reader(f))
        if not filas:
            return
        cabecera, resto = filas[0], filas[1:]
        try:
            idx_id = cabecera.index("id")
            idx_resultado = cabecera.index("resultado")
        except ValueError:
            print("El historial tiene una cabecera antigua sin columna 'id'/'resultado' -- no se puede actualizar.")
            return
        for fila in resto:
            if len(fila) > idx_id and fila[idx_id] == str(id_senal):
                fila[idx_resultado] = resultado
                break
        with open(ARCHIVO_HISTORIAL, "w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow(cabecera)
            escritor.writerows(resto)
    except Exception as e:
        print(f"No se pudo actualizar el resultado en el historial (senal #{id_senal}): {e}")


def _abrir_seguimiento_senal(direccion, entry, stop_loss, take_profit, ultima_vela_ts):
    """Registra una senal nueva como 'abierta' para que _seguir_senales_abiertas
    la vaya revisando en cada ciclo. Devuelve el id asignado."""
    global _siguiente_id_senal
    id_senal = _siguiente_id_senal
    _siguiente_id_senal += 1
    _senales_abiertas.append({
        "id": id_senal,
        "direccion": direccion,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "abierta_en": datetime.now(timezone.utc).isoformat(),
        "ultima_vela_revisada": ultima_vela_ts,
    })
    _guardar_senales_abiertas()
    return id_senal


def _seguir_senales_abiertas(velas):
    """En cada revision, compara las senales todavia abiertas contra las
    velas nuevas (desde la ultima vez que se revisaron) para ver si el
    precio ya toco el Take Profit o el Stop Loss. Si pasa demasiado tiempo
    sin tocar ninguno, la marca como TIMEOUT. No manda nada a Discord --
    solo actualiza el CSV de historial en silencio."""
    global _senales_abiertas
    if not _senales_abiertas:
        return

    ahora_utc = datetime.now(timezone.utc)
    marcas = [v["t"] for v in velas]
    huerfanas = []  # senales cuya ultima vela revisada ya no esta en el rango pedido

    senales_restantes = []
    for senal in _senales_abiertas:
        resultado = None

        try:
            idx_desde = marcas.index(senal["ultima_vela_revisada"]) + 1
        except ValueError:
            # La vela de referencia ya no esta en el rango de NUM_VELAS pedido
            # (senal muy vieja) -- revisamos desde la primera vela disponible.
            idx_desde = 0
            huerfanas.append(senal["id"])

        for v in velas[idx_desde:]:
            if senal["direccion"] == "alcista":
                toco_sl = v["l"] <= senal["stop_loss"]
                toco_tp = v["h"] >= senal["take_profit"]
            else:
                toco_sl = v["h"] >= senal["stop_loss"]
                toco_tp = v["l"] <= senal["take_profit"]

            # Si la misma vela toca ambos niveles, no se puede saber cual paso
            # primero con velas de 15min -- se asume el peor caso (SL primero),
            # como haria cualquier trader conservador revisando el historial.
            if toco_sl:
                resultado = "LOSS"
            elif toco_tp:
                resultado = "WIN"

            senal["ultima_vela_revisada"] = v["t"]
            if resultado:
                break

        if resultado is None:
            abierta_desde = datetime.fromisoformat(senal["abierta_en"])
            if (ahora_utc - abierta_desde) > timedelta(hours=TIMEOUT_HORAS_SEGUIMIENTO):
                resultado = "TIMEOUT"

        if resultado:
            _actualizar_resultado_historial(senal["id"], resultado)
            print(f"Senal #{senal['id']} ({senal['direccion']}) resuelta: {resultado}")
        else:
            senales_restantes.append(senal)

    if huerfanas:
        print(f"Senales seguidas desde la primera vela disponible (referencia antigua fuera de rango): {huerfanas}")

    _senales_abiertas = senales_restantes
    _guardar_senales_abiertas()


# --- Estadisticas historicas: metricas agregadas sobre el historial ya
# resuelto (WIN/LOSS/TIMEOUT), consultables con el comando de texto !stats
# en el canal de Discord. No se recalculan solas ni se mandan solas -- solo
# cuando alguien las pide. ---

def _calcular_estadisticas_historial():
    """Lee historial_senales.csv y calcula metricas agregadas: cuantas
    senales se han mandado, cuantas se resolvieron, el porcentaje de
    acierto, el Profit Factor y el drawdown maximo estimado.

    Profit Factor y drawdown se calculan en multiplos de riesgo (R), no en
    dinero real, porque el bot no conoce el tamano de posicion de cada
    quien opera: cada perdida cuesta 1R (el riesgo hasta el Stop Loss) y
    cada ganancia aporta su propio ratio recompensa:riesgo (la distancia
    hasta el Take Profit dividida entre la distancia hasta el Stop Loss).
    Devuelve None si el archivo no existe o tiene el formato antiguo (sin
    columna 'resultado')."""
    if not os.path.isfile(ARCHIVO_HISTORIAL):
        return None

    total = 0
    wins = 0
    losses = 0
    timeouts = 0
    pendientes = 0
    suma_ganancias = 0.0
    suma_perdidas = 0.0
    curva_r = []  # equity acumulada en R, en el orden en que aparecen en el CSV

    with open(ARCHIVO_HISTORIAL, "r", newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        if not lector.fieldnames or "resultado" not in lector.fieldnames:
            return None

        equity = 0.0
        for fila in lector:
            total += 1
            resultado = fila.get("resultado", "PENDIENTE")

            try:
                entry = float(fila["entry"])
                stop_loss = float(fila["stop_loss"])
                take_profit = float(fila["take_profit"])
            except (KeyError, ValueError, TypeError):
                continue

            riesgo = abs(entry - stop_loss)
            recompensa = abs(take_profit - entry)

            if resultado == "WIN":
                wins += 1
                suma_ganancias += recompensa
                if riesgo > 0:
                    equity += recompensa / riesgo
                curva_r.append(equity)
            elif resultado == "LOSS":
                losses += 1
                suma_perdidas += riesgo
                equity -= 1
                curva_r.append(equity)
            elif resultado == "TIMEOUT":
                timeouts += 1
            else:
                pendientes += 1

    resueltas = wins + losses
    win_rate = (wins / resueltas * 100) if resueltas else None
    profit_factor = (suma_ganancias / suma_perdidas) if suma_perdidas > 0 else None

    # Drawdown maximo: la mayor caida desde un pico de la curva de equity
    # (en R) hasta el punto mas bajo visto despues de ese pico.
    drawdown_maximo_r = 0.0
    pico = 0.0
    for valor in curva_r:
        pico = max(pico, valor)
        drawdown_maximo_r = max(drawdown_maximo_r, pico - valor)

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "timeouts": timeouts,
        "pendientes": pendientes,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "drawdown_maximo_r": drawdown_maximo_r,
    }


def generar_reporte_estadisticas():
    """Arma el embed que se manda como respuesta al comando !stats."""
    stats = _calcular_estadisticas_historial()

    if stats is None:
        return discord.Embed(
            title="Todavia no hay historial utilizable",
            description=(
                "No se encontro historial_senales.csv, o tiene un formato "
                "antiguo sin la columna 'resultado'. En cuanto se mande y se "
                "resuelva alguna senal nueva, las estadisticas apareceran aqui."
            ),
            color=0xEF9F27
        )

    if stats["total"] == 0:
        return discord.Embed(
            title="Todavia no hay senales registradas",
            description="En cuanto se mande la primera senal, aparecera aqui.",
            color=0xEF9F27
        )

    partes = [
        f"Senales enviadas: {stats['total']}",
        f"Resueltas: {stats['wins'] + stats['losses']} (WIN: {stats['wins']} / LOSS: {stats['losses']})",
        f"Pendientes: {stats['pendientes']} | Timeout: {stats['timeouts']}",
    ]

    if stats["win_rate"] is not None:
        partes.append(f"Porcentaje de acierto: {round(stats['win_rate'], 1)}%")
    else:
        partes.append("Porcentaje de acierto: sin senales resueltas todavia")

    if stats["profit_factor"] is not None:
        partes.append(f"Profit Factor: {round(stats['profit_factor'], 2)}")
    else:
        partes.append("Profit Factor: sin perdidas registradas todavia (no se puede calcular)")

    partes.append(f"Drawdown maximo estimado: {round(stats['drawdown_maximo_r'], 2)}R")

    embed = discord.Embed(
        title="Estadisticas del sistema",
        description="\n".join(partes),
        color=0x5DCAA5
    )
    embed.set_footer(text=f"Hora Madrid: {hora_madrid()}")
    return embed


# --- Cliente de Discord (bot de verdad, no un webhook) ---
intents = discord.Intents.default()
intents.message_content = True  # necesario para leer comandos de texto como !stats
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

    if not _dentro_de_horario_operativo():  # [V3 -- agregado]
        print(f"Fuera del horario operativo ({HORA_INICIO_OPERATIVA}-{HORA_FIN_OPERATIVA} Madrid) -- se salta revisar_senal().")
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

        # Seguimiento de resultados: se revisa en cada ciclo (haya o no vela
        # nueva para una senal de estructura), para no perder ninguna vela
        # nueva en la comparacion contra TP/SL de las senales abiertas.
        _seguir_senales_abiertas(velas)

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

        # Ventana de sesion: solo se mandan senales de entrada mientras haya
        # al menos una sesion abierta (Sidney/Tokio/Londres/Nueva York) --
        # entre las 4 cubren casi todo el dia, solo queda fuera la hora
        # muerta entre el cierre de NY y la apertura de Sidney.
        sesiones_activas = _sesiones_activas_ahora()
        fuera_de_ventana = REQUERIR_SESION_ACTIVA and not sesiones_activas
        etiqueta_sesion = (", ".join(sesiones_activas) + (" (solapamiento, alta liquidez)" if len(sesiones_activas) > 1 else "")) if sesiones_activas else "ninguna (hora muerta)"

        # Veredicto del dia por apertura de sesiones (Tokio/Londres/NY/Sidney)
        detalle_sesiones, veredicto_sesiones = _sesgo_por_apertura_sesiones(velas)
        texto_veredicto = _texto_veredicto_sesiones(detalle_sesiones, veredicto_sesiones)
        print(texto_veredicto)

        # Confirmacion de liquidez/volumen sobre la vela que dispara la senal
        # (misma vela para patrones y estructura en este ciclo de revision)
        confirma_liquidez, texto_liquidez = _confirma_liquidez_y_volumen(velas, atr_actual)

        no_enviar_entradas = en_blackout or fuera_de_ventana or not confirma_liquidez
        if fuera_de_ventana:
            print("Ninguna sesion abierta ahora mismo (hora muerta NY-Sidney) -- no se mandan entradas.")
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

            # [V3 -- agregado] Score de confianza + multi-timeframe. No cambia
            # si la senal se manda o no -- solo etiqueta la calidad.
            etiqueta_calidad_patron, score_patron, detalle_mtf_patron = _etiqueta_calidad_y_score(
                patron["direccion"],
                [
                    ("Patron chartista confirmado", True, 30),
                    ("RSI de reversion confirmado", True, 20),
                    ("Tendencia diaria a favor", True, 15),
                    ("Liquidez/volumen confirmado", confirma_liquidez, 15),
                    ("Sesion activa", not fuera_de_ventana, 10),
                ]
            )
            print(f"Patron {patron['nombre']} confirmado ({tipo_senal_patron}, {etiqueta_calidad_patron} "
                  f"{score_patron}/100) -- mandando senal limpia a Discord.")
            enviar_discord(
                f"{tipo_senal_patron} {etiqueta_calidad_patron} ({score_patron}/100)",
                f"Entrada: {patron['entry']}\n"
                f"Stop loss: {patron['stop_loss']}\n"
                f"Take Profit: {patron['take_profit']}",
                color=color_patron
            )
            id_senal_patron = _abrir_seguimiento_senal(
                patron["direccion"], patron["entry"], patron["stop_loss"], patron["take_profit"], velas[-1]["t"]
            )
            _registrar_senal_historial(
                id_senal_patron, patron["nombre"], patron["direccion"], patron["entry"],
                patron["stop_loss"], patron["take_profit"], rsi_actual, extra=f"patron chartista, score={score_patron}"
            )

        # [V3 -- agregado] Bandera/Banderin: patrones de CONTINUACION (no de
        # reversion), por eso usan la banda de RSI de impulso sano (la misma
        # banda ya calibrada para BOS/CHoCH: 45-80 alcista, 20-55 bajista)
        # en vez de la de sobrecompra/sobreventa que usa el loop de arriba.
        for patron_cont in ([] if no_enviar_entradas else _detectar_banderas_banderines(velas)):
            if rsi_actual is None:
                rsi_confirma_cont = True
            elif patron_cont["direccion"] == "alcista":
                rsi_confirma_cont = 45 <= rsi_actual < 80
            else:
                rsi_confirma_cont = 20 < rsi_actual <= 55

            if not rsi_confirma_cont:
                print(f"[V3] {patron_cont['nombre']} detectado, pero el RSI ({rsi_actual}) no confirma impulso sano -- no se manda.")
                continue

            tipo_senal_cont = "BUY" if patron_cont["direccion"] == "alcista" else "SELL"
            color_cont = 0x5DCAA5 if patron_cont["direccion"] == "alcista" else 0xE24B4A

            etiqueta_calidad_cont, score_cont, _detalle_mtf_cont = _etiqueta_calidad_y_score(
                patron_cont["direccion"],
                [
                    ("Patron de continuacion confirmado", True, 30),
                    ("RSI de impulso sano", rsi_confirma_cont, 20),
                    ("Tendencia diaria a favor", True, 15),
                    ("Liquidez/volumen confirmado", confirma_liquidez, 15),
                    ("Sesion activa", not fuera_de_ventana, 10),
                ]
            )
            print(f"[V3] {patron_cont['nombre']} confirmado ({tipo_senal_cont}, {etiqueta_calidad_cont} "
                  f"{score_cont}/100) -- mandando senal limpia a Discord.")
            enviar_discord(
                f"{tipo_senal_cont} {etiqueta_calidad_cont} ({score_cont}/100)",
                f"Entrada: {patron_cont['entry']}\n"
                f"Stop loss: {patron_cont['stop_loss']}\n"
                f"Take Profit: {patron_cont['take_profit']}",
                color=color_cont
            )
            id_senal_cont = _abrir_seguimiento_senal(
                patron_cont["direccion"], patron_cont["entry"], patron_cont["stop_loss"],
                patron_cont["take_profit"], velas[-1]["t"]
            )
            _registrar_senal_historial(
                id_senal_cont, patron_cont["nombre"], patron_cont["direccion"], patron_cont["entry"],
                patron_cont["stop_loss"], patron_cont["take_profit"], rsi_actual,
                extra=f"patron de continuacion, score={score_cont}"
            )

        # [V3 -- agregado] Barrido de liquidez (sweep): el precio supera una
        # zona EQH/EQL conocida y revierte -- patron clasico de caza de stops
        # antes de un giro. Independiente del BOS/CHoCH y de los patrones de
        # arriba.
        eqh_v3, eql_v3 = _detectar_liquidez(swings)
        barrido = None if no_enviar_entradas else _detectar_barrido_liquidez(velas, eqh_v3, eql_v3)
        if barrido:
            tipo_senal_barrido = "BUY" if barrido["direccion"] == "alcista" else "SELL"
            color_barrido = 0x5DCAA5 if barrido["direccion"] == "alcista" else 0xE24B4A
            riesgo_barrido = abs(barrido["entry"] - barrido["stop_loss"])
            take_profit_barrido = round(
                barrido["entry"] + riesgo_barrido * RATIO_RIESGO_BENEFICIO_RESPALDO
                if barrido["direccion"] == "alcista"
                else barrido["entry"] - riesgo_barrido * RATIO_RIESGO_BENEFICIO_RESPALDO, 2
            )
            etiqueta_calidad_barrido, score_barrido, _detalle_mtf_barrido = _etiqueta_calidad_y_score(
                barrido["direccion"],
                [
                    ("Barrido de liquidez confirmado", True, 30),
                    ("Tendencia diaria a favor", True, 15),
                    ("Liquidez/volumen confirmado", confirma_liquidez, 15),
                    ("Sesion activa", not fuera_de_ventana, 10),
                ]
            )
            print(f"[V3] Barrido de liquidez {barrido['direccion']} confirmado ({tipo_senal_barrido}, "
                  f"{etiqueta_calidad_barrido} {score_barrido}/100) -- mandando senal limpia a Discord.")
            enviar_discord(
                f"{tipo_senal_barrido} {etiqueta_calidad_barrido} ({score_barrido}/100) -- barrido de liquidez",
                f"Entrada: {barrido['entry']}\n"
                f"Stop loss: {barrido['stop_loss']}\n"
                f"Take Profit: {take_profit_barrido}",
                color=color_barrido
            )
            id_senal_barrido = _abrir_seguimiento_senal(
                barrido["direccion"], barrido["entry"], barrido["stop_loss"], take_profit_barrido, velas[-1]["t"]
            )
            _registrar_senal_historial(
                id_senal_barrido, "Barrido de liquidez", barrido["direccion"], barrido["entry"],
                barrido["stop_loss"], take_profit_barrido, rsi_actual, extra=f"score={score_barrido}"
            )

        patron_geometrico = _detectar_triangulos_cunas(swings)
        if patron_geometrico:
            # Aviso de CONTEXTO sin Entry/SL/TP -- se queda solo interno
            # (print), no se manda a Discord, porque no es una senal operable.
            print(f"Patron chartista de contexto formandose: {patron_geometrico['nombre']} "
                  f"(sesgo {patron_geometrico['sesgo']}) -- no se manda a Discord, no trae Entry/SL/TP.")

        evento = _detectar_evento_estructura(velas, swings)

        if evento is None:
            return  # sin cambio de estructura en esta vela, no hay nada mas que avisar

        if no_enviar_entradas:
            razon = ("blackout por noticias" if en_blackout else
                      "ninguna sesion abierta ahora mismo (hora muerta)" if fuera_de_ventana else
                      f"liquidez/volumen insuficiente ({texto_liquidez})")
            print(f"Senal XAU/USD: {evento['tipo']} {evento['direccion']} detectado, pero {razon} -- no se manda.")
            return

        if _contador_senales_hoy >= MAX_SENALES_ESTRUCTURA_POR_DIA:
            print(f"Senal XAU/USD: {evento['tipo']} {evento['direccion']} detectado, pero ya se "
                  f"alcanzo el limite de {MAX_SENALES_ESTRUCTURA_POR_DIA} senales de estructura hoy -- no se manda.")
            return

        # Filtro de tendencia: el veredicto por apertura de sesiones
        # (Tokio/Londres/Nueva York/Sidney) manda; si todavia esta MIXTO
        # (pocas sesiones abiertas o empate), se usa la EMA20 diaria como
        # respaldo en vez de bloquear la senal sin ningun criterio.
        if veredicto_sesiones == "ALCISTA":
            tendencia_diaria = "alcista"
        elif veredicto_sesiones == "BAJISTA":
            tendencia_diaria = "bajista"
        else:
            tendencia_diaria = _obtener_tendencia_diaria(velas)

        va_contra_el_dia = tendencia_diaria is not None and tendencia_diaria != evento["direccion"]

        if va_contra_el_dia and evento["tipo"] != "CHoCH":
            # Un BOS en contra del veredicto del dia no es el tipo de aviso
            # que interesa (un BOS por definicion sigue una tendencia de
            # estructura, no marca un giro) -- se sigue bloqueando igual
            # que antes.
            print(
                f"Senal XAU/USD: {evento['tipo']} {evento['direccion']} detectado, "
                f"pero el veredicto del dia es {tendencia_diaria} -- no se manda (va en contra del dia). {texto_veredicto}"
            )
            return

        # Si es CHoCH contra el dia, se deja pasar -- se manda igual, pero
        # mas abajo se etiqueta claramente como "contra-tendencia" en vez
        # de mandarlo como una senal BUY/SELL normal.
        contra_tendencia_choch = va_contra_el_dia and evento["tipo"] == "CHoCH"

        # Filtro de RSI: antes exigia una banda estrecha (50-70 para BUY,
        # 30-50 para SELL) que descartaba impulsos fuertes -- una vela muy
        # pronunciada en la ruptura empuja el RSI mas alla de 70 (o por
        # debajo de 30) justo quando esta pasando lo mas interesante, y esa
        # senal se perdia. Ahora se amplia el margen (45-80 para BUY,
        # 20-55 para SELL) para dejar pasar impulsos fuertes, pero se sigue
        # bloqueando lo verdaderamente plano (RSI muy cerca de 50 sin
        # impulso real) y lo verdaderamente agotado (RSI extremo >80 o <20,
        # donde ya es mas probable un retroceso que una continuacion).
        if rsi_actual is not None:
            if evento["direccion"] == "alcista":
                rsi_confirma = 45 <= rsi_actual < 80
            else:
                rsi_confirma = 20 < rsi_actual <= 55

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

        # NOTA: FVG, ATR, sesiones, veredicto del dia y RSI se siguen
        # calculando y filtrando por dentro (ver arriba), solo que ya no se
        # incluyen en el texto que se manda a Discord -- se deja el mensaje
        # limpio con solo lo operable.
        if contra_tendencia_choch:
            # Segundo tipo de aviso: CHoCH en contra del veredicto del dia --
            # se etiqueta claramente distinto a una senal BUY/SELL normal,
            # porque es de mayor riesgo (posible giro, no confirmado por la
            # tendencia general del dia).
            etiqueta_calidad_estructura, score_estructura, detalle_mtf_estructura = _etiqueta_calidad_y_score(
                evento["direccion"],
                [
                    (f"{evento['tipo']} confirmado", True, 25),
                    ("RSI favorable", True, 20),
                    ("Liquidez/volumen confirmado", confirma_liquidez, 10),
                    ("Sesion activa", not fuera_de_ventana, 10),
                ]
            )
            titulo_aviso = f"CHoCH {evento['direccion'].upper()} (contra-tendencia del dia) -- {etiqueta_calidad_estructura} ({score_estructura}/100)"
            print(f"CHoCH {evento['direccion']} contra la tendencia del dia -- mandando aviso "
                  f"etiquetado (senal {_contador_senales_hoy + 1} de {MAX_SENALES_ESTRUCTURA_POR_DIA} hoy).")
        else:
            etiqueta_calidad_estructura, score_estructura, detalle_mtf_estructura = _etiqueta_calidad_y_score(
                evento["direccion"],
                [
                    (f"{evento['tipo']} confirmado", True, 25),
                    ("RSI favorable", True, 20),
                    ("Tendencia diaria a favor (EMA20/sesiones)", True, 15),
                    ("FVG alineado", bool(fvgs), 10),
                    ("Liquidez/volumen confirmado", confirma_liquidez, 10),
                    ("Sesion activa", not fuera_de_ventana, 10),
                ]
            )
            titulo_aviso = f"{tipo_senal} {etiqueta_calidad_estructura} ({score_estructura}/100)"
            print(f"Senal {evento['tipo']} {evento['direccion']} confirmada -- mandando senal limpia a Discord "
                  f"(senal {_contador_senales_hoy + 1} de {MAX_SENALES_ESTRUCTURA_POR_DIA} hoy).")

        enviar_discord(
            titulo_aviso,
            f"Entrada: {precio_actual}\n"
            f"Stop loss: {stop_loss}\n"
            f"Take Profit: {take_profit}",
            color=color
        )

        _contador_senales_hoy += 1
        id_senal_estructura = _abrir_seguimiento_senal(
            evento["direccion"], precio_actual, stop_loss, take_profit, velas[-1]["t"]
        )
        _registrar_senal_historial(
            id_senal_estructura, evento["tipo"], evento["direccion"], precio_actual, stop_loss, take_profit,
            rsi_actual, extra=f"ATR={atr_actual}, score={score_estructura}"
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
    ningun estado interno (no interfiere con las alertas automaticas).

    El calculo de RSI, ATR, tendencia, sesiones, liquidez y FVG se sigue
    haciendo por dentro igual que siempre (para decidir si hay o no sesgo
    claro), pero el mensaje que se manda a Discord se deja reducido a solo
    BUY/SELL + Entrada/Stop loss/Take Profit, igual que las senales
    automaticas."""
    if en_pausa_fin_de_semana():
        return discord.Embed(
            title="El mercado esta cerrado (fin de semana)",
            description=(
                "XAU/USD no opera de viernes en la noche a domingo en la noche "
                "(hora Madrid). El bot vuelve a revisar solo apenas reabra el mercado."
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
        serie_atr = _calcular_serie_atr(velas)
        atr_actual = serie_atr[-1]
        precio_actual = velas[-1]["c"]

        highs = [s for s in swings if s[1] == "high"]
        lows = [s for s in swings if s[1] == "low"]
        ultimo_high = highs[-1][2] if highs else None
        ultimo_low = lows[-1][2] if lows else None

        eqh, eql = _detectar_liquidez(swings)
        colchon = (MULTIPLICADOR_ATR_SL * atr_actual) if atr_actual else None

        if ultimo_high and precio_actual > ultimo_high:
            tipo_senal = "BUY"
            color = 0x5DCAA5
            entrada = precio_actual
            if ultimo_low:
                stop_loss = round(ultimo_low - colchon, 2) if colchon else round(ultimo_low * 0.999, 2)
            else:
                stop_loss = round(precio_actual - colchon, 2) if colchon else round(precio_actual * 0.995, 2)
            objetivos = sorted([n for n in eqh if n > precio_actual])
            take_profit = objetivos[0] if objetivos else round(entrada + (entrada - stop_loss) * RATIO_RIESGO_BENEFICIO_RESPALDO, 2)

        elif ultimo_low and precio_actual < ultimo_low:
            tipo_senal = "SELL"
            color = 0xE24B4A
            entrada = precio_actual
            if ultimo_high:
                stop_loss = round(ultimo_high + colchon, 2) if colchon else round(ultimo_high * 1.001, 2)
            else:
                stop_loss = round(precio_actual + colchon, 2) if colchon else round(precio_actual * 1.005, 2)
            objetivos = sorted([n for n in eql if n < precio_actual], reverse=True)
            take_profit = objetivos[0] if objetivos else round(entrada - (stop_loss - entrada) * RATIO_RIESGO_BENEFICIO_RESPALDO, 2)

        else:
            return discord.Embed(
                title="Sin senal clara ahora mismo",
                description="El precio esta dentro del rango, sin ruptura confirmada.",
                color=0xEF9F27
            )

        embed = discord.Embed(
            title=tipo_senal,
            description=(
                f"Entrada: {entrada}\n"
                f"Stop loss: {stop_loss}\n"
                f"Take Profit: {take_profit}"
            ),
            color=color
        )
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


# [V3 -- agregado] Tareas periodicas de correlacion via Alpaca. Cada una ya
# se auto-desactiva por dentro si ALPACA_API_KEY/ALPACA_SECRET_KEY no estan
# configuradas (no rompen nada si no se usan).
@tasks.loop(minutes=30)
async def revisar_dolar_periodicamente():
    await asyncio.to_thread(revisar_dolar_maximo_semanal)


@tasks.loop(minutes=INTERVALO_ORO_MINUTOS)
async def revisar_estado_oro_periodicamente():
    await asyncio.to_thread(revisar_estado_oro)


@tasks.loop(minutes=2)
async def revisar_liquidez_spy_periodicamente():
    await asyncio.to_thread(revisar_liquidez_spy)


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

    # [V3 -- agregado] Arranca las tareas de correlacion junto a la principal.
    for tarea_v3 in (revisar_dolar_periodicamente, revisar_estado_oro_periodicamente,
                      revisar_liquidez_spy_periodicamente):
        if not tarea_v3.is_running():
            tarea_v3.start()


@client.event
async def on_message(message):
    # Ignorar los propios mensajes del bot (y los de otros bots) para no
    # entrar en bucle.
    if message.author.bot:
        return

    contenido = message.content.strip().lower()
    if contenido not in ("!stats", "!estadisticas"):
        return

    try:
        embed = await asyncio.to_thread(generar_reporte_estadisticas)
        await message.channel.send(embed=embed)
    except Exception as e:
        print(f"Error generando/enviando las estadisticas ({e})")
        try:
            await message.channel.send(content=f"Hubo un error generando las estadisticas: {e}")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# PROGRAMACION
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _cargar_senales_abiertas()
    threading.Thread(target=iniciar_servidor_web, daemon=True).start()
    client.run(DISCORD_BOT_TOKEN)
