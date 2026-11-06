# Plan de integracion YOLO + Gemini

> Autor del proyecto y dueño del codigo: **Carlos Jesus Ascarate Riega**

## Objetivo

Combinar deteccion rapida local o de bajo costo con razonamiento visual de Gemini desde el backend.

## Reparto de responsabilidades

| Componente | Mejor uso | Restriccion |
| --- | --- | --- |
| YOLO | Objetos conocidos, riesgos frecuentes, deteccion repetida | No explica bien escenas complejas por si solo |
| Gemini | Contexto, lectura, instrucciones cortas y escenas ambiguas | Tiene costo, latencia y depende de red |
| Safety Governor | Decide prioridad, repeticion y nivel de alerta | Nunca debe ocultar incertidumbre |

## Flujo propuesto

```text
Imagen
  |
  v
YOLO rapido
  |
  +--> deteccion clara y repetida: alerta local/backend corta
  |
  +--> escena nueva, ambigua o comando explicito: Gemini
  |
  v
Normalizador de detecciones
  |
  v
Safety Governor
  |
  v
Texto corto + nivel de riesgo + vibracion/interfaz
```

## Fases tecnicas

1. **Hecho hoy:** contrato común de detecciones y `SafetyGovernor` temporal.
2. **Hecho hoy:** `POST /api/vision/fast-detect` y `GET /api/vision/capabilities`.
3. **Hecho hoy:** adaptador YOLO opcional; Gemini sigue en `/api/vision/analyze`.
4. Instalar `backend/requirements-yolo.txt` en el equipo/worker de visión y descargar el modelo pequeño.
5. Ejecutar YOLO en modo sombra y guardar solo métricas anónimas.
6. Comparar detecciones contra un conjunto etiquetado de oficina y universidad.
7. Activar solo clases y umbrales con resultados suficientes.
8. Hacer fallback a Gemini cuando YOLO no tenga confianza o falte contexto.
9. Medir costo, latencia, batería y falsos negativos antes de usarlo con personas.

## Arquitectura ejecutable de la primera prueba

```text
Expo Camera (JPEG pequeño, 2-5 FPS controlados)
          |
          v
POST /api/vision/fast-detect  ---->  YOLO pequeño (worker local)
          |                                  |
          +------------------------> SafetyGovernor
                                             |
                         +-------------------+------------------+
                         |                                      |
                 alerta corta/vibración                 sin alerta repetida
                         |
       comando explícito, objeto desconocido o escena compleja
                         v
              POST /api/vision/analyze -> Gemini
```

`fast-detect` no consume tokens de Gemini. Gemini se consulta por comando de voz, lectura, escena ambigua o cambio importante. No se envía cada frame: el cliente espera respuesta y descarta frames viejos.

YOLO no se instala todavía en el EC2 `t4g.micro`: tiene poca memoria y debe seguir estable con Gemini. La primera inferencia YOLO se hará en el equipo local o en un worker separado.

## Contrato de detección

Cada detección usa coordenadas normalizadas `[x1, y1, x2, y2]` de 0 a 1:

```json
{"label":"mochila","confidence":0.91,"bbox":[0.35,0.52,0.72,0.95]}
```

La distancia es aproximada. Una alerta crítica siempre debe decir "detente" o pedir confirmación; nunca debe prometer que el camino está seguro.

## Criterios de seguridad

- Un objeto no detectado no significa que no exista.
- Para alertas criticas se debe ser conservador y pedir detenerse/verificar.
- La distancia derivada de una caja 2D es aproximada, no una medicion exacta.
- Toda salida debe indicar incertidumbre cuando corresponda.
- YOLO no debe enviar instrucciones autonomas de cruce o desplazamiento peligroso.
