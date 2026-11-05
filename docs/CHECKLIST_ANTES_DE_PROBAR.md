# Checklist antes de probar Sensus AI

## Estado actual

- Backend FastAPI funcionando.
- `GEMINI_API_KEY` cargada desde `.env`.
- `GEMINI_MODEL=gemini-flash-lite-latest`.
- Endpoint `/health` responde con `gemini_enabled=true`.
- Endpoint `/api/vision/analyze` probado con imagen de prueba.
- Spatial Core inicial creado con oficina piloto y universidad piloto.
- Endpoints de QR, rutas y emergencia disponibles en `/api/spatial`.

## Antes de probar en celular

1. Asegurar que backend este corriendo:

```powershell
cd "C:\proyecto para ciegos app\SensusAI"
.\.venv\Scripts\Activate.ps1
python backend\app.py
```

2. Obtener IP local de la computadora:

```powershell
ipconfig
```

3. Editar `frontend/.env`:

```text
EXPO_PUBLIC_API_BASE_URL=http://TU_IP_LOCAL:8000
```

4. Ejecutar Expo:

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend"
npm start
```

5. Abrir con Expo Go en el celular.

## Antes de probar con una persona

- Probar primero con una persona vidente.
- Probar en una habitacion o pasillo controlado.
- No probar en escaleras, calle, estacionamiento o zonas peligrosas.
- Tener una persona supervisora.
- Usar frases cortas.
- Si la IA falla, detener la prueba.

## Cosas importantes que faltan

- Escaneo QR real desde camara en Expo.
- Rutas reales de oficina medidas en el lugar.
- Rutas reales de universidad por piso.
- Modo emergencia conectado a contactos o seguridad.
- Logs de errores sin guardar imagenes privadas.
- Control de costos y limite de llamadas a Gemini.
- Boton para detener modo tiempo real.
- Configuracion de intervalo de analisis.

## Regla de prueba

Sensus AI nunca debe dar seguridad falsa.

Si no esta seguro:

```text
No estoy seguro. Detente y verifica.
```
