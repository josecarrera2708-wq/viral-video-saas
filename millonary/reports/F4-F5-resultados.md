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
  (comisiones ×2, deslizamiento 5 pb, +10 % del rango de la vela en stops), comparación con entradas aleatorias,
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

## ¿Aporta algo el minero frente al azar? (ejecutado)
| | Minadas (150 mejores en train) | Aleatorias sin minar (1.500, mismos mínimos) |
|---|---|---|
| Sharpe train medio | 1,51 | −0,46 |
| Sharpe validación medio | 0,58 | −0,34 |
| % con Sharpe de validación > 0 | 85 % | 42 % |
| % con Sharpe de validación > 1 | 26 % | 6,9 % |
| Correlación de rangos train↔validación | 0,06 | 0,57 |

Lectura:
1. **Sí hay algo, pero modesto:** las minadas superan al azar en validación (0,58 frente a −0,34), y
   también a las 150 mejores en train de estrategias aleatorias (0,36).
2. **Degradación fuerte:** el Sharpe cae de 1,51 (train) a 0,58 (validación), un ~62 % menos. El
   Sharpe de entrenamiento NO es la expectativa real; la expectativa es la de validación o menos.
3. **Dentro de las 150 elegidas, el orden de train no predice el de validación (0,06):** por eso
   el PBO sale tan alto. Elegir "la mejor" es casi una lotería entre buenas.
4. **Cuidado con el beta alcista:** la validación (2024-01 → 2025-06) fue en su mayoría alcista para
   BTC. Que el 85 % salga positivo puede deberse a que las estrategias de tendencia se benefician de
   ese tramo, no solo a habilidad. El periodo ciego (2025-07 → 2026-08), con caída desde máximos,
   será una prueba más dura. **Sigue sin abrirse.**
5. Las estrategias aleatorias pierden en promedio: los costes reales (comisiones, funding,
   deslizamiento) se comen el edge de cualquier regla sin fundamento.

## Pendiente
- Revisión adversarial del embudo (F5) con un modelo más fuerte.
- Walk-forward real con re-minado en ventanas móviles y datos nuevos (F7).
