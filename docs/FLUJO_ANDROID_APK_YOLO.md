# Flujo oficial de Sensus AI: APK Android + YOLO

## Decisión actual

El flujo oficial de prueba ya no es Expo Go. La aplicación se entrega como un APK Android independiente y usa el backend de Sensus AI desplegado en AWS EC2.

Expo sigue apareciendo como parte del stack interno porque el proyecto usa módulos Expo dentro de React Native, pero eso no significa que el usuario deba instalar Expo Go ni mantener Metro abierto. El APK contiene el bundle JavaScript y los módulos nativos necesarios.

## Arquitectura de la prueba

```text
APK Android instalado
        |
        v
API pública de AWS EC2: http://100.24.55.64:8000
        |
        v
FastAPI + YOLO11n (principal) + Depth Anything V2 (distancia aproximada)
        |
        v
Respuesta de detección y alertas para la app
```

Gemini está apagado en la EC2 para esta etapa. YOLO es el motor principal y la app usa las rutas rápidas de visión (`/api/vision/fast-detect` y `/api/vision/realtime`).

## Correcciones realizadas

- Se dejó de usar Expo Go como requisito de prueba.
- La URL del frontend apunta a AWS, no a `localhost` ni a la IP local de la laptop.
- Se generó un APK release local con Gradle.
- Se limitó la compilación local a `arm64-v8a` para evitar el fallo de CMake/Ninja con `armeabi-v7a` de VisionCamera.
- Se configuró `frontend/android/local.properties` para que Gradle encuentre el Android SDK de esta computadora.
- Se habilitó tráfico HTTP claro en el APK únicamente para esta prueba, porque la EC2 temporal usa `http://100.24.55.64:8000`; sin esto Android muestra `CLEARTEXT communication ... not permitted`.
- El backend responde con YOLO y profundidad habilitados; Gemini permanece apagado.

## Entorno local confirmado

Esta computadora tiene lo necesario para compilar el APK:

- Windows.
- Java 17: Eclipse Adoptium `17.0.17`.
- Android SDK: `C:\Users\CARLOS\AppData\Local\Android\Sdk`.
- Gradle Wrapper del proyecto: `frontend/android/gradlew.bat`.
- Expo CLI instalado como herramienta de compilación, no como requisito de ejecución para el usuario.

## Compilar el APK localmente

Desde PowerShell:

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend\android"
.\gradlew.bat assembleRelease
```

El APK queda en:

```text
C:\proyecto para ciegos app\SensusAI\frontend\android\app\build\outputs\apk\release\app-release.apk
```

También se dejó una copia fácil de compartir en:

```text
C:\proyecto para ciegos app\SensusAI\SensusAI-YOLO-local-arm64.apk
```

## Importante

- El APK no necesita Expo Go.
- El APK no necesita que esta computadora esté encendida para analizar: la API corre en AWS.
- Si cambia la IP pública de la EC2, hay que actualizar la URL y recompilar el APK. Para evitarlo después conviene asignar una Elastic IP o un dominio HTTPS.
- Antes de una prueba pública real, se debe reemplazar HTTP por HTTPS y quitar `usesCleartextTraffic`.
- `frontend/android/local.properties` es configuración de esta computadora y no debe subirse a GitHub.
- La compilación EAS en la nube es opcional; no es el flujo oficial de esta prueba local.

## Comprobación del backend

```powershell
Invoke-RestMethod http://100.24.55.64:8000/health
```

Resultado esperado:

```json
{"ok":true,"gemini_enabled":false,"yolo_enabled":true,"yolo_available":true}
```
