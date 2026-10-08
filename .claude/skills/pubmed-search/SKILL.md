---
name: pubmed-search
description: Busca y lee resúmenes de artículos científicos en PubMed (API oficial NCBI E-utilities) para verificar cifras y estudios de salud, ejercicio y nutrición antes de usarlos en un guion. Úsalo cuando haya que comprobar un estudio, encontrar un meta-análisis o sacar el resumen original de un PMID. Primero ejecuta `instalar.sh` una vez.
---

# PubMed Search (envoltorio revisado)

Usa la herramienta `pubmed_search.py` de https://github.com/JackKuo666/pubmed-search-skill (commit fijado, ver `ORIGEN.md`). El código se descarga con `instalar.sh` y se comprueba su SHA-256 contra la versión revisada. Solo habla con `eutils.ncbi.nlm.nih.gov` y `ncbi.nlm.nih.gov` (PubMed/PMC).

## Instalar (una vez)
```bash
bash .claude/skills/pubmed-search/instalar.sh
```
Si falla la huella, NO uses el archivo: el repositorio de origen ha cambiado y hay que revisarlo de nuevo.

## Uso
```bash
P=.claude/skills/pubmed-search/vendor/pubmed_search.py
python3 $P search --keywords "resistance training fat-free mass weight loss meta-analysis" --results 10
python3 $P metadata --pmid 28698222
python3 $P search --keywords "protein intake resistance training" --results 20 --output /tmp/resultados.json
```
No uses `download` salvo que el usuario lo pida: solo guarda PDFs de acceso abierto de PMC y respeta el copyright.

## Reglas
1. Cada cifra que vaya a un guion debe salir de un resumen leído aquí o del artículo, no de memoria.
2. Apunta PMID, año, tipo de estudio y tamaño de muestra en `fuentes.md`.
3. El resumen no basta para cifras finas (umbrales, subgrupos): marca "verificar texto completo".
4. Sin clave de API el límite es 3 peticiones por segundo. Si aparece el estado 429 (probado: ocurre con 3 resultados seguidos), espera unos segundos y repite, o pide un solo `metadata --pmid` cada vez. No lances búsquedas en bucle.
5. Los mensajes de la herramienta están en chino; el contenido de los artículos viene en inglés.
