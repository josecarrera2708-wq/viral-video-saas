---
description: Empaqueta un kit en un ZIP verificado, listo para entregar a un cliente
---

Preparas un kit para que viaje: lo dejas en estado de primer arranque, lo comprimes y
**compruebas el ZIP descomprimiéndolo**. Sin esa última comprobación no se entrega.

La receta completa, con las dos variantes de sistema, está en
`.claude/skills/creador-de-kits/referencias/empaquetado.md`. Léela antes de empezar.

## 1 · Qué kit y con qué condiciones

La carpeta viene en $ARGUMENTS; si no, lista `mis-kits/` y pregunta cuál.

Después, **dos preguntas en un solo mensaje**:

1. ¿Va con **marca blanca** (sin su nombre, para que el cliente lo sienta suyo) o
   firmado por él?
2. ¿El cliente va a **usar** el kit, o solo va a recibir los resultados? Si solo recibe
   resultados, no hace falta ZIP: se le manda el informe y punto.

## 2 · Revisa antes de comprimir

Pasa el `/revisa` sobre ese kit. Si hay algún fallo del montón "rompe el kit", **para**
y dilo: empaquetar un kit roto es enviarle el problema al cliente. Ofrece arreglarlo
primero.

## 3 · Estado de primer arranque

Es la mitad del trabajo. En orden, y confirmando cada uno con ✓:

- Borra `.claude/setup-completado.json` (si viaja, el cliente verá el menú en vez del
  asistente: es el fallo más común al entregar).
- Vacía `workspace/` dejando solo su `.gitkeep`.
- Borra `.env.local` y `.claude/settings.local.json` si existen. `.env.example` sí viaja.
- Borra los `.DS_Store`.
- Aparta el `_CONTRATO.md`: no viaja. Contiene la lista de errores plantados del ejemplo
  de práctica, y si viaja el ejemplo deja de servir. Se queda en la carpeta del usuario.
- Si es **marca blanca**: busca su nombre, su web y su correo en todo el kit
  (`grep -ri`) y quítalos, incluida la plantilla del informe. Siempre aparecen en un
  sitio que nadie recordaba.
- Busca rutas del ordenador del usuario en la documentación (`grep -r "/Users/"`).
- Y si se usó algún caso real suyo para probar, fuera: solo viaja el ejemplo ficticio.

## 4 · Comprime

Con la receta de `referencias/empaquetado.md`, la variante del sistema del usuario
(`zip -r` con exclusiones en Mac/Linux; copia a carpeta temporal + `Compress-Archive` en
Windows).

La raíz del ZIP es **la carpeta del kit con su número**: al descomprimir tiene que
aparecer `NN-kit-nombre/` y dentro los archivos, nunca los archivos sueltos.

## 5 · Verifica descomprimiendo

Obligatorio. Descomprime en una carpeta temporal, lista el contenido, compara con
`diff -r` contra el original y comprueba:

- Aparece una sola carpeta, con su número.
- Están `EMPIEZA-AQUI.md`, `README.md`, `CLAUDE.md`, `.claude/settings.json`,
  `.claude/commands/setup.md`, el `SKILL.md` y `ejemplos/`.
- **Están `workspace/` y, si el kit recibe archivos, `entrada/`**, cada una con su
  `.gitkeep`. La exclusión de `workspace/*` se lleva también el `.gitkeep` y con él la
  carpeta: el cliente abriría un kit sin sitio donde escribir sus resultados. Compruébalo
  con `unzip -l` antes de nada; la receta las devuelve con una línea aparte.
- **No** están `_CONTRATO.md`, `setup-completado.json`, `.env.local`,
  `settings.local.json`, `.DS_Store`, `node_modules/` ni resultados de pruebas.
- **Pero sí está todo lo que se llama igual y sí viaja.** Las exclusiones por nombre
  suelto (`*/_CONTRATO.md`) cazan el archivo en **todas** las carpetas, incluida
  `plantillas/`: el kit llegaría con una plantilla menos. Cuenta los archivos de
  `plantillas/` y `ejemplos/` en el ZIP y compáralos con los del disco. Por eso la
  receta ancla esa exclusión a la ruta completa.
- El `diff -r` solo muestra las exclusiones previstas. Cualquier otra diferencia se
  investiga antes de entregar.
- El peso tiene sentido (un kit normal: de 50 KB a 5 MB).

Borra la carpeta temporal al terminar.

## 6 · Entrega

Dile dónde está el ZIP y **escríbele el mensaje** para mandárselo al cliente, listo para
copiar: qué es el kit en dos líneas (entra X → sale Y), cómo se abre (descomprimir →
abrir la carpeta en VS Code → escribir `/setup`), que necesita Claude Code con una cuenta
activa, y qué cuesta usarlo si tiene claves o suscripciones.

Y una línea de recordatorio, solo si el kit se vende: conviene pactar por escrito si
incluye soporte y cambios, y hasta cuándo. Un kit con soporte ilimitado deja de ser
rentable en la segunda semana.
