# Sensus AI: estado del tiempo real Android

## Qué se corrigió

- La app Android ya no usa `expo-camera`.
- La cámara usa `react-native-vision-camera` y mantiene el preview nativo activo.
- La cámara se configura con `isActive`, `photo` y `video`; el APK se compila con VisionCamera y `react-native-worklets-core` habilitados.
- El modo rápido toma snapshots del preview nativo, en vez de montar/desmontar la cámara para cada análisis.
- Se conserva una sola petición de análisis a la vez y se descartan respuestas tardías.
- La voz ahora tiene cola y prioridad: una alerta de peligro puede adelantar una lectura normal, pero las detecciones normales no se pisan entre sí.

## Importante: qué significa “tiempo real” en esta versión

El sensor de cámara sí está transmitiendo video continuamente al componente nativo. Sin embargo, el YOLO actual todavía corre en el backend y recibe snapshots muestreados del preview. Esto reduce el retraso y evita la captura manual visible, pero todavía no es inferencia YOLO sobre cada frame de cámara.

El flujo actual es:

```text
video nativo VisionCamera
        |
        +-- snapshot muestreado cuando corresponde
                |
                +-- /api/vision/realtime
                        |
                        +-- YOLO + profundidad en AWS
                                |
                                +-- detección/evento + voz priorizada
```

## Lo que falta para el modo videollamada real

Para ejecutar YOLO sobre frames continuos y enviar solo eventos, hay que llevar el modelo al dispositivo o crear un plugin nativo Android que convierta el `Frame` de VisionCamera a tensor y ejecute un modelo TFLite/ONNX. Después se puede enviar únicamente un evento cuando cambie la detección, el riesgo o la distancia.

No se debe afirmar que esto ya está terminado: el backend actual todavía recibe imágenes muestreadas porque esa es la única ruta comprobada con el modelo YOLO de AWS.

## Compilación local

Este equipo tiene Android SDK, Java 17 y Gradle disponibles. El APK release se genera con:

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend\android"
cmd /c gradlew.bat assembleRelease --no-daemon
```

Salida:

```text
frontend/android/app/build/outputs/apk/release/app-release.apk
```

No es Expo Go. Es un APK Android nativo generado desde el proyecto prebuild con módulos nativos enlazados.

