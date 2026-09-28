# Las plantillas

Esqueletos de los archivos de un kit. Se copian a `mis-kits/NN-kit-nombre/` y se
adaptan: **todos los marcadores `[[así]]` hay que sustituirlos**. Ninguna plantilla se
entrega tal cual — un kit con `[[...]]` dentro es un kit sin terminar.

| Plantilla | Va a |
|---|---|
| `_CONTRATO.md` | `mis-kits/NN-kit-nombre/_CONTRATO.md` — lo primero que se crea (Paso 2) |
| `CLAUDE.md.txt` | `mis-kits/NN-kit-nombre/CLAUDE.md` |
| `SKILL.md` | `mis-kits/NN-kit-nombre/.claude/skills/<nombre-skill>/SKILL.md` |
| `setup.md` | `mis-kits/NN-kit-nombre/.claude/commands/setup.md` |
| `README.md` | `mis-kits/NN-kit-nombre/README.md` |
| `EMPIEZA-AQUI.md` | `mis-kits/NN-kit-nombre/EMPIEZA-AQUI.md` |
| `settings.json` | `mis-kits/NN-kit-nombre/.claude/settings.json` — quitando los permisos que ese kit no use |
| `gitignore.txt` | `mis-kits/NN-kit-nombre/.gitignore` |

`CLAUDE.md.txt` y `gitignore.txt` llevan `.txt` a propósito: un `CLAUDE.md` dentro de
esta carpeta se cargaría como instrucciones del kit 08, y un `.gitignore` aquí escondería
archivos que sí queremos ver.

El orden de construcción está en el Paso 5 de la skill, y no es opcional: estructura →
`CLAUDE.md` → skill → wizard → `README.md` → `EMPIEZA-AQUI.md` → `settings.json` +
`.gitignore`. Cada uno se apoya en el anterior.
