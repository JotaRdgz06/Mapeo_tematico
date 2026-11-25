"""
procesar_gpx.py
Lee todos los archivos .gpx del repositorio (los que sube OSMTracker)
y genera un único archivo datos.geojson que consume el mapa (index.html).
Solo usa librerías que ya trae Python, no hay que instalar nada.
"""
import glob
import json
import math
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ---------------------------------------------------------------
# CONFIGURACIÓN (lo que probablemente van a querer modificar)
# ---------------------------------------------------------------
SALIDA = "datos.geojson"
HORAS_UTC = -6            # Costa Rica = UTC-6 todo el año
MAX_SEG_FOTO = 120        # una foto se pega a un punto si pasaron <= 120 s
MAX_M_FOTO = 30           # ... y si está a <= 30 m
MIN_M_TRAZA = 3           # la traza guarda un punto cada 3 m (menos peso)

# Nombre del botón en OSMTracker  ->  categoría del mapa
CATEGORIAS = {
    "Acera": "Aceras",
    "fin de la acera": "Aceras",
    "Paso peatonal": "Cruces y tránsito",
    "Semaforo": "Cruces y tránsito",
    "Señal de tránsito": "Cruces y tránsito",
    "Reductor velocidad": "Cruces y tránsito",
    "Hidrante": "Seguridad",
    "Parque": "Espacios de permanencia",
    "Cancha de futbol": "Espacios de permanencia",
    "Parada bus": "Transporte público",
    "Recorrido bus": "Transporte público",
}
CATEGORIA_POR_DEFECTO = "Otros"

NS = {"g": "http://www.topografix.com/GPX/1/1"}


def hora_local(texto_utc):
    """'2026-10-04T16:27:14Z' -> datetime en hora de Costa Rica."""
    dt = datetime.strptime(texto_utc, "%Y-%m-%dT%H:%M:%SZ")
    return dt + timedelta(hours=HORAS_UTC)


def distancia_m(lat1, lon1, lat2, lon2):
    """Distancia aproximada en metros entre dos coordenadas."""
    dy = (lat2 - lat1) * 111_320
    dx = (lon2 - lon1) * 111_320 * math.cos(math.radians(lat1))
    return math.hypot(dx, dy)


def procesar_gpx(ruta):
    raiz = ET.parse(ruta).getroot()
    carpeta = os.path.dirname(ruta)
    nombre_traza = os.path.splitext(os.path.basename(ruta))[0]
    features = []
    ultimo = None  # último punto que NO es foto

    # ---- Waypoints (los botones) ----
    for w in raiz.findall("g:wpt", NS):
        lat, lon = float(w.get("lat")), float(w.get("lon"))
        tipo = w.find("g:name", NS).text.strip()
        t = hora_local(w.find("g:time", NS).text)
        enlace = w.find("g:link", NS)
        archivo = enlace.get("href") if enlace is not None else None
        ruta_archivo = (os.path.join(carpeta, archivo).replace("\\", "/")
                        if archivo else None)

        # OSMTracker guarda cada foto como un waypoint aparte llamado "Foto".
        # Si es cercano en tiempo y espacio al punto anterior, se la pegamos.
        if tipo == "Foto" and ultimo is not None:
            seg = (t - ultimo["t"]).total_seconds()
            dist = distancia_m(lat, lon, ultimo["lat"], ultimo["lon"])
            if seg <= MAX_SEG_FOTO and dist <= MAX_M_FOTO:
                ultimo["props"]["fotos"].append(ruta_archivo)
                continue

        props = {
            "tipo": tipo,
            "categoria": CATEGORIAS.get(tipo, CATEGORIA_POR_DEFECTO),
            "fecha": t.strftime("%Y-%m-%d"),
            "hora": t.strftime("%H:%M:%S"),
            "traza": nombre_traza,
            "fotos": [ruta_archivo] if (tipo == "Foto" and ruta_archivo) else [],
        }
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
            "properties": props,
        }
        features.append(feature)
        if tipo != "Foto":
            ultimo = {"t": t, "lat": lat, "lon": lon, "props": props}

    # ---- Trazas (el recorrido) ----
    for trk in raiz.findall("g:trk", NS):
        coords, tiempos = [], []
        for pt in trk.iter("{%s}trkpt" % NS["g"]):
            lat, lon = float(pt.get("lat")), float(pt.get("lon"))
            if coords and distancia_m(coords[-1][1], coords[-1][0], lat, lon) < MIN_M_TRAZA:
                continue
            coords.append([round(lon, 6), round(lat, 6)])
            tiempos.append(pt.find("g:time", NS).text)
        if len(coords) < 2:
            continue
        inicio, fin = hora_local(tiempos[0]), hora_local(tiempos[-1])
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "tipo": "Traza",
                "categoria": "Recorrido",
                "fecha": inicio.strftime("%Y-%m-%d"),
                "hora": inicio.strftime("%H:%M:%S"),
                "fin": fin.strftime("%H:%M:%S"),
                "traza": nombre_traza,
                "fotos": [],
            },
        })
    return features


def main():
    rutas = sorted(
        r for r in glob.glob("**/*.gpx", recursive=True)
        if not r.startswith(".")
    )
    todos = []
    for ruta in rutas:
        print("Procesando", ruta)
        todos.extend(procesar_gpx(ruta))

    geojson = {"type": "FeatureCollection", "features": todos}
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=1)
    print(f"Listo: {len(rutas)} GPX -> {len(todos)} elementos en {SALIDA}")


if __name__ == "__main__":
    main()
