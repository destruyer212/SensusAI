# Estado actual y tareas para Ing. Mendoza

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

## Donde estamos

Sensus AI ya tiene un prototipo funcional en celular:

- Frontend React Native + Expo.
- Camara con permisos y visor visible.
- Captura y subida multipart hacia FastAPI.
- Backend con Gemini Vision.
- Respuestas cortas y lectura por voz.
- Modo tiempo real con frecuencia adaptativa para reducir costo.
- Spatial Core para QR, sitios, destinos y rutas demo.
- Command Core para interpretar ordenes de voz escritas.
- Manejo de emergencia y estado de riesgo.

## Que falta para cerrar primero el MVP Gemini

1. Validar analisis manual y tiempo real en escenas controladas.
2. Completar el flujo de comandos, respuesta hablada y estados de error.
3. Probar rutas demo con QR y ubicacion conocida.
4. Medir latencia, costo por consulta y calidad de respuesta.
5. Congelar un conjunto de escenas de referencia.

## Que falta despues para una version mas fuerte

1. Integrar un detector YOLO desacoplado del resto del backend.
2. Medir la diferencia entre Gemini, YOLO y el modo hibrido.
3. Definir clases y datos del entorno real.
4. Cambiar el mapa demo por un mapa validado de la universidad.
5. Implementar reconocimiento de voz nativo y palabra clave `Sensus`.
6. Crear pruebas automatizadas para endpoints y reglas de seguridad.
7. Medir latencia, costo, bateria y falsos negativos.

## Primera tarea recomendada

Crear una interfaz de detector con esta idea:

```python
class ObjectDetector:
    def detect(self, image_bytes: bytes) -> list[dict]:
        ...
```

La respuesta debe ser normalizada, por ejemplo:

```json
{
  "label": "mochila",
  "confidence": 0.87,
  "box": {"x": 0.42, "y": 0.58, "width": 0.21, "height": 0.18},
  "source": "yolo"
}
```

Despues se puede agregar `GeminiDetector` y `YoloDetector` sin cambiar el contrato del frontend.

## No hacer todavia

- No eliminar Gemini antes de tener comparacion objetiva.
- No activar YOLO como unica fuente de seguridad sin evaluacion.
- No probar con escaleras, trafico o situaciones de emergencia real.
- No subir imagenes privadas ni llaves API al repositorio.
- No cambiar el contrato de API sin actualizar `docs/API_CONTRACT.md`.
