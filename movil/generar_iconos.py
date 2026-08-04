"""Genera los recursos gráficos de la app: icono adaptativo, splash y el
icono monocromo de notificación.

La marca: el sol justo encima de un gnomon vertical, y a sus pies la sombra
reducida a nada. Es literalmente lo que la app calcula.

Zona segura de los iconos adaptativos de Android: el sistema recorta el
lienzo a círculo, cuadrado redondeado, gota... y solo garantiza el 66%
central. Todo el dibujo se mantiene dentro de ese radio.

Uso:  py generar_iconos.py
"""

import io
import math
import os

from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(RAIZ, "resources")

SS = 4  # supersampling: se dibuja a 4x y se reduce, para bordes suaves

AZUL_NOCHE = (13, 33, 54)
AZUL_HONDO = (8, 22, 38)
SOL = (253, 214, 99)
SOL_BORDE = (234, 134, 0)
GNOMON = (232, 234, 237)


def lienzo(lado, fondo=None):
    return Image.new("RGBA", (lado * SS, lado * SS), fondo or (0, 0, 0, 0))


def reducir(img, lado):
    return img.resize((lado, lado), Image.LANCZOS)


def _capsula(d, x1, y1, x2, y2, grosor, color):
    """Línea con las puntas redondeadas: PIL no tiene round caps."""
    r = grosor / 2
    d.line([(x1, y1), (x2, y2)], fill=color, width=int(grosor))
    for x, y in ((x1, y1), (x2, y2)):
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


def dibujar_marca(d, cx, cy, escala, color_sol=SOL, borde=SOL_BORDE,
                  color_gnomon=GNOMON, con_borde=True):
    """La marca centrada ópticamente en (cx, cy). `escala` = radio seguro.

    La geometría se define respecto al sol y luego se desplaza en bloque
    para que el conjunto —desde la punta del rayo más alto hasta la base
    del gnomon— quede centrado. Sin ese ajuste todo el peso se va arriba.
    """
    r_sol = 0.355 * escala
    dy_sol = -0.36 * escala          # el sol, respecto al centro
    largo_ext = r_sol * 1.72
    gy0, gy1 = 0.16 * escala, 0.72 * escala
    gx = 0.075 * escala

    arriba = dy_sol - largo_ext
    abajo = gy1 + gx * 0.55
    ajuste = -(arriba + abajo) / 2    # centra el conjunto verticalmente

    y_sol = cy + dy_sol + ajuste

    # rayos, con las puntas redondeadas
    largo_int = r_sol * 1.32
    grosor = 0.085 * escala
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        _capsula(d,
                 cx + largo_int * math.cos(a), y_sol + largo_int * math.sin(a),
                 cx + largo_ext * math.cos(a), y_sol + largo_ext * math.sin(a),
                 grosor, color_sol)

    # disco solar
    d.ellipse([cx - r_sol, y_sol - r_sol, cx + r_sol, y_sol + r_sol],
              fill=color_sol,
              outline=borde if con_borde else None,
              width=max(1, int(0.03 * escala)) if con_borde else 0)

    # gnomon vertical
    d.rounded_rectangle([cx - gx, cy + gy0 + ajuste, cx + gx, cy + gy1 + ajuste],
                        radius=gx, fill=color_gnomon)

    # la sombra, reducida a nada: una elipse mínima a sus pies
    base = cy + gy1 + ajuste
    d.ellipse([cx - gx * 2.6, base - gx * 0.55, cx + gx * 2.6, base + gx * 0.55],
              fill=color_gnomon)


def icono_foreground(lado=1024):
    img = lienzo(lado)
    d = ImageDraw.Draw(img)
    c = lado * SS / 2
    # capacitor-assets mete este PNG en el lienzo adaptativo con un inset del
    # 16.7%, o sea que el dibujo ocupa los 72dp siempre visibles de los 108dp.
    # Con escala 0.42 la marca mide 0.73 del lienzo (~52dp) y su semidiagonal
    # queda en ~32dp, justo por dentro del círculo seguro de 66dp de diámetro.
    dibujar_marca(d, c, c, escala=0.42 * lado * SS)
    return reducir(img, lado)


def icono_background(lado=1024):
    img = lienzo(lado, AZUL_NOCHE)
    d = ImageDraw.Draw(img)
    n = lado * SS
    # degradado suave hacia las esquinas, en bandas concéntricas
    for i in range(60, 0, -1):
        t = i / 60
        r = int(n * 0.78 * t)
        col = tuple(int(AZUL_NOCHE[k] + (AZUL_HONDO[k] - AZUL_NOCHE[k]) * (1 - t))
                    for k in range(3))
        d.ellipse([n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r], fill=col + (255,))
    return reducir(img, lado)


def icono_completo(lado=1024):
    fondo = icono_background(lado)
    frente = icono_foreground(lado)
    fondo.alpha_composite(frente)
    return fondo


def splash(lado=2732):
    img = lienzo(lado, AZUL_NOCHE)
    d = ImageDraw.Draw(img)
    c = lado * SS / 2
    dibujar_marca(d, c, c, escala=0.13 * lado * SS)
    return reducir(img, lado)


def icono_notificacion(lado=96):
    """Android exige silueta blanca sobre transparente: cualquier color se
    descarta y quedaría un cuadrado gris."""
    img = lienzo(lado)
    d = ImageDraw.Draw(img)
    c = lado * SS / 2
    blanco = (255, 255, 255, 255)
    dibujar_marca(d, c, c, escala=0.42 * lado * SS,
                  color_sol=blanco, borde=None,
                  color_gnomon=blanco, con_borde=False)
    return reducir(img, lado)


# El icono de la barra de estado va a 24dp: una copia por densidad.
# capacitor-assets no genera este recurso, hay que ponerlo a mano.
DENSIDADES = [("mdpi", 24), ("hdpi", 36), ("xhdpi", 48),
              ("xxhdpi", 72), ("xxxhdpi", 96)]


def escribir_icono_notificacion():
    res = os.path.join(RAIZ, "android", "app", "src", "main", "res")
    if not os.path.isdir(res):
        print("\n  (aun no existe android/: corre `npx cap add android` y repite)")
        return
    for sufijo, lado in DENSIDADES:
        carpeta = os.path.join(res, "drawable-" + sufijo)
        os.makedirs(carpeta, exist_ok=True)
        icono_notificacion(lado).save(os.path.join(carpeta, "ic_stat_cenit.png"))
    print("\n  ic_stat_cenit.png -> %d densidades en android/app/src/main/res/"
          % len(DENSIDADES))


def main():
    os.makedirs(DESTINO, exist_ok=True)
    piezas = [
        ("icon-foreground.png", icono_foreground()),
        ("icon-background.png", icono_background()),
        ("icon.png", icono_completo()),
        ("splash.png", splash()),
        ("splash-dark.png", splash()),
        ("ic_stat_cenit.png", icono_notificacion(96)),
    ]
    for nombre, img in piezas:
        ruta = os.path.join(DESTINO, nombre)
        img.save(ruta)
        print("  %-24s %dx%d" % (nombre, img.width, img.height))
    print("\nescritos en movil/resources/")
    escribir_icono_notificacion()


if __name__ == "__main__":
    main()
