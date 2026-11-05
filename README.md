# Sensus AI

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

Plataforma de inteligencia espacial asistida para ayudar a personas ciegas o con baja vision a entender su entorno mediante camara, voz, reglas de seguridad y mapas interiores.

> Estado actual: prototipo controlado para oficina y universidad. No reemplaza baston, perro guia, acompanante ni sistemas oficiales de seguridad.

## Que hace

Sensus AI puede:

- Describir lo importante que aparece delante de la camara.
- Detectar obstaculos, riesgos y caminos bloqueados.
- Buscar objetos, por ejemplo llaves.
- Interpretar comandos como `Sensus quiero ir al bano`.
- Guiar hacia destinos conocidos mediante QR, puntos de referencia y mapas internos.
- Leer respuestas por voz y mostrar detecciones en pantalla para depuracion.
- Reducir costo y latencia con analisis adaptativo, evitando consultar la IA en cada instante.

## Arquitectura en una frase

El backend es el cerebro y el frontend es un cliente reemplazable.

```text
Camara / voz / QR
        |
        v
Frontend React Native + Expo
        |
        v
Backend FastAPI
  |             |
  v             v
Vision IA     Spatial Core / Command Core
  |
  v
Respuesta corta para voz, vibracion e interfaz
```

Esto permite cambiar Expo por una app nativa, gafas u otro dispositivo sin rehacer la logica principal.

## Estructura

```text
SensusAI/
  backend/       API FastAPI, IA visual, comandos y rutas espaciales
  frontend/      App React Native + Expo Go
  docs/          Contratos, arquitectura, seguridad y guias operativas
  contexto/      Contexto maestro para desarrolladores e IAs
  .env.example   Variables de entorno de referencia
```

## Empezar rapido

### Backend

```powershell
cd "C:\proyecto para ciegos app\SensusAI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
python backend\app.py
```

Comprueba `http://localhost:8000/health`. La documentacion interactiva esta en `http://localhost:8000/docs`.

### Frontend

En otra terminal:

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend"
npm install
npx expo start
```

En `frontend/.env`, configura la URL del backend. En un celular fisico no uses `localhost`; usa la IP de la PC en la misma red o una URL HTTPS de tunel.

```text
EXPO_PUBLIC_API_BASE_URL=http://TU_IP_LOCAL:8000
```

### Gemini

La llave vive solo en el `.env` del backend y nunca debe entrar al frontend ni a GitHub.

```text
GEMINI_API_KEY=TU_API_KEY
```

Sin llave, el backend puede funcionar en modo demo segun la configuracion actual.

## Endpoints principales

```text
GET  /health
POST /api/vision/analyze
POST /api/command/interpret
GET  /api/spatial/sites
POST /api/spatial/qr
GET  /api/spatial/sites/{site_id}/destinations
POST /api/spatial/route
POST /api/spatial/emergency
```

## Como continuar el trabajo

Lee primero [la guia rapida del equipo](docs/GUIA_RAPIDA_EQUIPO.md). Para cambios que afecten arquitectura, IA o seguridad, lee tambien [el contexto maestro](contexto/CONTEXTO_MAESTRO.md).

Documentos clave:

- [Autoria y propiedad](docs/AUTORIA_Y_PROPIEDAD.md): autor y dueño del codigo del proyecto.
- [Guia rapida del equipo](docs/GUIA_RAPIDA_EQUIPO.md): entrada para nuevos colaboradores.
- [Plan maestro](docs/PLAN_MAESTRO.md): avance real, fases y prioridades.
- [Carpeta Ing. Mendoza](ing_mendoza/README.md): guia de incorporacion y tareas de la siguiente etapa.
- [Contexto maestro](contexto/CONTEXTO_MAESTRO.md): mision, limites y reglas permanentes.
- [Contrato de API](docs/API_CONTRACT.md): formato de peticiones y respuestas.
- [Stack tecnologico](docs/STACK_TECNOLOGICO.md): tecnologias y responsabilidades.
- [Safety Governor](docs/SAFETY_GOVERNOR_V1.md): costo, frecuencia, repeticion y alertas.
- [Comandos de voz](docs/VOICE_COMMANDS.md): arquitectura de comandos tipo `Sensus quiero ir al bano`.
- [Estrategia de costo](docs/ESTRATEGIA_COSTO_MINIMO_TIEMPO_REAL.md): tiempo real sin consultar Gemini todo el tiempo.
- [Pruebas en celular y APK](docs/PROBAR_EN_CELULAR_Y_APK.md): Expo Go y compilacion movil.

## Reglas de producto

Sensus AI debe hablar poco, claro y con honestidad. Ejemplos validos:

- `Puerta al frente, a unos tres metros.`
- `Hay una mochila cerca. Reduce la velocidad.`
- `Camino libre al frente.`
- `No estoy seguro. Detente y verifica.`

Nunca debe afirmar que un camino es seguro si la evidencia no alcanza. En una emergencia debe priorizar detenerse, pedir ayuda y usar los canales humanos disponibles.

## Privacidad y seguridad

- No guardar imagenes ni audio por defecto.
- No incluir llaves API en el repositorio.
- Probar primero en espacios controlados y con supervision.
- No usar el prototipo para cruces de calle, vehiculos, escaleras peligrosas o decisiones criticas.
- Informar claramente cuando una imagen se envia al backend.
