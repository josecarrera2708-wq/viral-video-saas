# Millonary · Protocolo prerregistrado de la PRUEBA EN PAPEL (y del paso a dinero real)

Registrado en git ANTES de arrancar la cuenta de papel. Cambiar un umbral después de ver resultados
invalida la prueba: hay que anotarlo como desviación y reiniciar el reloj.

Objetivo del dueño: que todo funcione, se pueda comprobar con matemáticas, llevar un **registro de
cada entrada y si gana o pierde**, probar ~1 mes y luego pasar a dinero real.

## 0. Lo que un mes SÍ y NO puede demostrar (cifras del backtest 2017-2025, núcleo v1)
| Magnitud | Valor histórico |
|---|---|
| Posiciones completas (abrir → cerrar) | 44 en 7,9 años ≈ **0,46 al mes** |
| Órdenes (entradas, ajustes y salidas) | ≈ **7,5 al mes** (p5–p95 en ventanas de 30 días: 2–14) |
| % de posiciones ganadoras | **27 %** (ganancia media +11,3 %; pérdida media −1,2 %; relación ≈ 9:1) |
| Retorno a 30 días | p5 −5,1 % · mediana −0,5 % · p95 +16,2 % |
| **Prob. de un mes con pérdida SI la ventaja es real** | **≈ 51–54 %** |
| Caída máx. dentro de 30 días | mediana 4,0 % · p95 7,6 % · p99 9,6 % |
| Exposición media en 30 días (p5–p50–p95) | 0,05 – 0,22 – 0,56 |
| Sharpe del backtest | 1,10 → hacen falta **≈ 3,3 años de datos NUEVOS** para t = 2 |

Consecuencias, dichas sin rodeos:
1. **Un mes NO puede confirmar que es rentable**: con ventaja real, el mes es tan probable de ganar
   como de perder (cociente de verosimilitud ≈ 1). Perder el primer mes NO invalida el sistema.
2. **En un mes habrá 0 o 1 posición cerrada**: la estadística "% de aciertos" por posición no
   significa nada con n < 20. El registro cuenta por **lotes** (cada orden de compra) para tener más
   datos, pero los lotes de una misma tendencia están muy correlacionados.
3. Lo que un mes SÍ valida: que la implementación reproduce el backtest (decisiones, costes,
   funding), que el sistema es estable 24/7, que el registro cuadra y que el comportamiento está
   dentro de su envolvente histórica.
4. La rentabilidad se evalúa con una **probabilidad posterior bayesiana** que se actualiza cada día
   (sección 4); es honesta sobre lo lentamente que crece la evidencia.

## 1. Cuenta de papel
- Capital de referencia 1.000 USDT (con lote mínimo 0,001 BTC; ver aviso de cuentas pequeñas).
- Instrumento BTCUSDT perpetuo; núcleo v1 sin cambios (`config/nucleo_prerregistrado.md`).
- Inicio: primer cierre de vela de 4h posterior al commit de este documento. Duración mínima:
  **30 días naturales y ≥ 180 velas procesadas**.
- Registro: cada orden, cada lote (FIFO) y cada posición completa, con resultado GANA/PIERDE, precio,
  comisión, funding, duración, MAE/MFE, contexto (señales A/B, régimen macro) y comentario del
  departamento Escuela (post-mortem).

## 2. Puertas para pasar a la Fase 2 (dinero real MÍNIMO) — todas necesarias
| # | Puerta | Criterio |
|---|---|---|
| G1 | Réplica | Equity de papel frente al simulador validado sobre las mismas velas: diferencia ≤ 0,5 % y ≤ 1 orden de diferencia |
| G2 | Integridad | 0 velas cerradas sin procesar; toda incidencia de datos resuelta en < 24 h; 0 errores sin explicar |
| G3 | Envolvente | Exposición media ∈ [0,05 ; 0,56]; órdenes ∈ [2 ; 14]; caída máx. ≤ 9,6 % (p99 histórico); ningún freno de riesgo saltado |
| G4 | No anómalo | Retorno del periodo dentro de [p1, p99] del cono bootstrap del backtest (NO es una puerta de rentabilidad) |
| G5 | Registro cuadra | Suma del P&L de lotes/posiciones = variación de equity ± 0,01 USDT |
Fallar una puerta obliga a diagnosticar. Si se cambia código, se reinicia el reloj de 30 días.

## 3. Fase 2 · dinero real mínimo (solo con aprobación EXPRESA del dueño)
- Capital: lo fija el dueño; recomendación firme: **no más del 25 % del capital previsto** y solo
  dinero cuya pérdida total pueda asumir. Duración mínima 8 semanas.
- Claves de API de solo trading (SIN retirada), IP del VPS restringida, apalancamiento efectivo ≤ 2×.
- Puertas de la fase: costes reales por unidad rotada dentro de ±50 % de los del modelo; 0 fallos de
  ejecución sin resolver; sistema se pausa solo si la caída del capital asignado llega al 15 %.
- Escalado: por tramos (×2) con ≥ 4 semanas y sin incumplir ninguna puerta entre tramos.
- **Ir más allá de "mínimo" con criterio matemático** exige que la probabilidad posterior de
  Sharpe > 0 (sección 4) supere el 90 %; con el ritmo esperado eso tarda del orden de 1–3 años.
  El dueño puede decidir asumir más riesgo antes; lo dejo por escrito: sería una decisión sin
  respaldo estadístico suficiente.

## 4. Probabilidad posterior (informativa, en cada informe)
Prior conservador para el Sharpe verdadero: Normal(0,4 ; 0,5²) (encoge 1,10 del backtest por
sesgo de selección, un solo activo y un ciclo y medio de mercado). Verosimilitud: Sharpe observado
con error estándar 1/√(años). Se publica P(Sharpe verdadero > 0) y su intervalo al 90 %.

## 5. Agentes y departamentos: cómo se prueban
- Ningún agente puede **aumentar** la exposición por encima del objetivo del núcleo ni saltarse la
  capa de riesgo. En Fase 1 solo el departamento de Riesgos actúa; los demás operan en **modo
  sombra**: escriben qué recomendarían y el Laboratorio mide después si habrían mejorado el
  resultado (contrafactual con el mismo simulador).
- **Promoción** de una regla de un agente (o de una estrategia del Laboratorio) al capital real:
  ≥ 90 días de sombra hacia delante, supera al núcleo en Sharpe por ≥ 0,3 con caída ≤ 1,2× la del
  núcleo, pasa el embudo de robustez sobre la historia, y se anota como prueba nueva en el registro.
- Todo cambio del núcleo o de las reglas activas = versión nueva = reloj nuevo.
