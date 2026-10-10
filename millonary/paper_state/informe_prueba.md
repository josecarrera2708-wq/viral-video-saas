INFORME DE LA PRUEBA EN PAPEL · día 9 · 56 velas de 4h procesadas

Retorno: -1.85% | Caída máxima: 3.95% | Exposición media: 0.58× | Órdenes: 4
Rango esperado a ~7 días si el sistema se comporta como en el backtest: p5 -3.0% · mediana -0.0% · p95 +5.2% (probabilidad de terminar en pérdida aun siendo bueno: 51%).

REGISTRO DE ENTRADAS (lotes = cada compra):
  Cerrados: 0 → ganan 0 / pierden 0
  Abiertos: 2 (P&L no realizado -18.47 USDT)
  Posiciones completas cerradas: 0  (esperado histórico: ~27 % ganadoras, ganancia media ~9× la pérdida media)
  Cuadre del diario con la equity: OK (dif. -0.0000 USDT)

PUERTAS del protocolo (paso a dinero real mínimo):
  [OK] G1 Réplica del backtest (decisiones y estado)
  [OK] G2 Integridad (ninguna vela perdida)
  [OK] G3 Comportamiento dentro de su envolvente histórica
  [OK] G4 Retorno no anómalo
  [OK] G5 El registro cuadra con la equity
  Réplica de decisiones: dif. equity -0.000% vs simulador validado; órdenes 4 vs 4
  Réplica de estado (cuenta vs replay limpio): dif. +0.00e+00; velas 56 vs 56

PROBABILIDAD DE QUE EL SISTEMA SEA RENTABLE (Sharpe verdadero > 0):
  79% (intervalo 90 % del Sharpe verdadero: -0.43 a 1.22; prior conservador 0.4 ± 0.5).
  Sharpe observado en 10 días: -4.36 (error estándar ±19.6: muy poco informativo a este plazo).
  Referencia: con Sharpe 1,1, confirmar t = 2 exige ≈ 3.3 años de datos nuevos.

VEREDICTO: todas las puertas técnicas se cumplen; el paso a dinero real mínimo depende de tu aprobación expresa.  (Con menos de 30 días las puertas G3/G4 son provisionales.)