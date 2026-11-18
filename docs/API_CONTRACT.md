# Contrato de API de Sensus AI

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

El frontend y futuros dispositivos solo deben consumir el backend. La inteligencia, validaciones y reglas de seguridad viven en la API.

## Salud

```http
GET /health
```

Respuesta:

```json
{
  "ok": true,
  "app": "Sensus AI",
  "gemini_enabled": false,
  "yolo_enabled": true,
  "yolo_available": true,
  "webrtc_available": true
}
```

## Video continuo en tiempo real (WebRTC)

Permite transmitir video continuo desde la camara mediante WebRTC (UDP/SRTP) sin enviar fotogramas individuales por HTTP.

### Negociar conexion (Señalizacion)

```http
POST /api/webrtc/offer
Content-Type: application/json
```

Entrada:

```json
{
  "sdp": "v=0...",
  "type": "offer",
  "session_id": "mobile-123"
}
```

Salida:

```json
{
  "sdp": "v=0...",
  "type": "answer"
}
```

### Canal de datos (RTCDataChannel: `sensus-alerts`)

Las alertas y detecciones de YOLO se envian al vuelo de vuelta a la aplicacion movil a traves del DataChannel:

```json
{
  "mode": "hybrid",
  "risk_level": "caution",
  "text": "Hay una silla cerca. Reduce la velocidad.",
  "detections": [
    {
      "label": "chair",
      "confidence": 0.88,
      "distance_m": 1.2,
      "position": "al frente"
    }
  ],
  "action": "caution"
}
```

## Analizar escena (Modo foto / snapshot individual)

```http
POST /api/vision/analyze
Content-Type: multipart/form-data
```

Campo:

```text
image: archivo de imagen
```

Respuesta:

```json
{
  "mode": "gemini",
  "text": "Puerta al frente. Hay una silla a la derecha. Avanza despacio.",
  "confidence": "model_estimate"
}
```

## Reglas

- El backend responde frases cortas para audio.
- Si no hay seguridad, debe decir que no esta seguro.
- El frontend no debe inventar respuestas.
- Otros dispositivos, como gafas, deben usar el mismo contrato.

## Spatial Core

Spatial Core permite orientar sin gastar IA visual.

### Listar lugares

```http
GET /api/spatial/sites
```

## Command Core

Interpreta comandos tipo "Sensus quiero ir al bano".

```http
POST /api/command/interpret
Content-Type: application/json
```

Entrada:

```json
{
  "text": "Sensus quiero buscar mis llaves",
  "site_id": "office_demo",
  "landmark_id": "office_entrance"
}
```

Salida:

```json
{
  "intent": "find_object",
  "task": "find_keys",
  "text": "Buscando llaves. Apunta lentamente al suelo, mesa y superficies cercanas.",
  "requires_camera": true,
  "requires_route": false,
  "destination_id": null
}
```

### Resolver QR

```http
POST /api/spatial/qr
Content-Type: application/json
```

Entrada:

```json
{
  "qr_code": "SENSUS:office_demo:office_entrance"
}
```

Salida:

```json
{
  "site": {
    "id": "office_demo",
    "name": "Oficina piloto",
    "type": "office"
  },
  "landmark": {
    "id": "office_entrance",
    "name": "Entrada principal de oficina",
    "floor": 1,
    "kind": "entrance",
    "spoken": "Estas en la entrada principal de la oficina."
  },
  "text": "Estas en la entrada principal de la oficina."
}
```

### Calcular ruta

```http
POST /api/spatial/route
Content-Type: application/json
```

Entrada:

```json
{
  "site_id": "office_demo",
  "from_landmark_id": "office_entrance",
  "destination_id": "office_mens_bathroom"
}
```

### Emergencia

```http
POST /api/spatial/emergency
Content-Type: application/json
```

Entrada:

```json
{
  "site_id": "office_demo",
  "from_landmark_id": "office_entrance"
}
```
