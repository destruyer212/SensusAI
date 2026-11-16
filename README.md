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

## Arquitectura actual

El backend es el cerebro y el frontend es un cliente reemplazable.

```text
Camara / voz / QR
        |
        v
Frontend React Native con módulos Expo, distribuido como APK Android independiente
        |
        v
AWS EC2 m7i-flex.large — Sensus AI YOLO + Depth
  |
  +--> FastAPI + YOLO11n + Safety Governor
  +--> Spatial Core / Command Core
  +--> Depth Anything V2 Metric Indoor Small (distancia monocular aproximada)
  |
  v
Respuesta corta para voz, vibración y alerta visual
```

El APK actual usa YOLO como motor principal. Gemini está desactivado en la instancia
de prueba para reducir latencia, consumo y dependencia de una API externa. La
profundidad monocular queda disponible en el código, pero requiere más memoria y
calibración para producir distancias confiables.

### Backend de prueba activo

```text
Nombre EC2: sensus-ai-yolo-depth
Tipo: m7i-flex.large (2 vCPU, 8 GiB RAM + swap)
API: http://100.24.55.64:8000
Health: http://100.24.55.64:8000/health
Docs: http://100.24.55.64:8000/docs
Instancia: i-0fdbf603d2f1c6c0e
YOLO: activo
Gemini: apagado
Depth Anything: activo en EC2 (CPU; distancia monocular aproximada)
```

Perfil de inferencia activo: YOLO a tamaño 640 con hasta 30 detecciones y Depth
Anything a tamaño 448 con hasta 20 objetos. Es la configuración de mayor calidad
que dejamos para esta instancia CPU; puede aumentar la latencia por imagen. La
app sigue usando análisis temporal para no saturar el teléfono ni la API.

La IP es temporal. Para una versión estable se debe usar Elastic IP o un dominio
con HTTPS.

El precio observado para `m7i-flex.large` es aproximadamente US$0.0958 por hora,
unos US$16.09 por 168 horas de una semana, sin contar pequeñas variaciones de
EBS, red o impuestos. AWS aplica primero los créditos disponibles; si se agotan,
el uso posterior puede cobrarse según el plan de la cuenta.

## Estructura

```text
SensusAI/
  backend/       API FastAPI, IA visual, comandos y rutas espaciales
  frontend/      App React Native para APK Android (Expo Go no requerido)
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

### APK Android

En otra terminal:

```powershell
cd "C:\proyecto para ciegos app\SensusAI\frontend\android"
.\gradlew.bat assembleRelease
```

El APK se conecta al backend YOLO de AWS. Expo Go no es necesario.

```text
EXPO_PUBLIC_API_BASE_URL=http://100.24.55.64:8000
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
GET  /api/vision/capabilities
POST /api/vision/fast-detect
POST /api/vision/realtime
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
- [Flujo oficial Android APK + YOLO](docs/FLUJO_ANDROID_APK_YOLO.md): compilacion local, entorno confirmado y conexion con AWS.
- [Historial de cambios](docs/CHANGELOG.md): cambios recientes, correcciones y despliegues.

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
