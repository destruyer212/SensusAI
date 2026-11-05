# Sensus AI Mobile

Frontend movil de Sensus AI construido con React Native y Expo Go.

El frontend no contiene la inteligencia principal. Solo:

- Abre la camara.
- Captura una imagen.
- Envia la imagen al backend.
- Lee en voz alta la respuesta del backend.

## Ejecutar

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend"
npm install
npm start
```

Luego escanea el QR con Expo Go.

## Importante para celular fisico

En un celular real, `localhost` apunta al celular, no a la PC. Cambia `apiBaseUrl` en `app.json` por la IP de tu computadora en la red local:

```json
"apiBaseUrl": "http://192.168.1.50:8000"
```

El backend debe estar corriendo en:

```text
http://TU_IP_LOCAL:8000
```
