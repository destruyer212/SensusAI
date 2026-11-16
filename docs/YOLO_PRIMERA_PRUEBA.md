# Primera prueba YOLO de Sensus AI

> Autor del proyecto y dueño del código: **Carlos Jesus Ascarate Riega**

## Qué queda listo hoy

1. `POST /api/vision/fast-detect`: YOLO + decisión temporal del `SafetyGovernor`, sin llamar a Gemini.
2. `POST /api/vision/realtime`: YOLO con el mismo gobernador temporal y profundidad opcional.
3. `POST /api/vision/analyze`: ruta semántica opcional con Gemini.
4. `GET /api/vision/capabilities`: indica si cada motor está realmente activo.

La aplicación no debe asumir que YOLO funciona solo porque existe el endpoint. Debe consultar `capabilities`.

## Instalación local del detector

Desde `SensusAI`:

```powershell
python -m pip install -r backend/requirements-yolo.txt
$env:YOLO_ENABLED="true"
$env:YOLO_MODEL_PATH="backend/models/yolo11n.pt"
python backend/app.py
```

La primera ejecución descarga el peso pequeño si la librería lo necesita. La EC2
actual usa `yolo11n.pt`, con `YOLO_IMAGE_SIZE=320`, Gemini apagado y profundidad
desactivada para conservar memoria.

## Comprobación

```powershell
Invoke-RestMethod http://localhost:8000/api/vision/capabilities
```

Antes de instalar YOLO debe decir `available: false`; después de instalarlo y activar la variable, `dependency_installed` y `available` deben ser `true`.

## Prueba controlada de hoy

- Mochila, silla, mesa, persona y puerta.
- Objeto centrado que crece al acercarse.
- Objeto lateral que no debe ordenar detenerse.
- Escena sin detecciones.
- Repetición: una alerta no se repite en cada frame.
- Confianza baja: se comunica incertidumbre.

La primera prueba se hace con acompañante, sin escaleras, tráfico ni bordes. Esto es asistencia experimental, no un sistema certificado para evitar accidentes.
