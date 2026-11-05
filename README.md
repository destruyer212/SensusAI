# Sensus AI

Sensus AI es una plataforma de inteligencia espacial asistida para ayudar a personas ciegas o con baja vision a interpretar su entorno mediante camara, voz y backend con IA.

La arquitectura esta pensada para que el frontend sea reemplazable: hoy Expo Go en celular, luego una app nativa, gafas, camaras externas u otros dispositivos. El backend es el cerebro del sistema.

## Estructura

```text
SensusAI/
  backend/    API Python/FastAPI con IA, validaciones y reglas de seguridad
  frontend/   App movil React Native + Expo Go
  docs/       Plan tecnico, contrato API y pruebas
  contexto/   Contexto maestro para IA y desarrolladores
```

Antes de pedirle cambios a una IA o a otro desarrollador, leer:

```text
contexto/CONTEXTO_MAESTRO.md
```

## Backend

El backend expone la API y concentra toda la logica importante:

- Validacion de imagenes.
- Limite de carga.
- Prompt seguro.
- Integracion opcional con Gemini.
- Modo demo si no hay API key.
- Respuestas cortas para audio.

Configura variables en:

```text
.env
```

Ejecutar:

```powershell
cd "C:\proyecto para ciegos app\SensusAI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python backend\app.py
```

API:

```text
GET  /health
POST /api/vision/analyze
```

Documentacion interactiva:

```text
http://localhost:8000/docs
```

## Frontend movil

El frontend esta hecho con React Native y Expo Go.

Configura la URL de la API en:

```text
frontend/.env
```

Ejecutar:

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend"
npm install
npm start
```

Para celular fisico, cambia en `frontend/.env`:

```text
EXPO_PUBLIC_API_BASE_URL=http://TU_IP_LOCAL:8000
```

No uses `localhost` desde el celular, porque apuntara al propio celular.

## Activar Gemini

En PowerShell:

```powershell
$env:GEMINI_API_KEY="TU_API_KEY"
python backend\app.py
```

## Principio de producto

Sensus AI debe hablar poco, claro y con honestidad:

- "Puerta al frente, a unos tres metros."
- "Objeto en el suelo cerca. Detente."
- "Camino libre al frente."
- "No estoy seguro. Detente y verifica."

Si la IA no esta segura, debe decirlo.

## Documentos clave

- `contexto/CONTEXTO_MAESTRO.md`: mision, reglas y arquitectura.
- `docs/STACK_TECNOLOGICO.md`: stack tecnologico.
- `docs/API_CONTRACT.md`: contrato de API.
- `docs/ESTRATEGIA_COSTO_MINIMO_TIEMPO_REAL.md`: estrategia para tiempo real barato con QR, mapa interno y Spatial Core.
- `docs/CHECKLIST_ANTES_DE_PROBAR.md`: pasos antes de probar con celular o en entorno real.
- `docs/PROBAR_EN_CELULAR_Y_APK.md`: guia para probar con Expo Go y generar APK.
- `docs/SAFETY_GOVERNOR_V1.md`: logica para tiempo real, costo, repeticion y alertas.
- `docs/VOICE_COMMANDS.md`: arquitectura de comandos tipo "Sensus quiero ir al bano".
