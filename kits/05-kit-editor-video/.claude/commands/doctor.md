---
description: Revisa qué le falta al kit en este ordenador y lo arregla
---

Revisa la instalación y arregla lo que falte. Los comandos los ejecutas tú; el
usuario no abre ninguna terminal.

1. Ejecuta `python scripts/doctor.py --json` (con el comando de Python que esté
   guardado en `.claude/setup-completado.json`, o `python3` en Mac y `python` en
   Windows si no hay nada guardado).

2. Resúmelo en lista corta y en cristiano: ✓ lo que está, y el nombre normal de lo
   que falta. Nada de pegar el JSON. Distingue las dos categorías, porque no son
   igual de graves:
   - **`falta`** → el kit no puede editar hasta arreglarlo.
   - **`aviso`** → el kit edita igual. Lo más común es que los visuales (rótulos y
     mockups) no estén: se pierden los rótulos, nada más.

3. Si falta algo, arréglalo tú: `python scripts/doctor.py --instalar`. Y si el
   problema es solo ffmpeg, `python scripts/instalar_ffmpeg.py` da el mensaje
   detallado con la vía alternativa de su sistema.

4. Si el usuario viene porque **algo no funciona al editar** (no porque quiera una
   revisión), el doctor puede salir todo en verde y no servir de nada: el doctor
   comprueba que los programas están, no que hagan su trabajo. En ese caso lanza la
   prueba de verdad:

   ```
   python scripts/prueba.py
   ```

   Fabrica un vídeo y lo edita entero en unos 15 segundos. Si esa prueba pasa, el
   kit está bien y el problema está en el vídeo concreto del usuario (formato raro,
   sin audio, rotación de móvil): pídele el mensaje de error literal y mira la
   tabla de errores de `CLAUDE.md`.

5. Termina diciendo la siguiente acción concreta: editar un vídeo, o el arreglo
   exacto que falta.
