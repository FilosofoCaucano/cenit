# Cenit — Paso Cenital del Sol en Colombia

Calcula, para cualquier ubicación de Colombia, las dos fechas del año en que el
sol pasa exactamente por el cenit al mediodía solar: el momento en que los
objetos verticales no proyectan sombra.

Es un fenómeno exclusivo de la franja tropical —entre los paralelos -23.437° y
23.437°, menos del 40% de la superficie terrestre— y Colombia está enteramente
dentro de ella.

El proyecto tiene dos frentes que comparten los mismos cálculos: una aplicación
de escritorio en Python y una app Android.

## Descargar

Los ejecutables de cada versión están en la [página de Releases](https://github.com/FilosofoCaucano/cenit/releases).
No hace falta instalar Python.

| Sistema | Archivo | Cómo se abre |
|---|---|---|
| Windows | `Cenit-windows.exe` | Doble clic |
| Linux | `Cenit-linux` | `chmod +x Cenit-linux` y después `./Cenit-linux` |

En Windows, la primera vez aparece un aviso de SmartScreen porque el
ejecutable no está firmado con un certificado de pago: **Más información →
Ejecutar de todas formas**.

No hay versión para macOS: Apple bloquea las aplicaciones sin notarizar, y
notarizar exige una suscripción anual al programa de desarrolladores. En Mac
se puede usar igual desde el código fuente, como se explica abajo.

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
