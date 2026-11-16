# Arquitectura del pipeline híbrido

Autor y dueño del código: Carlos Jesus Ascarate Riega.

## Objetivo

Integrar `backend/ProyectoProfundidad` al backend FastAPI existente sin crear
otro servidor ni otro puerto. SensusAI conserva una sola API para Expo y para
futuros dispositivos.

## Flujo

```text
Imagen móvil → /api/vision/realtime → YOLO → Depth Anything
             → Safety Governor → observar / cuidado / detenerse
```

Gemini queda fuera del ciclo de cada frame. Se utiliza en `/api/vision/analyze`
para escenas complejas, búsquedas de objetos y comandos del usuario.

## Endpoints

- `GET /api/vision/capabilities`: informa qué motores están disponibles.
- `POST /api/vision/realtime`: YOLO, profundidad opcional y alertas temporales.
- `POST /api/vision/fast-detect`: ruta rápida existente, sin profundidad.
- `POST /api/vision/analyze`: análisis semántico con Gemini.

## Estado de esta primera integración

- El endpoint híbrido ya está integrado en el backend principal.
- La lógica adaptada incluye distancia por región interna del objeto, posición
  izquierda/frente/derecha y detección de corredor central.
- En la EC2 activa, `DEPTH_ENABLED=true`; en instalaciones pequeñas puede dejarse desactivada.
- Si el modelo de profundidad falla, el pipeline conserva YOLO y no tumba la API.
- `depth_score` conserva la lectura cruda del modelo y `distance_m` aplica la
  calibración configurada.
- Para emitir distancias en metros hay que calibrar cada cámara con medidas reales.

## Activación local

Instalar el perfil opcional en una máquina con memoria suficiente:

```powershell
pip install -r backend/requirements-yolo.txt
```

Después configurar `DEPTH_ENABLED=true`. El modelo se descargará de Hugging
Face al primer arranque.

## Criterio de despliegue

La EC2 activa es `sensus-ai-yolo-depth`, una `m7i-flex.large` con 8 GiB de RAM.
YOLO11n es el motor principal y Depth Anything está activo en CPU con el perfil
de calidad alto (`640/30` para YOLO y `448/20` para profundidad). Gemini está
desactivado para evitar consumo externo. Las distancias son monoculares y deben
calibrarse por cámara antes de usarse como medida exacta.
