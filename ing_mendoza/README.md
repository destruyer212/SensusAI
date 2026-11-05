# Carpeta de trabajo para Ing. Mendoza

Bienvenido al proyecto Sensus AI. Esta carpeta resume donde estamos y que trabajo sigue. El repositorio ya tiene una base funcional; el objetivo ahora es mejorar precision, latencia, costo y pruebas sin romper la arquitectura.

## Lectura en 15 minutos

1. `README.md`: como instalar y arrancar.
2. `docs/GUIA_RAPIDA_EQUIPO.md`: mapa de archivos y prueba minima.
3. `docs/PLAN_MAESTRO.md`: avance, fases y prioridades.
4. `contexto/CONTEXTO_MAESTRO.md`: reglas permanentes del producto.
5. `ing_mendoza/ESTADO_Y_TAREAS.md`: tareas concretas para empezar.
6. `ing_mendoza/PLAN_YOLO_GEMINI.md`: integracion del detector YOLO con Gemini.

## Regla de arquitectura

Gemini y YOLO se integran en el backend. El frontend React Native solo captura, envia, recibe y presenta. No se debe meter la llave de Gemini ni logica critica en el celular.

## Resultado esperado de esta etapa

Un pipeline hibrido en el que YOLO responda rapido a objetos y riesgos frecuentes, mientras Gemini explique escenas complejas o ambiguas. La salida final debe pasar por reglas de seguridad antes de convertirse en voz.
