# Contexto maestro de Sensus AI

## Nombre del software

**Sensus AI**

## Definicion

Sensus AI es una plataforma de inteligencia espacial asistida. Su objetivo es ayudar a personas ciegas o con baja vision a interpretar el entorno usando camaras, voz y backend con IA.

No es solo una app. Debe pensarse como una arquitectura: celular primero, luego otros clientes como gafas, camaras externas, dispositivos portables o integraciones empresariales.

## Idea principal de arquitectura

El backend es el cerebro.

El frontend solo debe:

- Capturar imagenes o datos del sensor.
- Enviar la informacion al backend.
- Recibir una respuesta estructurada.
- Presentarla al usuario por voz, vibracion o interfaz.

Esto permite cambiar de frontend sin rehacer la inteligencia principal.

## Problema que queremos resolver

Una persona ciega puede necesitar apoyo para:

- Saber que hay delante.
- Detectar si el camino esta libre o bloqueado.
- Encontrar una puerta, bano, aula, salida u objeto.
- Reconocer obstaculos cercanos.
- Entender un espacio publico o privado.
- Saber cuando la IA no esta segura y debe pedir ayuda.

## Usuario principal

Personas ciegas o con baja vision que necesitan orientacion auditiva en espacios controlados.

Tambien puede servir para:

- Universidades.
- Centros empresariales.
- Hospitales.
- Oficinas.
- Familias.
- Equipos de accesibilidad.
- Investigacion de dispositivos asistivos.

## Regla principal de seguridad

Sensus AI no debe fingir certeza.

Si la IA no esta segura, debe decir:

```text
No estoy seguro. Detente y verifica.
```

Sensus AI no reemplaza baston, perro guia, acompanante, criterio humano ni sistemas oficiales de seguridad.

## Etapa actual

Prototipo controlado.

Esto significa:

- Pruebas en habitacion, pasillo o zona conocida.
- Persona supervisora.
- Sin cruces de calle.
- Sin vehiculos.
- Sin escaleras peligrosas.
- Sin decisiones criticas.
- Objetos grandes y conocidos.

## Arquitectura actual

```text
SensusAI/
  backend/
  frontend/
  docs/
  contexto/
```

### Backend

Tecnologia:

- Python.
- FastAPI.
- Uvicorn.
- Gemini opcional.

Responsabilidades:

- Recibir imagenes.
- Validar tipo de archivo.
- Limitar tamano.
- Ejecutar analisis de IA.
- Aplicar reglas de seguridad.
- Responder frases cortas para audio.
- Mantener contrato estable para cualquier frontend.

Endpoint principal:

```text
POST /api/vision/analyze
```

### Frontend

Tecnologia actual:

- React Native.
- Expo Go.
- Expo Camera.
- Expo Speech.

Responsabilidades:

- Pedir permiso de camara.
- Capturar imagenes.
- Enviar imagen al backend.
- Leer la respuesta en voz alta.
- Permitir lectura manual y modo tiempo real.

El frontend no debe inventar respuestas ni contener la inteligencia principal.

## Prompt base de IA visual

```text
Eres Sensus AI, un sistema de inteligencia espacial asistida para una prueba controlada con una persona ciega.
Responde en espanol latino, con frases cortas y utiles para audio.
Describe solo lo importante para orientacion segura: objetos, personas, puertas, caminos libres,
obstaculos cercanos, texto visible y ubicacion relativa aproximada.
No inventes. Si no estas seguro, dilo claramente.
No des instrucciones peligrosas. Si ves riesgo, recomienda detenerse y pedir ayuda.
Maximo 3 frases.
```

## Como debe hablar

Bueno:

- "Puerta al frente, a unos tres metros."
- "Hay una silla a la derecha."
- "Objeto en el suelo cerca. Detente."
- "Camino libre al frente."
- "No estoy seguro. Detente y pide ayuda."

Malo:

- "Definitivamente no hay peligro."
- "Cruza ahora."
- "Avanza rapido."
- "La escena contiene elementos posiblemente relevantes."

## Prioridades de deteccion

1. Riesgos cercanos.
2. Camino libre o bloqueado.
3. Puertas, salidas y banos.
4. Personas.
5. Objetos buscados por el usuario.
6. Texto de letreros.
7. Ubicacion relativa: frente, izquierda, derecha, cerca, lejos.

## Privacidad

La camara puede capturar rostros, pantallas, documentos, aulas o casas.

Reglas:

- No guardar imagenes por defecto.
- No registrar audio por defecto.
- Avisar si se envia imagen al backend.
- Pedir permisos para pruebas reales.
- Evitar datos sensibles cuando sea posible.

## Estrategia tecnica

Para el prototipo:

- Frontend Expo Go.
- Backend FastAPI.
- Gemini desde servidor.
- Modo demo sin API key.
- Spatial Core con QR, mapas internos y rutas para reducir costos.
- IA visual solo bajo demanda o cada pocos segundos, no video continuo.

Para version mas fuerte:

- Modelo local pequeno para alertas rapidas.
- Servidor para vision compleja.
- Rutas interiores con mapas o marcadores.
- QR, beacons Bluetooth o puntos de referencia.
- Registro de errores para mejorar.

Para gafas:

- Las gafas no deben cargar toda la IA al inicio.
- Camara ligera.
- Celular como puente.
- Backend como cerebro.
- Audio al usuario.

## Estrategia de costo minimo

Sensus AI debe sentirse en tiempo real sin gastar IA pesada todo el tiempo.

La estrategia oficial esta documentada en:

```text
docs/ESTRATEGIA_COSTO_MINIMO_TIEMPO_REAL.md
```

Principios:

- QR y mapa interno primero.
- IA visual solo cuando aporte valor.
- Backend como cerebro.
- Frontend como cliente reemplazable.
- Modo emergencia con frases cortas y rutas seguras.

## Contrato mental para futuras IAs

Antes de modificar el proyecto:

1. Lee este archivo.
2. Manten el backend como fuente de verdad.
3. Manten el frontend reemplazable.
4. Prioriza seguridad sobre apariencia.
5. Responde con frases aptas para audio.
6. No prometas certeza si la IA no la tiene.

La mision de Sensus AI es construir tecnologia seria, clara y segura para asistencia espacial.
