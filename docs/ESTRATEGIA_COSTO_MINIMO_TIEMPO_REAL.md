# Estrategia de costo minimo para tiempo real

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

## Decision principal

Sensus AI debe sentirse en tiempo real, pero no debe enviar video continuo a una IA costosa.

La regla es:

```text
No usar IA pesada todo el tiempo.
Usar mapa, QR, sensores y logica barata primero.
Usar IA visual solo cuando realmente aporte valor.
```

Esto permite probar en universidad y oficina con costo muy bajo, incluso casi cero en las primeras fases.

## Por que no usar IA pesada continua

Enviar muchos frames por segundo a Gemini u otro modelo visual seria:

- Costoso.
- Lento.
- Malo para la bateria.
- Dependiente de internet.
- Riesgoso si la respuesta llega tarde.

Para una persona ciega, una respuesta tarde puede ser peor que una respuesta simple pero rapida.

## Arquitectura de bajo costo

Sensus AI debe funcionar por capas:

1. **Capa gratuita/local**
   - Camara activa.
   - Voz.
   - Botones grandes.
   - QR.
   - Estado actual del usuario.
   - Mapa interno.

2. **Capa barata de backend**
   - Rutas.
   - Pisos.
   - Banos.
   - Ascensores.
   - Salidas.
   - Oficinas.
   - Instrucciones guardadas.

3. **Capa de IA visual**
   - Gemini u otro modelo visual.
   - Solo se activa cuando hace falta.

## Modo tiempo real economico

El modo tiempo real no significa analizar video completo.

Debe funcionar asi:

- Capturar 1 frame cada 4 a 8 segundos.
- Si el usuario esta quieto, analizar menos.
- Si el usuario esta en una ruta conocida, usar mapa antes que IA.
- Si escanea QR, no gastar IA para ubicarlo.
- Si hay duda o peligro, usar IA visual.
- Si el usuario presiona "leer entorno", usar IA visual.

Frecuencias sugeridas:

```text
Modo manual: 1 analisis cuando el usuario toca el boton.
Modo ruta conocida: instrucciones por mapa, sin IA visual constante.
Modo tiempo real normal: 1 frame cada 5 segundos.
Modo duda/peligro: 1 frame cada 3 segundos temporalmente.
Modo quieto: 1 frame cada 8 a 10 segundos.
```

## QR como localizacion barata

Para interiores, GPS no es confiable.

En universidad u oficina, la estrategia inicial debe usar QR en puntos clave:

- Ascensores.
- Entrada de cada piso.
- Cerca de banos.
- Cruces de pasillo.
- Escaleras.
- Oficinas importantes.
- Seguridad.
- Enfermeria.
- Salidas.

Un QR debe indicar algo como:

```json
{
  "site_id": "universidad_principal",
  "building": "torre_a",
  "floor": 7,
  "landmark_id": "ascensor_principal_p7"
}
```

Con eso, Sensus AI sabe donde esta el usuario sin gastar IA visual.

## Spatial Core

El modulo clave del backend sera **Spatial Core**.

Spatial Core es la memoria espacial de Sensus AI.

Debe guardar:

- Lugares.
- Edificios.
- Pisos.
- Soteranos.
- Banos.
- Ascensores.
- Escaleras.
- Salidas.
- Puntos QR.
- Rutas seguras.
- Rutas de emergencia.
- Zonas peligrosas.
- Notas de accesibilidad.

Ejemplo:

```json
{
  "place": "Universidad",
  "building": "Torre principal",
  "floor": 7,
  "current_landmark": "Ascensor principal",
  "destination": "Bano hombres",
  "steps": [
    "Avanza recto por el pasillo.",
    "Mantente a la derecha.",
    "El bano esta despues de la segunda puerta."
  ]
}
```

## Caso universidad

La universidad tiene muchos niveles:

- 16 pisos hacia arriba.
- 5 pisos hacia abajo.

No se debe mapear todo el campus el primer dia.

Plan recomendado:

1. Un solo piso.
2. Ascensor principal.
3. Bano hombres.
4. Bano mujeres.
5. Escalera.
6. Seguridad o punto de ayuda.
7. Una ruta simple de prueba.

Cuando eso funcione, escalar a:

- 3 pisos mas usados.
- Todos los pisos principales.
- Soteranos.
- Rutas de emergencia.

## Caso oficina

La oficina debe ser el laboratorio inicial.

Primera prueba:

- Entrada.
- Pasillo.
- Bano.
- Escritorio.
- Sala.
- Salida.
- 5 a 10 QR.

Objetivo:

```text
Probar orientacion, voz, QR, rutas y modo tiempo real barato antes de llevarlo a la universidad.
```

## Modo emergencia

Sensus AI necesita un modo emergencia de bajo costo y alta claridad.

No debe hablar mucho.

Debe priorizar:

- Detener al usuario si hay duda.
- Ubicar ultimo QR conocido.
- Guiar a punto seguro cercano.
- Mostrar o decir contacto de seguridad.
- Pedir ayuda humana si no hay certeza.

Frases recomendadas:

- "Detente."
- "Estoy buscando la ruta segura mas cercana."
- "Ultima ubicacion conocida: piso 7, ascensor principal."
- "Dirigete a la pared derecha y espera ayuda."
- "No estoy seguro. Pide apoyo cercano."

## Cuando usar IA visual

Usar IA visual solo en estos casos:

- El usuario presiona "leer entorno".
- El usuario esta perdido y no hay QR reciente.
- La ruta indica un cruce o punto confuso.
- Hay posible obstaculo.
- El usuario pregunta por un objeto.
- El sistema detecta baja confianza.
- Modo emergencia requiere confirmar entorno.

## Cuando NO usar IA visual

No usar IA visual si:

- Hay QR reciente y ruta clara.
- El usuario esta siguiendo una instruccion simple.
- El backend ya sabe la ruta.
- El usuario esta quieto y no pidio lectura.
- Solo se necesita repetir la siguiente instruccion.

## Objetivo de costo

Primera version:

```text
Costo casi cero:
QR + mapa interno + voz + backend local.
```

IA visual:

```text
Uso minimo:
solo bajo demanda o cada pocos segundos en modo tiempo real.
```

## Principio humano

Sensus AI existe para ayudar a personas que realmente necesitan apoyo.

La tecnologia debe ser:

- Barata.
- Clara.
- Segura.
- Honesta.
- Facil de probar.
- Posible de escalar.

No se debe construir primero algo caro y perfecto. Se debe construir algo simple, verificable y util en espacios controlados.
