# Cenit — app Android

App de [Capacitor](https://capacitorjs.com) que empaqueta la interfaz web en un
APK/AAB nativo. Todo el cálculo corre en el dispositivo: **no necesita internet
ni un servidor**, y no caduca — las fechas se calculan con el motor solar
NOAA/Meeus portado a JavaScript, no con una tabla precocinada.

```
movil/
├── package.json            npm + scripts
├── capacitor.config.json   appId, nombre, plugins
├── generar_iconos.py       icono adaptativo, splash e icono de notificación
├── resources/              fuentes 1024×1024 y 2732×2732 (generadas)
├── www/index.html          GENERADO — no editar
└── android/                proyecto Android nativo (Capacitor lo genera)
```

## Una sola fuente de verdad

`www/index.html` **se genera**. La app se edita en `../preview_movil.html` y
después se corre el build. Lo único que cambia es el "cromo" de escritorio
—marco de teléfono, cabecera, panel de novedades— que en la app sobra.

```bash
py ../build_movil.py     # preview_movil.html -> www/index.html
npx cap sync android     # www/ -> android/app/src/main/assets/public/
```

O de una: `npm run sync`

## Qué falta en esta máquina

| | |
|---|---|
| Node / npm | ✅ |
| JDK | ⚠️ 18.0.2 fuera del PATH — **Android quiere 17** |
| Android SDK | ❌ `ANDROID_HOME` apunta a una carpeta que no existe |
| Android Studio | ❌ no instalado |

Sin el SDK no se puede compilar. Instalá [Android Studio](https://developer.android.com/studio)
(trae el SDK y un JDK 17 propio) y ya.

## Compilar

```bash
npm install              # una sola vez
npm run sync             # cada vez que edites la interfaz
npx cap open android     # abre Android Studio -> botón Run
```

Desde la terminal, si preferís:

```bash
npm run apk              # APK de depuración -> android/app/build/outputs/apk/debug/
npm run aab              # AAB de release   -> android/app/build/outputs/bundle/release/
```

Si Gradle se queja de la versión de Java, apuntá al JDK que trae Android Studio:

```bash
# PowerShell
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
```

## Probar en un celular de verdad

1. Activá **Opciones de desarrollador** → **Depuración por USB** en el teléfono.
2. Conectalo y corré `npx cap run android`.
3. En el PC abrí **`chrome://inspect`** → aparece la WebView de la app y tenés
   DevTools completas: consola, red, inspector. Es la herramienta clave, y los
   builds de depuración ya vienen con esto habilitado (en release se apaga solo).

Lo que de verdad encuentra bugs, en este orden:

- **Tamaño de fuente al 130%** (Ajustes → Pantalla). Rompe más layouts que nada.
- **Botón atrás** con la hoja de municipios abierta → debe subir de nivel, luego cerrar.
- **Modo avión** → tiene que funcionar igual. Si algo falla, se coló una dependencia de red.
- **Tema oscuro del sistema** y el botón de tema de la app.
- **Rotar la pantalla** y un celular con notch.
- **Cambiar la zona horaria del teléfono** → las fechas NO deben moverse (se
  calculan en UTC−5 explícito).

## Publicar en Google Play

Lo que ya está resuelto:

- `applicationId` = `co.cenit.diasinsombra`
- `targetSdk 35` (Android 15) — el mínimo que Play exige para apps nuevas
- `minSdk 23` (Android 6) — cubre prácticamente todo el parque
- Iconos adaptativos, splash claro y oscuro, icono monocromo de notificación
- Permisos: solo `POST_NOTIFICATIONS`, `RECEIVE_BOOT_COMPLETED`, `WAKE_LOCK`
  (los aporta el plugin de notificaciones) e `INTERNET` (por defecto de Capacitor)

### 1. Firma

Una vez en la vida — **si perdés este archivo no podés volver a actualizar la app**:

```bash
keytool -genkey -v -keystore cenit-release.jks -keyalg RSA \
        -keysize 2048 -validity 10000 -alias cenit
```

Guardalo **fuera del repositorio**. En `android/key.properties` (que va al
`.gitignore`):

```properties
storeFile=C:/ruta/segura/cenit-release.jks
storePassword=...
keyAlias=cenit
keyPassword=...
```

Y enganchalo en `android/app/build.gradle` dentro de `signingConfigs`.

### 2. Subir la versión en cada release

En `android/app/build.gradle`:

```gradle
versionCode 2          // entero, +1 en cada subida. Play rechaza repetidos.
versionName "1.1"      // el que ve la gente
```

### 3. Generar el AAB

Play ya no acepta APK para apps nuevas, hay que subir **AAB**:

```bash
npm run aab
```

### 4. En Play Console

Cuenta de desarrollador: **25 USD, pago único**.

- Ficha: título, descripción corta (80), descripción larga (4000)
- Capturas: mínimo 2 de teléfono; ícono 512×512; gráfico destacado 1024×500
- **Política de privacidad**: obligatoria, con URL pública. Aunque la app no
  recoja nada, hay que declararlo.
- **Data safety**: esta app no recolecta ni transmite datos. Es la respuesta
  más fácil que existe — mantenela así.
- Clasificación de contenido: cuestionario, sale "para todos"
- Cuentas nuevas: se exige un **test cerrado con 12 probadores durante 14 días**
  antes de poder publicar en producción.

### Antes de subir, revisá

- [ ] `versionCode` mayor que el de la versión anterior
- [ ] Compilaste **release**, no debug
- [ ] El AAB está firmado con tu keystore
- [ ] Probaste en un dispositivo real, no solo el emulador
- [ ] `npm run sync` corrido después del último cambio en `preview_movil.html`

> **Sobre `INTERNET`**: la app es 100% offline, pero Capacitor pone ese permiso
> por defecto. Se puede quitar del manifiesto para una ficha aún más limpia —
> probalo en un dispositivo real antes, no vaya a ser que el puente de Capacitor
> lo necesite.

## Notificaciones

Se programan dos por paso cenital: la **víspera a las 7:00 p.m.** y **45 minutos
antes** del instante exacto, ambas en hora de Colombia. Se usan alarmas
**inexactas** a propósito: para un aviso de la noche anterior sobran, y pedir
`SCHEDULE_EXACT_ALARM` atrae revisión extra de Play sin ganar nada.

En el navegador el botón no rompe nada: avisa que los recordatorios solo
funcionan en la app instalada.
