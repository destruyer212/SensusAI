# Contrato de API de Sensus AI

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
  "gemini_enabled": false
}
```

## Analizar escena

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
