# Sensus AI Mobile

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

Frontend movil de Sensus AI construido con React Native y modulos Expo, distribuido como APK Android independiente. Expo Go no es parte del flujo oficial.

El frontend no contiene la inteligencia principal. Solo:

- Abre la camara.
- Captura una imagen.
- Envia la imagen al backend.
- Lee en voz alta la respuesta del backend.

## Compilar APK Android local

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend\android"
.\gradlew.bat assembleRelease
```

El APK queda en `android/app/build/outputs/apk/release/app-release.apk` y usa el backend YOLO de AWS.

## Importante para celular fisico

La app ya está configurada para usar la API pública de AWS:

```json
"apiBaseUrl": "http://35.153.208.142:8000"
```

El backend debe estar corriendo en:

```text
http://35.153.208.142:8000
```
