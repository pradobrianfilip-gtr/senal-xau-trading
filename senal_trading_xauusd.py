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

De donde salen los datos:
  - Twelve Data (proveedor de datos de mercado, no un broker) via su API
    REST. Da velas reales (Open/High/Low/Close) del simbolo XAU/USD, no
    precios sueltos -- mucho mas preciso que aproximar velas a partir de
    un precio muestreado cada 2 minutos. Plan gratis: 800 consultas al dia
    (el bot usa muchas menos que eso).

Filtro de tendencia diaria:
  Antes de avisar una senal en las velas de 15 minutos, el bot revisa la
  vela DIARIA actual (compara su cierre contra su apertura). Si el dia esta
  alcista, solo avisa senales BUY; si el dia esta bajista, solo avisa
  senales SELL. Las senales de 15 min que van en contra del dia se
  calculan igual por dentro (para no perder el hilo de la estructura), pero
  NO se mandan a Discord -- asi solo te llegan las entradas que van a favor
  de la tendencia grande, como se busca la entrada de forma profesional.

Como conseguir la API key (gratis, sin tarjeta, funciona desde Espana):
  1. Ve a https://twelvedata.com y crea una cuenta gratis (solo pide correo)
  2. Tu API key aparece en el panel principal (dashboard) apenas te registras
  3. Pon esa key en la variable de entorno TWELVE_DATA_API_KEY

IMPORTANTE -- esto no es asesoria financiera:
  BOS, CHoCH, EQH y FVG son patrones de analisis tecnico (price action /
  "smart money concepts"). Son herramientas de lectura del grafico, no
  garantias. Esta senal es automatica, basada en reglas fijas, y puede
  fallar como cualquier metodo tecnico. Este bot NO ejecuta ninguna orden
  -- solo avisa. La decision de entrar o no es tuya, revisando el grafico.

Requisitos:
    pip install requests apscheduler

Configuracion (variables de entorno):
    DISCORD_WEBHOOK_SENALES -> URL del webhook de Discord (canal aparte del
                                 de noticias) donde quieres recibir las senales
    TWELVE_DATA_API_KEY     -> API key gratis de twelvedata.com (ver arriba)
"""

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.blocking import BlockingScheduler

# ---------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------

DISCORD_WEBHOOK_SENALES = os.environ.get("DISCORD_WEBHOOK_SENALES", "PON_AQUI_TU_WEBHOOK")
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "PON_AQUI_TU_API_KEY")

TWELVE_DATA_URL = "https://api.twelvedata.com/time_series"
SIMBOLO = "XAU/USD"

MADRID_TZ = ZoneInfo("Europe/Madrid")

# Cada cuantos minutos revisamos la estructura
INTERVALO_REVISION_MINUTOS = 5

# Granularidad de las velas que pedimos a Twelve Data (15min = velas de 15 minutos)
GRANULARIDAD = "15min"
NUM_VELAS = 200  # cuantas velas pedimos cada vez (suficiente historial)

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


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def hora_madrid():
    return datetime.now(MADRID_TZ).strftime("%d/%m/%Y %H:%M:%S")


def enviar_discord(titulo, descripcion, color=0xF5A623):
    if "PON_AQUI" in DISCORD_WEBHOOK_SENALES:
        print(f"[SIN CONFIGURAR] {titulo}: {descripcion}")
        return
    payload = {
        "embeds": [{
            "title": titulo,
            "description": descripcion,
            "color": color,
            "footer": {"text": f"Hora Madrid: {hora_madrid()}"}
        }]
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_SENALES, json=payload, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Error enviando a Discord: {e}")


# ---------------------------------------------------------------------------
# DATOS: velas reales de Twelve Data
# ---------------------------------------------------------------------------

def _obtener_velas():
    """Pide velas reales (OHLC) de XAU/USD a Twelve Data. Devuelve la lista
    en orden CRONOLOGICO (la mas vieja primero, la mas reciente al final),
    que es como el resto del codigo espera los datos."""
    params = {
        "symbol": SIMBOLO,
        "interval": GRANULARIDAD,
        "outputsize": NUM_VELAS,
        "apikey": TWELVE_DATA_API_KEY,
    }
    r = requests.get(TWELVE_DATA_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    if data.get("status") == "error":
        raise RuntimeError(f"Twelve Data error: {data.get('message')}")

    velas = []
    for v in data.get("values", []):
        velas.append({
            "t": v["datetime"],
            "o": float(v["open"]),
            "h": float(v["high"]),
            "l": float(v["low"]),
            "c": float(v["close"]),
        })
    velas.reverse()  # Twelve Data manda lo mas reciente primero, lo invertimos
    return velas


def _obtener_tendencia_diaria():
    """Consulta la vela DIARIA actual de XAU/USD (la de hoy, aunque siga
    formandose) y determina si el dia va alcista o bajista comparando su
    cierre (precio actual) contra su apertura. Devuelve 'alcista', 'bajista'
    o None si no se pudo determinar."""
    params = {
        "symbol": SIMBOLO,
        "interval": "1day",
        "outputsize": 2,
        "apikey": TWELVE_DATA_API_KEY,
    }
    r = requests.get(TWELVE_DATA_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    if data.get("status") == "error":
        raise RuntimeError(f"Twelve Data error: {data.get('message')}")

    velas_diarias = data.get("values", [])
    if not velas_diarias:
        return None

    vela_hoy = velas_diarias[0]  # Twelve Data manda la mas reciente primero
    apertura = float(vela_hoy["open"])
    cierre = float(vela_hoy["close"])

    if cierre > apertura:
        return "alcista"
    elif cierre < apertura:
        return "bajista"
    return None


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
                               f"neckline en {round(neckline,2)}"
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
                               f"neckline en {round(neckline,2)}"
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
                    "detalle": f"Cabeza en {round(cabeza[2],2)}, neckline aprox {round(neckline,2)}"
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
                    "detalle": f"Cabeza en {round(cabeza[2],2)}, neckline aprox {round(neckline,2)}"
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
    global _ultima_vela_procesada

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

        # --- Patrones chartistas (independientes del BOS/CHoCH) ---
        for patron in _detectar_doble_techo_suelo(swings, velas) + _detectar_hch(swings, velas):
            color_patron = 0x5DCAA5 if patron["direccion"] == "alcista" else 0xE24B4A
            enviar_discord(
                f"Patron chartista confirmado: {patron['nombre']}",
                f"Precio actual: {patron['entry']} USD/oz (velas {GRANULARIDAD})\n"
                f"Entry sugerido: {patron['entry']}\n"
                f"Stop Loss: {patron['stop_loss']}\n"
                f"Take Profit: {patron['take_profit']} (altura del patron proyectada)\n\n"
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

        # Filtro de tendencia diaria: solo avisamos si la senal va a favor del dia
        tendencia_diaria = _obtener_tendencia_diaria()
        if tendencia_diaria is not None and tendencia_diaria != evento["direccion"]:
            print(
                f"Senal XAU/USD: {evento['tipo']} {evento['direccion']} detectado, "
                f"pero el dia esta {tendencia_diaria} -- no se manda (va en contra del dia)."
            )
            return

        precio_actual = velas[-1]["c"]
        eqh, eql = _detectar_liquidez(swings)
        fvgs = _detectar_fvg_recientes(velas)

        if evento["direccion"] == "alcista":
            tipo_senal = "BUY"
            # Stop Loss: justo debajo del swing que confirmo la estructura (con un pequeno margen)
            stop_loss = round(evento["swing_opuesto"] * 0.999, 2) if evento["swing_opuesto"] else round(precio_actual * 0.995, 2)
            # Take Profit: el EQH mas cercano por encima del precio actual, si existe
            objetivos = sorted([n for n in eqh if n > precio_actual])
            take_profit = objetivos[0] if objetivos else round(precio_actual + (precio_actual - stop_loss) * RATIO_RIESGO_BENEFICIO_RESPALDO, 2)
            fuente_tp = "zona de liquidez EQH" if objetivos else f"respaldo 1:{RATIO_RIESGO_BENEFICIO_RESPALDO}"
            color = 0x5DCAA5
        else:
            tipo_senal = "SELL"
            stop_loss = round(evento["swing_opuesto"] * 1.001, 2) if evento["swing_opuesto"] else round(precio_actual * 1.005, 2)
            objetivos = sorted([n for n in eql if n < precio_actual], reverse=True)
            take_profit = objetivos[0] if objetivos else round(precio_actual - (stop_loss - precio_actual) * RATIO_RIESGO_BENEFICIO_RESPALDO, 2)
            fuente_tp = "zona de liquidez EQL" if objetivos else f"respaldo 1:{RATIO_RIESGO_BENEFICIO_RESPALDO}"
            color = 0xE24B4A

        lineas_fvg = []
        for z in fvgs:
            lineas_fvg.append(f"FVG {z['tipo']} sin rellenar: {round(z['desde'],2)} - {round(z['hasta'],2)}")
        texto_fvg = "\n".join(lineas_fvg) if lineas_fvg else "Sin FVG relevantes sin rellenar cerca."

        enviar_discord(
            f"{evento['tipo']} {evento['direccion'].upper()} -- posible entrada {tipo_senal}",
            f"Precio actual: {precio_actual} USD/oz (velas {GRANULARIDAD})\n"
            f"Entry sugerido: {precio_actual}\n"
            f"Stop Loss: {stop_loss} (mas alla del swing que confirmo la estructura)\n"
            f"Take Profit: {take_profit} ({fuente_tp})\n\n"
            f"Evento de estructura: {evento['tipo']} -- rompio el nivel {round(evento['nivel_roto'],2)}\n"
            f"Va a favor de la tendencia diaria ({tendencia_diaria or 'sin dato claro'}).\n\n"
            f"{texto_fvg}\n\n"
            f"IMPORTANTE: BOS/CHoCH/EQH/FVG son patrones de analisis tecnico, "
            f"no garantias. Este bot NO ejecuta ninguna orden. Revisa el "
            f"grafico y decide tu si te conviene entrar.",
            color=color
        )

    except Exception as e:
        print(f"Error revisando senal XAU/USD: {e}")


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
# PROGRAMACION
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    threading.Thread(target=iniciar_servidor_web, daemon=True).start()

    print("Bot de senales ICT XAU/USD iniciado. Hora Madrid:", hora_madrid())
    enviar_discord(
        "Bot de senales ICT iniciado",
        f"Vigilando XAU/USD con velas reales de Twelve Data ({GRANULARIDAD}), filtradas "
        f"por la tendencia de la vela diaria. Te aviso cuando detecte un BOS o "
        f"CHoCH a favor del dia (con EQH/EQL para el Take Profit y FVG como "
        f"contexto). Este bot NO ejecuta ninguna orden, la decision es tuya.",
        color=0x639922
    )

    scheduler = BlockingScheduler(timezone=MADRID_TZ)
    scheduler.add_job(revisar_senal, "interval", minutes=INTERVALO_REVISION_MINUTOS)

    revisar_senal()

    scheduler.start()
