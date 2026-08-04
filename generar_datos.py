"""Genera el dataset de departamentos y municipios a partir de GeoNames."""

import io
import json
import os
import sys

SCRATCH = os.path.dirname(os.path.abspath(__file__))
PROYECTO = r"c:\Users\Willi\Downloads\ProyectoAstronomia"
sys.path.insert(0, PROYECTO)

import solar  # noqa: E402
import zenith  # noqa: E402

# Nombres en español, limpiando el "Department" que trae GeoNames
NOMBRES = {
    "01": "Amazonas", "02": "Antioquia", "03": "Arauca", "04": "Atlántico",
    "35": "Bolívar", "36": "Boyacá", "37": "Caldas", "08": "Caquetá",
    "32": "Casanare", "09": "Cauca", "10": "Cesar", "11": "Chocó",
    "12": "Córdoba", "33": "Cundinamarca", "15": "Guainía", "14": "Guaviare",
    "16": "Huila", "17": "La Guajira", "38": "Magdalena", "19": "Meta",
    "20": "Nariño", "21": "Norte de Santander", "22": "Putumayo",
    "23": "Quindío", "24": "Risaralda", "25": "San Andrés y Providencia",
    "26": "Santander", "27": "Sucre", "28": "Tolima", "29": "Valle del Cauca",
    "30": "Vaupés", "31": "Vichada", "34": "Bogotá D.C.",
}

# Feature codes de GeoNames que corresponden a poblados
POBLADOS = {"PPLC", "PPLA", "PPLA2", "PPLA3", "PPL", "PPLG"}

# Municipios de referencia del proyecto que deben aparecer aunque no estén
# entre los 10 más poblados de su departamento
FORZAR = {
    "Valle del Cauca": ["San Pedro"],
}

por_depto = {}

with io.open(os.path.join(SCRATCH, "CO.txt"), encoding="utf-8") as fh:
    for linea in fh:
        campos = linea.rstrip("\n").split("\t")
        if len(campos) < 15:
            continue
        nombre, lat, lon = campos[1], campos[4], campos[5]
        fclass, fcode, admin1, poblacion = campos[6], campos[7], campos[10], campos[14]

        if fclass != "P" or fcode not in POBLADOS:
            continue
        if admin1 not in NOMBRES:
            continue

        try:
            lat_f, lon_f, pob = float(lat), float(lon), int(poblacion or 0)
        except ValueError:
            continue

        por_depto.setdefault(admin1, []).append(
            {"nombre": nombre, "lat": lat_f, "lon": lon_f, "pob": pob, "cap": fcode in ("PPLC", "PPLA")}
        )

ANIO = 2026
salida = {}
total = 0

for codigo in sorted(NOMBRES, key=lambda c: NOMBRES[c]):
    depto = NOMBRES[codigo]
    lugares = por_depto.get(codigo, [])

    # Sin duplicados por nombre, quedándonos con el de mayor población
    unicos = {}
    for lugar in lugares:
        previo = unicos.get(lugar["nombre"])
        if previo is None or lugar["pob"] > previo["pob"]:
            unicos[lugar["nombre"]] = lugar

    # Solo lugares con población registrada (o capital). Preferimos que un
    # departamento tenga menos de 10 a rellenarlo con veredas y caseríos.
    reales = [x for x in unicos.values() if x["pob"] > 0 or x["cap"]]
    reales.sort(key=lambda x: (not x["cap"], -x["pob"]))
    ordenados = reales[:10]

    # Bogotá D.C. es un solo distrito: no tiene sentido listarle barrios.
    if depto == "Bogotá D.C.":
        ordenados = [x for x in ordenados if x["nombre"] == "Bogotá"]

    # Municipios que el proyecto usa de referencia y deben estar sí o sí
    for forzado in FORZAR.get(depto, []):
        if any(x["nombre"] == forzado for x in ordenados):
            continue
        extra = unicos.get(forzado)
        if extra:
            ordenados.append(extra)

    items = []
    for lugar in ordenados:
        pasos = zenith.find_zenith_passages(lugar["lat"], lugar["lon"], ANIO)
        if len(pasos) != 2:
            continue
        locales = [p.astimezone(solar.COLOMBIA_TZ) for p in pasos]
        items.append({
            "n": lugar["nombre"],
            "lat": round(lugar["lat"], 4),
            "lon": round(lugar["lon"], 4),
            "pob": lugar["pob"],
            "cap": lugar["cap"],
            "f1": [locales[0].month - 1, locales[0].day],
            "f2": [locales[1].month - 1, locales[1].day],
            "h1": locales[0].strftime("%H:%M"),
            "h2": locales[1].strftime("%H:%M"),
        })

    if items:
        salida[depto] = items
        total += len(items)

with io.open(os.path.join(SCRATCH, "lugares.json"), "w", encoding="utf-8") as fh:
    json.dump(salida, fh, ensure_ascii=False, separators=(",", ":"))

# Módulo Python para la app de escritorio
CABECERA = '''"""Departamentos de Colombia y sus municipios principales.

GENERADO AUTOMÁTICAMENTE — no editar a mano.

Fuente de coordenadas y población: GeoNames (dominio público, CC BY 4.0),
descarga de {anio}. Se toman los 10 municipios más poblados de cada
departamento, con la capital siempre de primera.

Estructura: DEPARTAMENTOS[departamento] = [(municipio, lat, lon), ...]
"""

DEPARTAMENTOS = {{
'''

with io.open(os.path.join(SCRATCH, "lugares.py"), "w", encoding="utf-8") as fh:
    fh.write(CABECERA.format(anio=ANIO))
    for depto in sorted(salida):
        fh.write(f'    "{depto}": [\n')
        for x in salida[depto]:
            fh.write(f'        ("{x["n"]}", {x["lat"]}, {x["lon"]}),\n')
        fh.write("    ],\n")
    fh.write("}\n\n")
    fh.write('PERSONALIZADO = "Coordenadas personalizadas..."\n\n')
    fh.write("NOMBRES_DEPARTAMENTOS = sorted(DEPARTAMENTOS) + [PERSONALIZADO]\n\n\n")

    fh.write("def municipios(departamento):\n")
    fh.write('    """Nombres de los municipios de un departamento."""\n')
    fh.write("    return [m for m, _, _ in DEPARTAMENTOS.get(departamento, [])]\n\n\n")

    fh.write("def coordenadas(departamento, municipio):\n")
    fh.write('    """(lat, lon) de un municipio, o None si no existe."""\n')
    fh.write("    for nombre, lat, lon in DEPARTAMENTOS.get(departamento, []):\n")
    fh.write("        if nombre == municipio:\n")
    fh.write("            return lat, lon\n")
    fh.write("    return None\n\n\n")

    fh.write("def todos():\n")
    fh.write('    """[(municipio, departamento, lat, lon), ...] de todo el país."""\n')
    fh.write("    return [\n")
    fh.write("        (m, depto, lat, lon)\n")
    fh.write("        for depto, lista in DEPARTAMENTOS.items()\n")
    fh.write("        for m, lat, lon in lista\n")
    fh.write("    ]\n")

print("Departamentos:", len(salida))
print("Municipios:   ", total)
print()

# --- verificación contra los valores ya validados a mano ---
ESPERADO = {
    ("Cundinamarca", "Bogotá"): None,   # Bogotá D.C. va aparte
    ("Bogotá D.C.", "Bogotá"): ((3, 1), (8, 10)),
    ("Valle del Cauca", "Cali"): ((2, 29), (8, 13)),
    ("Valle del Cauca", "Tuluá"): ((2, 30), (8, 12)),
    ("Atlántico", "Barranquilla"): ((3, 18), (7, 24)),
    ("Amazonas", "Leticia"): ((2, 9), (9, 3)),
    ("San Andrés y Providencia", "San Andrés"): ((3, 23), (7, 19)),
}
MES = ["ene", "feb", "mar", "abr", "may", "jun",
       "jul", "ago", "sep", "oct", "nov", "dic"]
print("Contraste con los cálculos verificados antes:")
for (depto, ciudad), esperado in ESPERADO.items():
    if esperado is None:
        continue
    encontrado = next((x for x in salida.get(depto, []) if x["n"] == ciudad), None)
    if encontrado is None:
        print(f"  {ciudad:16} NO ESTA en {depto}")
        continue
    real = (tuple(encontrado["f1"]), tuple(encontrado["f2"]))
    ok = "OK " if real == esperado else "DIFIERE"
    print(f"  {ok} {ciudad:16} {real[0][1]} {MES[real[0][0]]} / {real[1][1]} {MES[real[1][0]]}"
          f"   (esperado {esperado[0][1]} {MES[esperado[0][0]]} / {esperado[1][1]} {MES[esperado[1][0]]})")

print()
for depto in sorted(salida):
    nombres = ", ".join(x["n"] for x in salida[depto][:5])
    print(f"  {depto:28} {len(salida[depto]):2}  {nombres}")
