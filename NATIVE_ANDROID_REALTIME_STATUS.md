# Sensus AI: estado del tiempo real Android

## Qué se corrigió

- La app Android ya no usa `expo-camera`.
- La cámara usa `react-native-vision-camera` y mantiene el preview nativo activo.
- La cámara se configura con `isActive`, `photo` y `video`; el APK se compila con VisionCamera y `react-native-worklets-core` habilitados.
- El modo tiempo real ya no llama `takeSnapshot()`.
- El `frameProcessor` de VisionCamera recibe frames RGB del stream nativo y los muestrea a 2 FPS para no bloquear la cámara.
- El frame se envía como `application/octet-stream` al endpoint `/api/vision/realtime-frame`; no se usa multipart ni una foto capturada.
- Se conserva una sola petición de análisis a la vez y se descartan respuestas tardías.
- La voz ahora tiene cola y prioridad: una alerta de peligro puede adelantar una lectura normal, pero las detecciones normales no se pisan entre sí.

## Importante: qué significa “tiempo real” en esta versión

El sensor de cámara transmite video continuamente al componente nativo. El YOLO corre en AWS sobre frames RGB muestreados del stream. No se captura una foto ni se abre/cierra la cámara en cada ciclo. El muestreo es deliberado: el backend CPU no puede procesar 30 inferencias por segundo sin una GPU.

El flujo actual es:

```text
video nativo VisionCamera
        |
        +-- frameProcessor RGB @ 2 FPS
                |
                +-- buffer binario /api/vision/realtime-frame
                        |
                        +-- YOLO + profundidad en AWS
                                |
                                +-- detección/evento + voz priorizada
```

## Límite actual de rendimiento

La cámara sí es continua. La inferencia está limitada a aproximadamente 2 FPS por la CPU de la instancia actual y por el costo de transferir buffers RGB. Para 10–30 FPS reales hay dos opciones: ejecutar YOLO TFLite/ONNX dentro del APK, o cambiar AWS a una instancia con GPU. La app ya quedó separada para que el transporte no tenga que cambiar cuando se incorpore inferencia on-device.

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

