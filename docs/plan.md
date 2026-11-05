# Plan de desarrollo de Sensus AI

## Objetivo

Crear primero una app de celular con React Native y Expo Go para pruebas controladas. Luego evolucionar hacia otros clientes como gafas, camaras externas o dispositivos de asistencia.

## Principio arquitectonico

El backend es el cerebro.

El frontend solo consume la API. Esto permite cambiar de app movil a gafas o a otro dispositivo sin reescribir la inteligencia.

## Etapa 1: prototipo controlado

Ambiente:

- Una sala, pasillo o zona de universidad conocida.
- Objetos grandes y repetidos.
- Persona supervisora.
- Sin cruces de calle, escaleras abiertas, zonas con vehiculos o decisiones de riesgo.

Funciones minimas:

- Abrir camara en Expo Go.
- Capturar una imagen manualmente.
- Enviar imagen al backend.
- Recibir respuesta corta.
- Leer respuesta por voz.
- Activar modo tiempo real cada pocos segundos.

## Etapa 2: objetos y lugares

Funciones:

- "Busca mi celular."
- "Busca mi mochila."
- "Donde esta la puerta?"
- "Donde esta el bano?"

El backend debe convertir estas intenciones en instrucciones para la IA.

## Etapa 3: mapa privado del lugar

Para una universidad, casa u oficina:

- Crear lista de lugares: entrada, bano, aula, escalera, ascensor, cafeteria.
- Tomar fotos de referencia.
- Usar QR o marcadores visuales si el lugar lo permite.
- Combinar vision con rutas seguras.

## Etapa 4: mejor orientacion

Opciones tecnicas:

- IA visual en servidor para escenas complejas.
- Modelo pequeno local para detecciones rapidas.
- GPS solo para exteriores.
- Bluetooth beacons o QR para interiores.
- Vibracion para alertas urgentes.

## Etapa 5: gafas

Arquitectura recomendada:

- Gafas con camara ligera.
- Celular como puente de red y energia.
- Backend para IA pesada.
- Audio por auricular o conduccion osea.
- Modelo local basico solo para alertas rapidas.

## Riesgos importantes

- Latencia.
- Alucinaciones de IA.
- Bateria.
- Costo de servidor.
- Privacidad.
- Falsa sensacion de seguridad.

## Regla de producto

Sensus AI debe ser honesta:

- Si ve algo, lo dice claro.
- Si no sabe, lo dice.
- Si hay riesgo, pide detenerse.
