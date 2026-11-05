# Plan maestro de Sensus AI

Este es el mapa de trabajo del proyecto. La prioridad es seguridad, utilidad para una persona ciega y una arquitectura que pueda crecer desde el celular hacia gafas u otros dispositivos.

## Estado actual

### Ya elaborado

- Estructura unica de proyecto con `backend`, `frontend`, `docs` y `contexto`.
- API FastAPI funcionando con `/health` y documentacion OpenAPI.
- Integracion de Gemini Vision desde el backend.
- Modo demo cuando no hay llave de Gemini.
- Validacion de imagen y respuestas cortas para lectura por voz.
- Spatial Core con sitios, puntos de referencia, QR, destinos y rutas demo.
- Command Core para intenciones como buscar llaves, ir al bano, analizar escena y emergencia.
- Frontend React Native + Expo con camara, permisos, lectura por voz, vibracion y visor de depuracion.
- Modo tiempo real con intervalos adaptativos, control de solicitudes simultaneas y supresion de repeticiones.
- Configuracion para probar en red local o mediante tunel HTTPS temporal.
- Documentacion de arquitectura, contrato API, seguridad, costo y comandos de voz.
- Repositorio GitHub con `.env` excluido y `.env.example` publicado.

### Parcial o pendiente

- Reconocimiento real de la palabra de activacion `Sensus`.
- Reconocimiento de voz permanente en una compilacion nativa; Expo Go solo sirve para validar el flujo inicial.
- Mapa real de la universidad, pisos, banos, salidas, ascensores y rutas accesibles.
- Dataset propio de objetos y riesgos del entorno real.
- Detector YOLO integrado y evaluado junto a Gemini.
- Pruebas con personas ciegas y protocolo de consentimiento, privacidad y reporte de incidentes.
- Persistencia de sesiones, metricas de latencia y trazabilidad sin guardar imagenes por defecto.
- Build Android instalable y posterior preparacion para gafas.

## Fases

### Fase 0: base controlada, actual

Objetivo: que el prototipo sea reproducible en una oficina o habitacion.

- Mantener backend y Expo arrancables desde una guia unica.
- Probar camara, permisos, voz, Gemini y comandos simulados.
- Validar respuestas `clear`, `notice`, `caution`, `danger` y `unknown`.
- Registrar errores tecnicos y nunca probar situaciones de riesgo.

### Fase 1: inteligencia hibrida Gemini + YOLO

Objetivo: responder mas rapido y gastar menos consultas de Gemini.

1. Definir clases iniciales: persona, puerta, mochila, silla, obstaculo, escalon, baranda, senal y objeto buscado.
2. Crear un servicio `object_detector` con una interfaz estable independiente del modelo.
3. Integrar YOLO primero en modo observacion, sin dar instrucciones autonomas.
4. Comparar YOLO y Gemini sobre el mismo conjunto de imagenes.
5. Usar reglas de confianza y distancia aproximada para alertas.
6. Enviar a Gemini solo escenas nuevas, ambiguas o solicitadas por el usuario.
7. Medir precision, falsos negativos, latencia, memoria, bateria y costo.

### Fase 2: universidad piloto

Objetivo: orientar en un espacio conocido con supervision.

- Levantar mapa por pisos y zonas.
- Identificar QR o marcadores en entradas, cruces, ascensores y banos.
- Definir rutas accesibles y puntos de reubicacion.
- Probar oficina, pasillo y bano antes de ampliar el recorrido.
- Crear una matriz de peligros por zona y horario.

### Fase 3: voz natural y experiencia accesible

Objetivo: que la persona pueda decir `Sensus, ayudame a ir al bano` sin buscar botones.

- Incorporar reconocimiento de voz en build nativa.
- Implementar activacion por palabra clave con consumo controlado.
- Permitir cancelar, repetir, pausar y pedir emergencia por voz.
- Mantener botones grandes como respaldo, no como flujo principal.

### Fase 4: pruebas humanas y Android

Objetivo: evaluar utilidad real de forma responsable.

- Preparar consentimiento y protocolo de prueba.
- Probar con personas ciegas o con baja vision acompañadas por un responsable.
- Medir comprension, tiempo de orientacion, errores y falsas alarmas.
- Corregir antes de ampliar el area de prueba.
- Generar APK de prueba con configuracion segura y sin secretos incluidos.

### Fase 5: dispositivos portables

Objetivo: preparar gafas o camaras externas.

- Mantener el backend independiente del cliente.
- Evaluar telefono como puente de conectividad y audio.
- Reducir peso de imagenes y frecuencia de subida.
- Investigar inferencia local o servidor privado segun costo y privacidad.

## Criterios de avance

No se pasa de fase por entusiasmo. Se avanza cuando:

- El flujo anterior funciona de forma repetible.
- Los errores conocidos estan documentados.
- No hay secretos en GitHub.
- Las alertas peligrosas priorizan detenerse y verificar.
- Una persona responsable puede reproducir la prueba.

## Orden inmediato de trabajo

1. Mantener Gemini como referencia y congelar un conjunto pequeno de pruebas.
2. Implementar la interfaz de detector en backend sin acoplarla a YOLO.
3. Preparar imagenes anonimizadas y etiquetas del entorno controlado.
4. Integrar YOLO en modo paralelo y comparar resultados.
5. Activar alertas YOLO solo con umbrales conservadores.
6. Recién despues llevarlo al mapa real de la universidad.
