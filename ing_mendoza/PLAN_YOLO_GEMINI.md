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

1. Definir `ObjectDetector` y un formato comun de detecciones.
2. Crear un adaptador YOLO sin cambiar el endpoint del frontend.
3. Ejecutar YOLO en modo sombra y guardar solo metricas anonimas.
4. Comparar detecciones contra un conjunto etiquetado.
5. Activar solo clases y umbrales con resultados suficientes.
6. Hacer fallback a Gemini cuando YOLO no tenga confianza o falte contexto.
7. Medir costo, latencia, bateria y falsos negativos antes de usarlo en universidad.

## Criterios de seguridad

- Un objeto no detectado no significa que no exista.
- Para alertas criticas se debe ser conservador y pedir detenerse/verificar.
- La distancia derivada de una caja 2D es aproximada, no una medicion exacta.
- Toda salida debe indicar incertidumbre cuando corresponda.
- YOLO no debe enviar instrucciones autonomas de cruce o desplazamiento peligroso.
