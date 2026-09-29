# Núcleo prerregistrado v1 · resultado sobre 2017-08 → 2025-06 (ciego NO abierto aún)

Definición, parámetros y criterios: `config/nucleo_prerregistrado.md` (commit `3e61b21`, anterior a
cualquier ejecución). Un único pase sobre datos reales. Spot 4h (perpetuo + funding real desde 2020),
costes 7 pb por unidad de rotación, funding sintético 0,01 %/8h antes de 2020.

## Resultado principal (2017-08 → 2025-06, ≈ 7,9 años)
| | Sharpe | CAGR | Caída máx. | Ret. total | Peor día |
|---|---|---|---|---|---|
| **Núcleo** | **1,10** | 19,4 % | **25,0 %** | +304 % | −4,7 % |
| Comprar y mantener | 0,92 | 48,1 % | 85,7 % | +2.093 % | −39,5 % |
| Comprar y mantener con el mismo vol. target | 0,85 | 20,7 % | 44,0 % | +338 % | −15,6 % |
| 50 % BTC + 50 % efectivo | 0,92 | 29,6 % | 57,7 % | +671 % | −21,3 % |

Operativa: exposición media 0,25× (máx. 0,84×), rotación 8,3 veces el capital al año, en mercado
el 88 % del tiempo, funding pagado 0,31 % del capital en total.

## Subperiodos
| | Sharpe | Retorno | Caída |
|---|---|---|---|
| 2017-08 → 2019-12 *(fresco)* | 0,90 | +34,0 % | 22,4 % |
| 2020-2021 *(fresco)* | 1,46 | +73,3 % | 16,2 % |
| 2022 | **−1,56** | −14,8 % | 18,2 % |
| 2023-01 → 2025-06 | 1,55 | +104,1 % | 14,6 % |

En 2022 (mercado bajista con muchos falsos movimientos) el núcleo perdió un 14,8 %, frente a
−64 % de comprar y mantener y −33 % con vol. target, pero **su Sharpe no fue mejor** (−1,56 frente a
−1,29 y −1,47): perder poco no es lo mismo que ganar en una tendencia bajista, porque el sistema es
solo largos.

## Criterios prerregistrados: **los 6 se cumplen**
1. Sharpe ≥ 0,50 → 1,10 ✔
2. Sharpe > 0 en ≥ 3 de 4 subperiodos → 3 de 4 ✔
3. Caída máx. ≤ 30 % → 25,0 % ✔
4. Meseta: 30 de 30 horizontes (10–300 días) con Sharpe > 0, media sin el mejor 0,88 ✔
   (Sharpe de la pata A sola entre 0,54 y 1,52; mejor a 40 días)
5. Caída máx. ≤ 60 % de la de comprar y mantener con vol. target → 25,0 % frente a 26,4 % permitido ✔ (justo)
6. Sharpe con costes de estrés (15 pb) ≥ 0,30 → 1,06 ✔

## Estadística (informativa)
- **Bootstrap estacionario (5.000, bloque de 30 días), Sharpe del núcleo: p5 0,39 · mediana 1,09 · p95 1,75.**
- Diferencia de Sharpe frente a comprar y mantener con vol. target: p5 −0,10 · mediana +0,23 ·
  p95 +0,57. **El intervalo incluye el cero**: no puede afirmarse que el núcleo mejore el Sharpe de
  ese punto de referencia; sí mejora claramente la caída máxima (25 % frente a 44 %).
- Alfa frente a comprar y mantener: +7,7 % anual, t = 1,73 (beta 0,18). Frente a comprar y mantener
  con vol. target: +7,1 % anual, t = 1,86 (beta 0,55). Ninguno llega a t = 2.

## Perpetuo con funding real (2020-01 → 2025-06) y variante F
Núcleo: Sharpe 1,18, CAGR 22,0 %, caída 23,8 %. Comprar y mantener con vol. target: Sharpe 0,94,
caída 44,0 %.
**Variante F (recortar a la mitad con funding en percentil ≥ 95): NO se acepta** (reducción de caída
0 %; el filtro estuvo activo solo el 4,1 % del tiempo). Se mantiene el núcleo sin filtro.

## Lectura honesta
1. Pasa todos los criterios fijados de antemano: **queda habilitado para el periodo ciego y para
   paper trading. NO está demostrado.**
2. La evidencia fresca (2017-2021, nunca probada con estas reglas) es buena (Sharpe 0,9 y 1,5),
   pero fue un mercado alcista muy fuerte, favorable al seguimiento de tendencia, y con muy pocas
   tendencias grandes: el tamaño de muestra real es de unos pocos movimientos, no de 2.874 días.
3. **El valor principal es control de riesgo, no alfa:** caída del 25 % frente a 44–86 %, y un peor
   día de −4,7 % frente a −15,6 % y −39,5 %. No batirá a comprar y mantener en retorno absoluto en
   mercados alcistas fuertes (CAGR 19 % frente a 48 %).
4. El criterio 5 pasó por poco (25,0 % frente a 26,4 %); no lo interpreto como holgura.
5. Sesgos que no puedo eliminar: solo BTC (un activo que ganó), un ciclo y medio de mercado, y el
   diseño lo decidí conociendo el historial general del activo aunque no las cifras de 2017-2021.

## Registro de pruebas
Este núcleo: 1 prueba (+1 la variante F, rechazada). Total de variantes de proceso contabilizadas: 16.
