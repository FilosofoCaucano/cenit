"""Genera movil/www/index.html a partir de preview_movil.html.

preview_movil.html es la ÚNICA fuente de verdad: se edita ahí y se corre este
script. La diferencia entre la vista previa y la app instalada es solo el
"cromo" de escritorio —el marco de teléfono, la cabecera de la página, el
panel de novedades y la barra de estado falsa—, que en la app sobra.

No se recorta HTML (frágil y propenso a romper el marcado): se inyecta un
bloque de CSS al final de la hoja de estilos que fuerza el modo app siempre.
Es exactamente la media query de `max-width: 480px` que ya existe, pero sin
condición, para que un tablet no muestre la vista previa de escritorio.

Uso:  py build_movil.py
"""

import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
ORIGEN = os.path.join(RAIZ, "preview_movil.html")
DESTINO = os.path.join(RAIZ, "movil", "www", "index.html")

MODO_APP = """
  /* ==================================================================
     MODO APP — inyectado por build_movil.py, no editar aquí.
     Fuerza a pantalla completa sin depender del ancho: en un tablet la
     media query de 480px no aplicaría y se vería la vista previa de
     escritorio dentro de la app.
     ================================================================== */
  .page-header, .notes, .notch, .status-bar { display: none !important; }
  body { padding: 0 !important; }
  .wrap { max-width: none !important; }
  .layout { gap: 0 !important; grid-template-columns: 1fr !important; }
  .phone {
    width: 100vw !important; max-width: none !important;
    height: 100vh !important; height: 100dvh !important;
    border: none !important; border-radius: 0 !important; box-shadow: none !important;
  }
  .app-bar { padding-top: calc(14px + env(safe-area-inset-top, 0px)) !important; }
  .screen {
    height: calc(100vh - 66px - env(safe-area-inset-top, 0px)) !important;
    height: calc(100dvh - 66px - env(safe-area-inset-top, 0px)) !important;
    padding-bottom: calc(28px + env(safe-area-inset-bottom, 0px)) !important;
  }
  .sheet { padding-bottom: calc(22px + env(safe-area-inset-bottom, 0px)) !important; }
  .snackbar { bottom: calc(24px + env(safe-area-inset-bottom, 0px)) !important; }

  /* En la app no hay barra de direcciones que rebote: matamos el
     overscroll para que no aparezca el efecto de estiramiento sobre un
     fondo que no es el de la app. */
  html, body { overscroll-behavior: none; }
"""


def construir():
    if not os.path.exists(ORIGEN):
        sys.exit("no encuentro %s" % ORIGEN)

    html = io.open(ORIGEN, encoding="utf-8-sig").read()

    # El bloque grande de estilos es el último </style> antes del marcado.
    cierres = [m.start() for m in re.finditer(r"</style>", html)]
    if len(cierres) < 2:
        sys.exit("esperaba al menos dos bloques <style> en el HTML")
    corte = cierres[-1]

    salida = html[:corte] + MODO_APP + html[corte:]

    # Un aviso para quien abra el archivo generado
    salida = salida.replace(
        "<title>",
        "<!-- GENERADO POR build_movil.py — editar preview_movil.html -->\n<title>",
        1,
    )

    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    io.open(DESTINO, "w", encoding="utf-8").write(salida)

    # Comprobaciones mínimas: que no se haya roto nada por el camino
    problemas = []
    if "MODO APP" not in salida:
        problemas.append("no se inyectó el modo app")
    if salida.count("</style>") != html.count("</style>"):
        problemas.append("cambió el número de bloques <style>")
    for tag in ("section", "div", "details"):
        cuerpo = salida[salida.index("<body>"):]
        cuerpo = re.sub(r"<!--.*?-->", "", cuerpo, flags=re.S)
        cuerpo = re.sub(r"<style>.*?</style>", "", cuerpo, flags=re.S)
        cuerpo = cuerpo[:cuerpo.index("<script>")]
        a = len(re.findall(r"<%s[\s>]" % tag, cuerpo))
        c = len(re.findall(r"</%s>" % tag, cuerpo))
        if a != c:
            problemas.append("<%s> desbalanceado: %d abre / %d cierra" % (tag, a, c))

    print("origen : %s (%d KB)" % (os.path.basename(ORIGEN), len(html) // 1024))
    print("destino: movil/www/index.html (%d KB)" % (len(salida) // 1024))
    if problemas:
        for p in problemas:
            print("  PROBLEMA:", p)
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    construir()
