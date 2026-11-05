# Comandos de voz en Sensus AI

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

## Objetivo final

El usuario no debe depender de botones pequenos.

Flujo ideal:

```text
Usuario: "Sensus"
Sensus: "Si, que necesitas?"
Usuario: "Quiero ir al bano"
Sensus: calcula ruta o pide ubicacion por QR.
```

Otros ejemplos:

```text
Sensus, quiero buscar mis llaves.
Sensus, que hay delante?
Sensus, emergencia.
```

## Estado actual

Expo Go sirve para probar rapido, pero no es ideal para wake word real siempre escuchando.

Por eso se implemento primero:

- `Command Core` en backend.
- Endpoint `POST /api/command/interpret`.
- Botones de simulacion en frontend:
  - `Sensus bano`
  - `Sensus llaves`
  - `Sensus ayuda`

Esto prueba la logica sin depender todavia del microfono.

## Endpoint

```http
POST /api/command/interpret
Content-Type: application/json
```

Entrada:

```json
{
  "text": "Sensus quiero ir al bano",
  "site_id": "office_demo",
  "landmark_id": "office_entrance"
}
```

Salida:

```json
{
  "intent": "route",
  "task": "navigation",
  "text": "Te ayudo a ir al bano. Necesito tu ubicacion actual por QR o punto conocido.",
  "requires_camera": false,
  "requires_route": true,
  "destination_id": "office_mens_bathroom"
}
```

## Version real con voz

Para voz real hay tres piezas:

1. Wake word:
   - Detectar "Sensus".
   - Debe funcionar con bajo consumo.
   - Normalmente requiere modulo nativo.

2. Speech-to-text:
   - Convertir "quiero ir al bano" a texto.
   - Puede ser nativo o por servidor.

3. Command Core:
   - Interpretar texto.
   - Ejecutar ruta, busqueda, emergencia o lectura de entorno.

## Decision tecnica

Para prototipo:

```text
Expo Go + botones simulados de comando.
```

Para version seria:

```text
Build nativa con EAS + wake word + speech-to-text.
```

El backend ya esta preparado para recibir el texto reconocido.
