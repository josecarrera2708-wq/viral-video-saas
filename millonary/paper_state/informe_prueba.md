INFORME DE LA PRUEBA EN PAPEL · día 2 · 14 velas de 4h procesadas

Retorno: +0.81% | Caída máxima: 0.52% | Exposición media: 0.59× | Órdenes: 1
Rango esperado a ~7 días si el sistema se comporta como en el backtest: p5 -3.0% · mediana -0.0% · p95 +5.2% (probabilidad de terminar en pérdida aun siendo bueno: 51%).

REGISTRO DE ENTRADAS (lotes = cada compra):
  Cerrados: 0 → ganan 0 / pierden 0
  Abiertos: 1 (P&L no realizado +8.13 USDT)
  Posiciones completas cerradas: 0  (esperado histórico: ~27 % ganadoras, ganancia media ~9× la pérdida media)
  Cuadre del diario con la equity: OK (dif. -0.0000 USDT)

PUERTAS del protocolo (paso a dinero real mínimo):
  [NO] G1 Réplica del backtest (decisiones y estado)
  [OK] G2 Integridad (ninguna vela perdida)
  [OK] G3 Comportamiento dentro de su envolvente histórica
  [OK] G4 Retorno no anómalo
  [OK] G5 El registro cuadra con la equity
  Réplica de decisiones: dif. equity +0.001% vs simulador validado; órdenes 1 vs 1
  Réplica de estado (cuenta vs replay limpio): dif. -1.34e-05; velas 14 vs 14

PROBABILIDAD DE QUE EL SISTEMA SEA RENTABLE (Sharpe verdadero > 0):
  Con 3 días aún no se puede calcular (mínimo 10).
  Referencia: con Sharpe 1,1, confirmar t = 2 exige ≈ 3.3 años de datos nuevos.

VEREDICTO: alguna puerta no se cumple todavía; NO pasar a dinero real hasta diagnosticarla.  (Con menos de 30 días las puertas G3/G4 son provisionales.)