# Cenit — Paso Cenital del Sol en Colombia

Calcula, para cualquier ubicación de Colombia, las dos fechas del año en que el
sol pasa exactamente por el cenit al mediodía solar: el momento en que los
objetos verticales no proyectan sombra.

Es un fenómeno exclusivo de la franja tropical —entre los paralelos -23.437° y
23.437°, menos del 40% de la superficie terrestre— y Colombia está enteramente
dentro de ella.

El proyecto tiene dos frentes que comparten los mismos cálculos: una aplicación
de escritorio en Python y una app Android.

## Escritorio

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
