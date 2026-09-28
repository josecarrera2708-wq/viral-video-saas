---
description: Pasa la lista de calidad de espectador a un kit ya hecho y te dice qué falla
---

Revisas un kit con la lista de calidad, como si fueras la persona que lo acaba de
descargar y no sabe nada de él. Es una revisión **de solo lectura**: informas de lo que
falla y preguntas antes de cambiar nada.

## 1 · Qué kit se revisa

La carpeta viene en $ARGUMENTS. Si no viene, lista las carpetas de `mis-kits/` y
pregunta cuál. También vale un kit de fuera de `mis-kits/` si el usuario da la ruta —
pero entonces la revisión es **estrictamente de lectura**: no tocas nada de ese kit sin
permiso explícito.

## 2 · Lee el kit

Lee, en este orden, y apunta las contradicciones a medida que aparecen:
`EMPIEZA-AQUI.md` → `README.md` → `CLAUDE.md` → el `SKILL.md` de cada skill → los
comandos → el `LEEME.md` de `ejemplos/`. Si hay `_CONTRATO.md`, léelo al final: dice qué
prometía el kit y con qué se comparó.

Y lista los archivos de verdad (`ls -R`), porque la mitad de los defectos son rutas
citadas que no existen.

## 3 · Los nueve puntos

Comprueba uno a uno, con ✓ o ✗ y **la prueba al lado**. Nada se marca ✓ de memoria — y
**ningún ✗ se escribe sin comprobarlo dos veces**: buena parte de los ✗ de una primera
pasada son fallos del comprobador (un `grep` que caza una palabra en un ejemplo, una ruta
resuelta desde la carpeta equivocada), no defectos del kit. Un ✗ falso hace que el usuario
estropee algo que funcionaba.

1. **Primer arranque correcto.** ¿Existe `.claude/setup-completado.json`? Si existe, el
   kit está en estado "ya instalado" y quien lo abra verá el menú en vez del asistente.
   ✗ si va a entregarse.
2. **Instalación sin terminal.** Lee el `setup.md`: ¿le pide al usuario en algún momento
   que abra una terminal, que edite un archivo de código o que pegue una clave en el
   chat? Cualquiera de las tres es ✗.
3. **El ejemplo de práctica funciona.** ¿Existe `ejemplos/` con contenido y su
   `LEEME.md`? ¿La skill tiene el paso que lo activa y el `CLAUDE.md` la fila en su
   tabla de decisión? Si el ejemplo depende de internet, dilo: debería funcionar offline.
4. **Reapertura.** ¿El `CLAUDE.md` distingue primer arranque de reapertura, con un
   marcador claro, y tiene menú para la segunda vez?
5. **Se entiende sin ser técnico.** Busca jerga sin traducir (API, endpoint, CDN,
   scraping, JSON, CLI, deploy…). Cada término técnico debería explicarse la primera
   vez. Cita las líneas que fallan.
6. **Los tres documentos cuentan la misma historia.** ¿El README promete algo que la
   skill no hace? ¿Hay nombres de carpetas o de archivos de salida que no coinciden
   entre documentos? Es el defecto más frecuente y el que más confunde al cliente.

   Si el kit puntúa, **compara las dos tablas de dimensiones con un comando**, no
   leyéndolas: extrae nombre y peso del README y de la skill y ponlos uno al lado del
   otro. Una glosa que está en un sitio y no en el otro ("Cláusulas mudas" frente a
   "Cláusulas mudas: lo que no dice") se lee bien en las dos tablas por separado y solo
   salta al compararlas — y llega hasta el informe del cliente.
7. **Cero referencias rotas.** Cada archivo, carpeta y comando citado en los documentos:
   compruébalo con `ls`. Y las skills: ¿está cada `SKILL.md` en su carpeta, con
   frontmatter `name` y `description`?

   **Cada ✗ de este punto se comprueba a mano antes de darlo por defecto**, porque es el
   punto que más falsos positivos produce. Los tres de siempre: lo que **crea el wizard**
   (`setup-completado.json` — que además **no** debe existir todavía), los archivos de
   salida citados por su nombre suelto cuando viven en `workspace/`, y los archivos
   citados por su nombre corto dentro de un árbol dibujado (`datos-publicos.md` por
   `ejemplos/la-carpeta/datos-publicos.md`). Resuelve la ruta completa antes de escribir
   el ✗: si no, el usuario "arregla" documentos que estaban bien.
8. **Qué cuesta usarlo.** ¿El README dice si hace falta una clave de API, una
   suscripción o un gasto? Si el kit no cuesta nada aparte de Claude Code, tiene que
   decirlo también: tranquiliza.
9. **Mac y Windows.** Busca comandos de un solo sistema sin su alternativa (`open`,
   `brew`, `zip`, rutas con `\`). Y rutas absolutas del ordenador de quien lo hizo
   (`grep -r "/Users/"`).

## 4 · Comprobaciones extra que casi siempre destapan algo

- **La descripción de la skill**: ¿dice qué hace, cuándo usarla y las frases exactas que
  diría el usuario? Una descripción de una línea es una skill que no se activa
  (`referencias/skill-que-dispara.md`).
- **`workspace/`**: ¿existe y con su `.gitkeep`? Si además hay resultados dentro,
  **eso solo no es un defecto**: pregunta antes de tocar nada. Un kit que acaba de pasar
  su Paso 7 guarda ahí la única copia comprobada de su prueba, y en el ZIP no viajan de
  todas formas porque `/empaqueta` los excluye. Es ✗ únicamente si el kit **se está
  entregando ya** con ellos dentro.
- **Secretos**: `grep -ri "sk-\|api_key\|password\|token" [kit]` — que no haya ninguna
  clave real escrita en ningún documento. Si aparece una, es lo primero que se dice.
- **Ni modelos ni asistentes externos** (regla absoluta del estándar: el kit funciona con
  el modelo que el usuario ya tiene en Claude Code):
  `grep -rniE "gemini|opencode|kimi|chatgpt|copilot|ollama|deepseek" [kit]`. Lee cada
  línea que salga antes de marcarla — la palabra puede estar en un ejemplo del oficio del
  kit y no ser una dependencia.
- **Si el kit cita fuentes** (contratos, reseñas, textos de una web), ¿lleva escritas en
  la skill las dos reglas de la cita? *La cita se copia, no se reescribe* y *nunca termina
  antes de la condición, la excepción o la consecuencia que la modifica*. Sin ellas, el
  kit produce citas mal cortadas que se leen perfectamente y dicen lo contrario.
- **Marcadores sin sustituir**: busca `[[`, `TODO`, `XXX`, `lorem`.
- **El sistema de medida**, si el kit puntúa: ¿los pesos suman 100? Súmalos. ¿Hay
  anclajes (qué es un 20, un 50, un 80) o solo adjetivos?

## 5 · El informe

En pantalla, corto y ordenado por gravedad:

- **Veredicto en una línea**: listo para entregar / le faltan cosas / tiene un fallo
  grave.
- **Lo que falla**, agrupado en tres montones: **rompe el kit** (no arranca, referencia
  rota, secreto expuesto, viaja instalado) · **confunde al usuario** (documentos que se
  contradicen, jerga, falta el coste) · **detalle** (formato, orden, redacción).
- Para cada fallo: **el archivo y la línea**, y la corrección concreta en una frase.
- **Lo que está bien**, en dos líneas. Si el kit está bien, dilo sin rebajarlo.

Y cierra preguntando: "¿quieres que arregle los [N] fallos que rompen el kit?". No
arregles nada antes de que conteste — y si el kit no es suyo, no lo arregles en absoluto:
dile qué cambiar.
