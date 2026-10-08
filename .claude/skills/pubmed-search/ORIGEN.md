# Origen y revisión

- Fuente: https://github.com/JackKuo666/pubmed-search-skill
- Commit fijado: `bc68a03871058c9614147d23a52a6a943bee381c`
- SHA-256 de `pubmed_search.py` revisado: `ba8d9846cd98d3b112f8a5893711f8a873a67f652cd7890c1e8823ffb9879e8a`
- Licencia: el README muestra una insignia MIT, pero el repositorio NO incluye archivo LICENSE (404). Por eso no se copia su código a este repo: se descarga bajo demanda (`vendor/` está en .gitignore).
- Revisión (2026-10-08): 639 líneas leídas. Sin `subprocess`, `eval`, `exec`, `os.system`, `pickle`, `base64`, sockets ni lectura de credenciales. Red: solo `eutils.ncbi.nlm.nih.gov` y `ncbi.nlm.nih.gov`. Escribe archivos solo en la ruta que se le pasa (`--output`, `--output-dir`). Lee `PUBMED_API_KEY`, `PUBMED_EMAIL` y `PUBMED_TOOL` del entorno y de un `.env` opcional. Sin Unicode oculto.
- Descartado de sus instrucciones de instalación: `curl ... | sh` para instalar `uv` (no se ejecuta; basta `pip install requests`).
- Descartado el skill hermano `cookjohn/pm-skills`: exige abrir Chrome con depuración remota y enlaza Sci-Hub.
