# Cenit — Paso Cenital del Sol en Colombia

[![Compilar escritorio](https://github.com/FilosofoCaucano/cenit/actions/workflows/escritorio.yml/badge.svg)](https://github.com/FilosofoCaucano/cenit/actions/workflows/escritorio.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
[![Descargas](https://img.shields.io/github/downloads/FilosofoCaucano/cenit/total.svg)](https://github.com/FilosofoCaucano/cenit/releases)

Calcula, para cualquier ubicación de Colombia, las dos fechas del año en que el
sol pasa exactamente por el cenit al mediodía solar: el momento en que los
objetos verticales no proyectan sombra.

Es un fenómeno exclusivo de la franja tropical —entre los paralelos -23.437° y
23.437°, menos del 40% de la superficie terrestre— y Colombia está enteramente
dentro de ella.

El proyecto tiene dos frentes que comparten los mismos cálculos: una aplicación
de escritorio en Python y una app Android.

---

# ⬇️ Descargar

**No hace falta instalar Python ni nada más.** Descargá un solo archivo y abrilo.

### 🪟 Windows (64 bits)

**[Descargar Cenit-windows-x64.exe](https://github.com/FilosofoCaucano/cenit/releases/latest)**

Doble clic y listo. La primera vez Windows muestra una pantalla azul que dice
*"Windows protegió su PC"*: es porque el ejecutable no está firmado con un
certificado de pago, no porque tenga nada raro. Hacé clic en **Más información**
y después en **Ejecutar de todas formas**.

Requiere Windows 10 o posterior.

### 🐧 Linux (64 bits)

**[Descargar Cenit-linux-x64](https://github.com/FilosofoCaucano/cenit/releases/latest)**

```bash
chmod +x Cenit-linux-x64
./Cenit-linux-x64
```

Probado sobre Ubuntu. Sirve para **Linux Mint, Ubuntu, Pop!_OS, Debian** y
demás derivadas. Mint está basada en Ubuntu, que a su vez desciende de Debian,
así que el mismo binario vale para todas.

Se compila sobre Ubuntu 22.04 (glibc 2.35), así que funciona en esa versión y
en cualquiera posterior:

| Distribución | Desde |
|---|---|
| Linux Mint | 21 |
| Ubuntu | 22.04 |
| Debian | 12 (bookworm) |
| Pop!_OS | 22.04 |

En distribuciones anteriores falla con un error de `GLIBC`. En ese caso, usalo
desde el código fuente, que no tiene esa limitación.

### 🍎 macOS

No hay ejecutable. macOS bloquea las aplicaciones que no estén notarizadas por
Apple, y notarizar exige una suscripción anual de pago al programa de
desarrolladores. En Mac se puede usar igual desde el código fuente.

### 📱 Android

En camino.

---

## Escritorio desde el código

```bash
pip install -r requirements.txt
py main.py
```

Interfaz en CustomTkinter con las gráficas en Matplotlib. Arranca en Bogotá D.C.
y permite elegir departamento y municipio.

## Módulos de cálculo

| Archivo | Qué hace |
|---|---|
| `solar.py` | Declinación solar y mediodía solar en UTC |
| `zenith.py` | Fechas de paso cenital a partir de la declinación |
| `lugares.py` | Dataset de departamentos y municipios con sus coordenadas |
| `mapsim.py` | Visualización del mapa |
| `generar_datos.py` | Regenera `lugares.py` desde GeoNames (requiere `CO.txt`) |

El cálculo busca los días en que la declinación solar cruza la latitud del
lugar. Cuando el cruce cae entre dos mediodías solares se toma el día en que el
sol pasa más cerca del cenit, comparando distancias en vez de redondear — Python
y JavaScript redondean los empates de forma distinta y el escritorio y el móvil
llegaban a dar días diferentes.

## Móvil

La app Android es un WebView empaquetado con Capacitor.

`preview_movil.html` es la **única fuente de verdad** de la interfaz móvil: se
edita ahí y luego se genera la versión de la app.

```bash
py build_movil.py     # preview_movil.html -> movil/www/index.html
cd movil
npx cap sync android
```

`build_movil.py` no recorta HTML: inyecta un bloque de CSS que fuerza el modo
app siempre, de modo que en una tablet no aparezca el marco de vista previa de
escritorio.

## Datos

`lugares.py` se genera desde el dataset de Colombia de [GeoNames](https://download.geonames.org/export/dump/).
Descargá `CO.txt` en la raíz del proyecto y corré `py generar_datos.py`. El
archivo no se versiona por tamaño.

## Firma de la app

Los keystores (`*.jks`, `*.keystore`) y `movil/android/key.properties` están
excluidos del repositorio a propósito. Si esa clave se filtra, cualquiera puede
publicar actualizaciones haciéndose pasar por la app; si se pierde, la app no se
puede volver a actualizar nunca. Guardala aparte y con respaldo.

## Publicar una versión

Los ejecutables los compila GitHub Actions, no hace falta compilarlos a mano.
Al empujar una etiqueta se generan los binarios de Windows y Linux, se prueba
que cada uno arranque de verdad y se publica la Release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Desde la pestaña Actions se puede lanzar el mismo flujo a mano, sin publicar
nada: deja los binarios como artefactos descargables.

## Licencia

[MIT](LICENSE) — se puede usar, modificar y redistribuir libremente,
conservando el aviso de autoría.

Los datos de municipios provienen de [GeoNames](https://www.geonames.org/),
bajo licencia CC BY 4.0.
