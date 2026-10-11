# Evidencia 9 · Transcripción: flujo minería → incubadora → estrategias minadas (2026-09-29)

Fuente: audio de Conesa aportado por el dueño (el texto llega cortado: "…puedo ver en qué nivel de"). **Afirmaciones de marketing, no verificadas.**

## Flujo descrito
1. **Minería de estrategias** con un programa conectado (**"GoMaker"/AlgoMaker**): mina estrategias automáticamente; las candidatas pasan por "un sistema de rebuce (¿re-test?), post-mortem, Monte Carlo, muchas cosas que se utilizan en fondos de inversión, una serie de ecuaciones matemáticas para comprobar si realmente son rentables".
2. **Incubadora de traders:** prueban todas las estrategias en simulado, **sin capital asignado**, solo para ver si funcionan.
3. Si funcionan **en la sala de trading** ("aplicándole todo"), pasan automáticamente a la **mesa de estrategias minadas**: "ya están comprobadas que funcionan a largo plazo y que a largo plazo van a ser rentables" (afirmación fuerte, sin evidencia de horizonte).
4. **Arbitraje** entre exchanges por diferencia de precios; **coberturas**, **derivados**, **equipo cuantitativo** (especialista en Machine Learning, vinculado a IA).
5. **Chat con los agentes:** el dueño puede preguntarles ("cómo vamos"), darles instrucciones o dejar que funcione en automático. Ejemplo: "Bien jefe, concentrado con la energía alta, acabo de subir al nivel 14 estudiando la probabilidad de sobreajuste".
6. Promete que los espectadores tendrán acceso (producto a la venta).

## Correspondencia con Millonary
| Etapa de Conesa | Millonary |
|---|---|
| Minería + embudo (Monte Carlo, post-mortem) | ✔ `src/miner` + `src/robustness` (OOS, MC, DSR, PBO) |
| Incubadora (simulado sin capital) | ✘ por construir: papel/sombra por estrategia |
| Mesa de estrategias minadas (promoción por evidencia) | ◐ regla de promoción del laboratorio (≥90 días hacia delante) |
| Chat con agentes (preguntar/instruir) | ✘ por construir (capa conversacional sobre informes deterministas) |

## Nota crítica
"Comprobadas que funcionan a largo plazo" = en realidad lo comprobado es un periodo fuera de muestra corto. Nuestro criterio: promoción solo con evidencia hacia delante + corrección por comparaciones múltiples; nuestro minero de precio no mostró ventaja demostrable, por eso el núcleo es simple.
