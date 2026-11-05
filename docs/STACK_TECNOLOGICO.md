# Stack tecnologico de Sensus AI

## Vision general

Sensus AI usa una arquitectura cliente-servidor.

El backend es el cerebro del sistema. El frontend movil solo captura datos, consume la API y presenta la respuesta al usuario.

## Backend

Tecnologias:

- Python 3.12.
- FastAPI.
- Uvicorn.
- Gemini API para vision con IA.
- python-dotenv para configuracion.
- Multipart upload para recibir imagenes.

Responsabilidades:

- Recibir imagenes desde cualquier cliente.
- Validar archivos.
- Aplicar limites de seguridad.
- Ejecutar el prompt visual.
- Responder texto corto apto para voz.
- Mantener un contrato API estable.

## Frontend movil

Tecnologias:

- React Native.
- Expo Go.
- Expo Camera.
- Expo Speech.
- Expo Constants.

Responsabilidades:

- Pedir permiso de camara.
- Capturar imagenes.
- Enviar imagen al backend.
- Leer respuestas por voz.
- Permitir modo manual y modo tiempo real.

## IA

Primera etapa:

- Gemini desde backend.
- Modo demo si no hay API key.

Futuro:

- Modelos locales pequenos para alertas rapidas.
- Modelos de servidor para escenas complejas.
- Posible RAG/mapas internos para rutas privadas.

## Configuracion

Backend:

```text
.env
```

Frontend:

```text
frontend/.env
```

El frontend no debe tener secretos. Solo puede tener variables publicas como la URL de la API.

## Contrato principal

```http
POST /api/vision/analyze
```

Entrada:

```text
image: archivo de imagen
```

Salida:

```json
{
  "mode": "gemini",
  "text": "Puerta al frente. Hay una silla a la derecha. Avanza despacio.",
  "confidence": "model_estimate"
}
```

## Por que este stack

- Expo Go permite probar rapido en celular.
- FastAPI permite una API clara, documentada y escalable.
- Separar frontend/backend permite cambiar de celular a gafas sin rehacer la IA.
- Gemini permite prototipar vision avanzada sin entrenar un modelo propio al inicio.
