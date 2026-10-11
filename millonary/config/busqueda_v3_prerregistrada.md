# Búsqueda v3 · estrategias de fondos, investigadores y traders conocidos (prerregistro, 2026-10-05)

Petición del dueño: «busca los grandes traders y los grandes fondos, cómo operan, y crea mesas nuevas con estrategias nuevas y con nombres».
Este documento se registra en git ANTES de ejecutar la evaluación. Pruebas nº 1082-1109 (28 variantes).

## Qué hacen los grandes (investigación, 2026-10-05) y qué YA estaba probado
- Fondos de futuros/CTA (AHL, Winton, AQR): momentum de series temporales, mezcla de varias velocidades de tendencia. Ya probado:
  F01-F03, F07 en la mesa de fondos y Q01/Q06 en las mesas cortas. **Nuevo aquí:** el CONJUNTO de 3 velocidades (N11).
- Fondos neutrales (base/funding, creadores de mercado): carry F06, basis B01/B02, maker. Ya en marcha; no se repite.
- Traders legendarios: Tortugas, Tudor Jones, L. Williams, Raschke y Crabel ya están en la mesa de fondos.
  **Nuevos:** Connors (N07), Weinstein (N09), Minervini/Darvas con máximos de 52 semanas (N10).
- Investigación cuantitativa publicada sobre BTC, nueva aquí:
  - Zarattini-Aziz-Barbon 2024, zona de ruido (N01).
  - Concretum 2025, apertura de Asia del lunes (N02).
  - Quantpedia 2024: noches con la bolsa cerrada (N03), MAX(10) y MIN(10) (N05/N06).
  - Estudios de estacionalidad horaria: 21-23 UTC (N04).
  - Literatura de reversión diaria: IBS (N08).

## Reglas
Las reglas exactas están en `src/busqueda/v3.py` (congelado con este commit).
- Familias y temporalidades:
  - 1 h: N01-N04.
  - 4 h: N11.
  - Diario: N05-N11.
- Variantes: 28. La lista exacta está en `variants()`.
- Stops amplios: 2-6 ATR. Casi todas las salidas son por regla («dejar correr»), por tiempo o por estacionalidad, sin TP corto, según las marginales de la v2.

## Evaluación (idéntica a la v2)
Datos: perpetuo Binance BTCUSDT.

| Periodo | Desde | Hasta |
|---|---|---|
| Construcción | 2020-03 | 2024-01 |
| Validación | 2024-01 | 2025-07 |
| Examen | 2025-07 | 2026-09-28 |

- Motor `src/backtest/engine.py`: taker 0,05 %, deslizamiento 2 pb, funding real, riesgo 0,5 % por operación.
- Elegible: R>0 en construcción y en validación, con ≥30 ops en validación (≥10 en diario).
- Examen: las elegibles, como máximo 20, por t de validación.
- Puertas:
  - G1: R>0 con ≥20 ops.
  - G2: p de Holm <0,10.
  - G3: R>0 con costes ×2.
  - G4: caída <30 %.
  - G5: DSR ≥0,80 con n_trials = 28. El total acumulado del proyecto (1.109) se informa aparte.
- Certificada = 5/5. Sin certificación NO hay dinero real (además exige la aprobación EXPRESA del dueño).

## Mesas nuevas en papel (decisión del dueño, 2026-10-05) — regla fijada ANTES de ver los resultados
- **Mesa Swing 4 h y Mesa Diaria** (más la horaria de estacionalidad si alguna familia de 1 h sale elegible).
- Composición:
  - (a) De la v3, la mejor variante elegible de CADA familia, por t de validación. Las familias sin ninguna elegible quedan fuera.
  - (b) De la v2, solo en 4 h y diario, la mejor variante elegible de cada setup S1-S6, por t de validación.
- Inicio: 2026-10-06 00:00 UTC.
- Fuente: Deribit BTC-PERPETUAL. Las velas de 1 h, 4 h y diarias se construyen desde las de 15 min ya usadas por las mesas.
- Capital y riesgo: 1.000 USDT de papel por trader y 0,5 % de riesgo por operación, con el mismo motor.
- Nombres: apodos de presentación en `config/apodos.json`. No cambian reglas.
- Sin cambios de reglas ni parámetros durante la prueba.
- Lectura a los 90 días o a las 30 operaciones cerradas por trader, lo que llegue antes.
