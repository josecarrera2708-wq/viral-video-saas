# Empaquetar un kit para entregarlo

Cuando el kit va a manos de otra persona —un cliente, un comprador, alguien de su
equipo— se comprime en un ZIP. Parece el paso trivial y es donde se cuelan los
errores más caros, porque el fallo aparece en el ordenador de otro.

Los tres desastres clásicos, y los tres tienen la misma causa (no comprobar):

1. **El kit viaja ya instalado.** El cliente descomprime, escribe "hola" y le sale el
   menú de kit configurado en vez del asistente. Se colaron el
   `.claude/setup-completado.json` y los resultados de las pruebas.
2. **El ZIP pesa 300 MB.** Se colaron `node_modules/`, cachés o los archivos de prueba.
3. **Falta un archivo** y el kit no arranca. Nadie comprobó el ZIP descomprimiéndolo.

---

## Antes de comprimir: dejar el kit en estado de primer arranque

Esto es la mitad del trabajo. En orden:

```bash
KIT="mis-kits/NN-kit-nombre"

# 1. Que el kit no viaje instalado
rm -f "$KIT/.claude/setup-completado.json"

# 2. workspace/ vacío, solo con su .gitkeep
find "$KIT/workspace" -type f ! -name '.gitkeep' -delete

# 3. Ni claves ni configuraciones locales
rm -f "$KIT/.env.local" "$KIT/.claude/settings.local.json"

# 4. Basura de macOS
find "$KIT" -name '.DS_Store' -delete
```

Y a mano, comprobando uno por uno:

- **`.env.example` sí viaja** (es la plantilla), `.env.local` **no** (son sus claves).
- **`_CONTRATO.md` no viaja.** Es material de construcción y contiene la lista de
  errores plantados del ejemplo de práctica: si viaja, el ejemplo deja de servir. Se
  queda en la carpeta del usuario, que es quien lo necesita para ampliar el kit.
- El **cuaderno de trabajo** de las pruebas (`workspace/*-hallazgos.md`) no viaja.
- Si el kit se entrega con **marca blanca**: ni el nombre del usuario, ni su web, ni su
  correo, ni su firma en ningún documento ni en la plantilla del informe. Búscalo con
  `grep -ri "su-nombre" "$KIT"` — siempre aparece en un sitio que nadie recordaba.
- **Ninguna ruta del ordenador del usuario** en la documentación: nada de
  `/Users/nombre/Desktop/...`. Rutas relativas desde la raíz del kit. `grep -r "/Users/" "$KIT"`.
- Y los **datos de prueba reales**, si en algún momento se usó un caso real del usuario
  para probar: fuera. Solo viaja el ejemplo ficticio.

---

## Comprimir

### Mac y Linux

```bash
cd mis-kits
zip -r "NN-kit-nombre.zip" "NN-kit-nombre" \
  -x "NN-kit-nombre/_CONTRATO.md" \
  -x "*/node_modules/*" \
  -x "*/.next/*" \
  -x "*/.git/*" \
  -x "*/.env.local" \
  -x "*/.claude/settings.local.json" \
  -x "*/.claude/setup-completado.json" \
  -x "*.DS_Store" \
  -x "*/workspace/*" \
  -x "*/datos/*"

# Y devuelve los .gitkeep de las carpetas que acabas de excluir enteras.
# Sin esta línea el ZIP no lleva workspace/ y el kit llega sin la carpeta
# donde escribe sus resultados. Es el fallo más silencioso de esta receta.
zip -q "NN-kit-nombre.zip" "NN-kit-nombre/workspace/.gitkeep"
```

**Por qué el contrato se excluye con su ruta completa y no con `*/_CONTRATO.md`.**
Porque `*` en `zip` atraviesa las barras: `*/_CONTRATO.md` caza **cualquier**
`_CONTRATO.md` del kit, incluido el de `plantillas/`, que es un archivo del kit y tiene
que viajar. Pasó de verdad al empaquetar el kit 08: el ZIP salió sin
`plantillas/_CONTRATO.md`, y el kit habría llegado con una plantilla menos de las nueve
que su propia skill promete. Se ve con `unzip -l NN-kit-nombre.zip | grep -i contrato`:
tiene que salir la plantilla y **no** el contrato de la raíz.

La regla general: **una exclusión por nombre suelto se ancla a su ruta completa en
cuanto ese nombre existe legítimamente en otro sitio del kit**. Vale para cualquier kit
con carpeta de plantillas o de ejemplos: un `settings.json` de plantilla, un
`.env.local` de ejemplo, un `README.md` dentro de `ejemplos/`.

**Por qué esa segunda línea.** `-x "*/workspace/*"` no excluye solo los resultados:
excluye también el `.gitkeep`, y con él la carpeta entera — al descomprimir, `workspace/`
no existe. Se ve en `unzip -l`: si no aparece ninguna línea con `workspace`, falta.
Pasó de verdad al empaquetar el kit 01 de `mis-kits/`, con la exclusión copiada tal cual
de esta misma receta.

Se mantiene la exclusión (protege de un resultado olvidado) y se devuelve el `.gitkeep`
después. Si el kit tiene otras carpetas excluidas enteras que deben existir al
descomprimir (`datos/`, una `salidas/`), se devuelve el `.gitkeep` de cada una con su
propia línea. Y si una de esas carpetas **no** tiene `.gitkeep`, se le pone antes de
empaquetar.

### Windows (PowerShell)

`zip` no existe en Windows. Se usa `Compress-Archive`, que **no tiene exclusiones**, así
que se copia primero a una carpeta temporal limpia:

```powershell
$origen  = "mis-kits\NN-kit-nombre"
$destino = "$env:TEMP\NN-kit-nombre"

Remove-Item $destino -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item $origen $destino -Recurse

# Quitar lo que no viaja
Remove-Item "$destino\_CONTRATO.md" -Force -ErrorAction SilentlyContinue
Remove-Item "$destino\.env.local" -Force -ErrorAction SilentlyContinue
Remove-Item "$destino\.claude\setup-completado.json" -Force -ErrorAction SilentlyContinue
Remove-Item "$destino\.claude\settings.local.json" -Force -ErrorAction SilentlyContinue
Remove-Item "$destino\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem "$destino\workspace" -File -Exclude ".gitkeep" | Remove-Item -Force

Compress-Archive -Path $destino -DestinationPath "mis-kits\NN-kit-nombre.zip" -Force
Remove-Item $destino -Recurse -Force
```

La variante de Windows no tiene los dos problemas de arriba: sus `Remove-Item` van con la
ruta completa (`"$destino\_CONTRATO.md"`, solo el de la raíz) y su
`Get-ChildItem -Exclude ".gitkeep"` conserva la carpeta. Es lo que pasa por borrar en vez
de excluir por patrón.

En los dos casos, **la raíz del ZIP es la carpeta del kit con su número**: al
descomprimir tiene que aparecer `NN-kit-nombre/` y dentro los archivos. Nunca los
archivos sueltos: quien lo abre acaba con veinte cosas en su carpeta de Descargas.

---

## Verificar: descomprimir y comparar

**Sin este paso no se entrega.** Es lo único que demuestra que el ZIP sirve.

```bash
cd /tmp && rm -rf verificacion && mkdir verificacion && cd verificacion
unzip -q "/ruta/al/NN-kit-nombre.zip"

# ¿Está todo lo que debía?
ls -la "NN-kit-nombre"
ls -la "NN-kit-nombre/.claude/commands" "NN-kit-nombre/.claude/skills"

# ¿Qué diferencias hay con el original? Solo deberían salir las exclusiones
diff -r "NN-kit-nombre" "/ruta/original/mis-kits/NN-kit-nombre"

# ¿Cuánto pesa?
du -sh "NN-kit-nombre"
```

La lista de comprobación del ZIP:

- [ ] Al descomprimir aparece **una** carpeta, `NN-kit-nombre/`.
- [ ] Están `EMPIEZA-AQUI.md`, `README.md`, `CLAUDE.md`, `.claude/settings.json`, el
      comando `setup.md`, el `SKILL.md` y la carpeta `ejemplos/`.
- [ ] **Están las carpetas vacías que el kit necesita**, con su `.gitkeep`: `workspace/`
      siempre, `entrada/` si el kit recibe archivos, y cualquiera que el kit escriba.
      Se comprueba en la lista del ZIP, no descomprimiendo:
      `unzip -l NN-kit-nombre.zip | grep -E "workspace|entrada"`. Si no sale ninguna
      línea, la exclusión se llevó la carpeta y el kit llega sin sitio donde escribir.
- [ ] **No** están: `_CONTRATO.md`, `setup-completado.json`, `.env.local`,
      `settings.local.json`, `.DS_Store`, `node_modules/`, ni resultados de pruebas.
- [ ] **Pero sí está todo lo que se llama igual y sí viaja.** Una exclusión por nombre
      suelto caza el archivo en todas las carpetas: si el kit tiene `plantillas/` o
      `ejemplos/`, comprueba que no se llevó nada de ahí.
      `unzip -l NN-kit-nombre.zip | grep -cE "plantillas/|ejemplos/"` y compara con lo
      que hay en disco (`ls plantillas | wc -l`). Falta uno = falta una plantilla, y el
      kit llega prometiendo un archivo que no lleva.
- [ ] `diff -r` solo muestra las exclusiones previstas. Cualquier otra diferencia se
      investiga antes de entregar.
- [ ] El peso tiene sentido: un kit normal va de **50 KB a 5 MB**. Más de 20 MB, algo
      se ha colado: mira qué con `du -sh */`.
- [ ] Y la prueba de verdad: **abrir la copia descomprimida en una ventana nueva de
      VS Code, escribir "hola" y ver que sale el asistente de instalación**, no el
      menú. Si sale el menú, el kit viajó instalado: vuelve al primer apartado.

Los archivos de la copia de verificación se borran al terminar (`rm -rf /tmp/verificacion`).

---

## Qué se le entrega al cliente

El ZIP solo no basta. Con él van tres cosas, en el mensaje o el correo:

1. **Qué es y qué hace**, en dos líneas: entra X → sale Y.
2. **Cómo se abre**: descomprimir, abrir la carpeta en VS Code (`Archivo → Abrir
   carpeta…`), y escribir `/setup`. Con la advertencia de que el kit necesita Claude
   Code instalado y una cuenta activa.
3. **Qué cuesta usarlo**, si tiene claves de API o suscripciones.

Y si el kit se vende, lo que conviene pactar por escrito antes: si incluye soporte, si
incluye cambios, y durante cuánto tiempo. Un kit sin límite de soporte deja de ser
rentable en la segunda semana.
