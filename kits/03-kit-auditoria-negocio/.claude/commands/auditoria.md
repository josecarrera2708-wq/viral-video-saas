---
description: Audita un negocio por fuera y por dentro, y genera el informe ejecutivo
---

Lanza una auditoría de negocio nueva usando la skill `auditoria-negocio`.

Antes de investigar nada:

1. **Determina el alcance** (Paso 0 de la skill) y dilo en una línea. Mira si hay
   algún formulario relleno en `entrada/` y si el usuario ha dado una web:
   - web + formulario → **auditoría completa**, con el cruce del Paso 9
   - solo web → **solo por fuera**; ofrece el formulario de `formulario/` una vez,
     en una línea, y sigue
   - solo formulario → **solo por dentro**; pregunta si tiene su web para
     completar la otra mitad
2. Si el usuario ha escrito una URL o un nombre de negocio junto al comando, dalo
   por recibido y no lo vuelvas a preguntar. Si no ha escrito nada y tampoco hay
   nada en `entrada/`, pregunta qué negocio se audita — una URL, o el nombre y la
   ciudad si no tiene web.
3. Si hay algo en `entrada/`, haz **primero** la revisión de privacidad del Paso 2
   de la skill: si aparecen datos de los clientes de ese negocio, contraseñas o
   accesos, párate y pide que se quiten antes de seguir.
4. Sigue con los dos bloques de preguntas de contexto del Paso 1A (lo básico ·
   contexto estratégico), agrupados en dos mensajes, no de uno en uno.

Después ejecuta la skill completa: investigar por fuera, puntuar las 11 dimensiones
con evidencia, puntuar las 8 áreas de madurez con citas del formulario, calcular
las horas y el coste con los datos declarados, **cruzar las dos mitades**, generar
los dos mapas, montar el informe HTML en `workspace/` y presentarlo con las dos
cifras.

Si el usuario quiere probar el kit sin gastar en un negocio real, dile que escriba
*"audita el negocio de ejemplo"*: la peluquería ficticia de
`ejemplos/negocio-de-practica/`, que trae web, datos públicos y formulario relleno,
así que sale una auditoría completa (Paso 0 de la skill).
