# Millonary · Núcleo prerregistrado v1 (escrito ANTES de ejecutar nada sobre datos reales)

Fecha de registro: 2026-09-29. Este documento se sube a git antes de cualquier ejecución sobre datos
reales del núcleo; el historial de git es la prueba de que los parámetros y criterios no se ajustaron
después de ver resultados. **Cambiar cualquier cosa de este documento tras ejecutar invalida la
prueba y obliga a contarla como una prueba nueva en el registro.**

Origen: revisión de diseño con un revisor cuantitativo (Opus) tras constatar que el minero genético
no aporta ventaja fuera de muestra (ranking sin poder predictivo: ρ = 0,06; nulo B 30 %; PBO alto).
El minero queda como generador de hipótesis, no como selector de qué operar.

## 1. Qué es
Un sistema de **tendencia de baja frecuencia, solo largos (o fuera de mercado)**, con exposición
continua y dimensionado por volatilidad. No hay parámetros optimizados: todo está fijado aquí.

### Pata A · Momentum de series temporales (marco diario)
Para cada horizonte L ∈ {20, 60, 120, 250} días: s_L = 1 si cierre_t / cierre_{t−L} − 1 > 0, si no 0.
Señal A = media de las cuatro s_L ∈ {0, 0,25, 0,5, 0,75, 1}. Se evalúa al cierre diario UTC y se aplica
desde la vela siguiente.

### Pata B · Ruptura Donchian 50 (velas 4h)
Estado largo cuando el cierre supera el máximo de las 50 velas anteriores; sale (estado 0) cuando el
cierre cae por debajo del mínimo de las 50 velas anteriores. Señal B ∈ {0, 1}.

### Señal combinada
Señal = 0,5 · A + 0,5 · B (pesos iguales y fijos).

### Dimensionado (volatility targeting)
Exposición objetivo = Señal · mín(2,0; 0,25 / σ), con σ = volatilidad anualizada del BTC estimada por
EWMA de 45 días sobre retornos de 4h, medida con retraso de una vela. **Tope efectivo de exposición
2× el capital** (el apalancamiento máximo de 5× queda como límite técnico del exchange, nunca se usa
como objetivo).

### Rebalanceo con banda
Se ajusta la exposición cuando cambia la señal o cuando la exposición actual se desvía más de un 20 %
relativo del objetivo. En otro caso se mantiene (minimiza rotación).

### Costes del modelo
Comisión 0,05 % por lado sobre el nocional negociado + deslizamiento 0,02 % = 7 pb por unidad de
rotación (prueba de estrés: 15 pb). Funding: real desde 2020-01 (perpetuo); sintético 0,01 % cada 8 h
para el spot 2017-2019, pagado por las posiciones largas.

### Filtro de riesgo (una única variante, prerregistrada)
Variante F: reducir la exposición a la mitad cuando el funding supera su percentil 95 móvil de 365
días. Solo aplicable con funding real (2020+). **Se acepta solo si** reduce el drawdown máximo en
≥ 10 % relativo sin bajar el CAGR más de un 10 % relativo frente a la versión sin filtro. Cuenta como
una prueba adicional en el registro.

## 2. Datos y periodos
- **Historia larga (prueba principal):** BTC spot 4h de Binance Vision, 2017-08 → 2025-06-30,
  excluyendo 2018-02-08 → 2018-02-11 (caída del servidor). 2020-01 → 2025-06 se repite con el
  perpetuo y su funding real como comprobación.
- **Subperiodos:** 2017-08→2019-12, 2020-2021, 2022, 2023-01→2025-06.
  *Ya vistos* (resultados de las reglas canónicas): 2022-01 → 2025-06. *Frescos, nunca miradas
  estas reglas*: 2017-08 → 2021-12. La evidencia principal es la fresca.
- **Periodo ciego:** 2025-07-01 en adelante. NO se toca hasta que se cumplan los criterios y se abre
  UNA sola vez.

## 3. Referencias fijas
Comprar y mantener (1×); comprar y mantener con el mismo volatility targeting y el mismo tope;
50 % comprar y mantener + 50 % efectivo.

## 4. Criterios de aceptación (todos necesarios para pasar al ciego y al paper trading)
1. Sharpe neto de costes, 2017-08 → 2025-06, ≥ 0,50.
2. Sharpe > 0 en al menos 3 de los 4 subperiodos.
3. Drawdown máximo ≤ 30 %.
4. Meseta: con la Pata A sola y un único horizonte L, entre 10 y 300 días (paso 10), al menos el 80 %
   de los horizontes con Sharpe > 0 (sin costes de ajuste), y sigue > 0 al quitar el mejor horizonte.
5. Drawdown máximo ≤ 60 % del de "comprar y mantener con vol. target".
6. Con costes de estrés (15 pb) el Sharpe sigue ≥ 0,30.

**Informativo, no eliminatorio:** alfa frente a comprar y mantener con su t (Newey-West, retardo 5);
intervalo bootstrap estacionario (bloque medio de 30 días, 5.000 remuestreos) del Sharpe y de la
diferencia de Sharpe frente a las referencias; rotación anual; exposición media; peor día.

## 5. Lo que este núcleo NO pretende
- Batir a comprar y mantener en retorno bruto en un mercado alcista fuerte (no lo hará).
- Objetivo honesto: Sharpe 0,5–0,8, drawdown 15–30 %.
- Con ~8 años de historia el error estándar del Sharpe es ≈ 0,37: **aunque pase los criterios no
  queda "demostrado"**; pasa a la siguiente etapa (ciego + paper trading), no a dinero real.

## 6. Prueba en el periodo ciego (criterios escritos antes de abrirlo)
Se abrirá una sola vez. No certifica: solo detecta fallos groseros. Aceptable si el drawdown queda
dentro de la banda del bootstrap al 95 % y la exposición media y la rotación anual están dentro
de ±50 % de las de 2017-2025-06. Cualquier fallo obliga a revisar la implementación, no los parámetros.

## 7. Registro de pruebas
Este núcleo cuenta como **1 prueba** (+1 por la variante de filtro de funding). Se suman al registro
existente (14 variantes de proceso + ≈ 50.000 estrategias del minero, que no se usan para elegir
nada aquí).
