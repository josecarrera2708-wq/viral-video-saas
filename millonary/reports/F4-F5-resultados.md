# F4 + F5 · Minero de estrategias y embudo de robustez (2026-09-29)

## Qué se hizo
- **Datos:** perpetuo BTCUSDT USDT-M, 1h y 4h, 2020-01-01 → 2026-08-31 (funding incluido).
- **Reparto fijado de antemano** (`config/splits.json`): entrenamiento 2020-01→2023-12, validación
  2024-01→2025-06, **ciego 2025-07→2026-08 (sin tocar)**. El minero tiene una barrera de código que
  le impide ver nada más allá del entrenamiento.
- **Minero genético:** 8 islas independientes × 300 individuos × 15 generaciones.
  **32.304 estrategias únicas probadas** (dato necesario para el ajuste por sobreajuste).
  Genoma = filtro de régimen + regla de entrada (cruce de medias, ruptura Donchian, RSI, MACD,
  Bollinger, patrones de velas, ruptura de estructura) + stop (ATR o estructura) + salida
  (TP en R, tiempo, señal contraria). Costes reales incluidos. Riesgo 1 % por operación, capital
  de referencia 1.000 USDT.
- **Embudo** (umbrales en `config/gates.json`, fijados antes de ver resultados) sobre 150
  candidatas descorrelacionadas (|corr| < 0,8): validación fuera de muestra, estabilidad por
  semestres, Monte Carlo (5.000 remuestreos), sensibilidad de parámetros ±1 paso, estrés de costes
  (comisiones ×2, deslizamiento 5 pb, +15 % del rango en stops), comparación con entradas aleatorias,
  Deflated Sharpe Ratio y PBO (CSCV).

## Resultado
| Prueba | Pasan (de 150) |
|---|---|
| Validación fuera de muestra (Sharpe ≥ 1, DD ≤ 20 %, PF ≥ 1,15, mín. operaciones) | 39 |
| Estabilidad por semestres | 139 |
| Monte Carlo (p5 del retorno > 0, p95 DD ≤ 30 %) | 86 |
| Sensibilidad de parámetros | 150 |
| Estrés de costes | 138 |
| Mejor que entradas aleatorias | 148 |
| **Deflated Sharpe ≥ 0,95** | **0** |
| **Supervivientes (pasan todo)** | **0** |

- **PBO global = 0,80** (umbral aceptable ≤ 0,30): el ranking "mejor en entrenamiento" no persiste
  con fiabilidad fuera de muestra.
- Mejor Deflated Sharpe individual: 0,66.
- Hubo candidatas con Sharpe de validación de 1,4 a 2,1 y drawdown de 4–12 %, pero con solo
  ~1,5 años de validación y 150 candidatas comparadas, **no hay evidencia estadística suficiente**
  de que sean habilidad y no suerte.

## Lectura honesta
1. **El sistema hace lo que debe: rechaza.** Con umbrales fijados de antemano, ninguna estrategia
   se certifica. Es exactamente el comportamiento de Conesa en pantalla (1092 evaluadas, 0 candidatas).
2. **No se certifica NINGUNA estrategia para operar.** No hay que "rebajar los umbrales" para que
   pase alguna: eso sería engañarnos.
3. El periodo ciego (2025-07 → 2026-08) **sigue sin abrirse**. No se abre hasta que haya candidatas
   que hayan superado el embudo.

## Próximos pasos posibles (no aplicados todavía)
- Más historia de validación con **walk-forward real** (re-minar en ventanas móviles y validar
  siempre en datos posteriores), en lugar de una única ventana de validación de 1,5 años.
- Ampliar el espacio de búsqueda con **datos que aportan información distinta**: funding, open
  interest, Fear & Greed, régimen macro, calendario de eventos (F7).
- Reducir el número de comparaciones (menos genes, reglas más simples) para bajar el umbral del DSR.
- Probar la misma familia de estrategias en ETH/SOL solo como **contraste de robustez**, no para
  operar (el proyecto es solo BTC).

## Pendiente de ejecutar (terminal no disponible en el momento de escribir esto)
- `src/robustness/mining_value_check.py`: mide si el minero aporta algo frente a estrategias
  aleatorias con los mismos mínimos (degradación train→validación, correlación de rangos).
- Revisión adversarial del embudo (F5) con un modelo más fuerte.
