# Mesa de 15 min · Prerregistro (v1) — fijado ANTES de ejecutar ningún resultado

Fecha: 2026-10-02. Petición del dueño: acelerar la prueba con velas de 15 minutos, **en paralelo** (la mesa de 1 h sigue intacta), con
acción de precio (techos y suelos, ineficiencias, mejores patrones de velas) y fórmulas cuantitativas que usan los fondos; y que los
agentes **aprendan** de sus errores sin esperar 90 días. Sistema aparte, contabilidad aparte (`paper_state/mesa15/`).

## Datos
Deribit BTC-PERPETUAL, velas de 15 min CERRADAS (único proveedor accesible), 2022-06-01 → hoy; funding real `interest_1h/4` por vela
(los huecos recientes aún no publicados cuentan como 0 y se avisan). Motor validado `src/backtest/engine.py`, mismos costes que la mesa de 1 h
(taker 5 pb, maker 2 pb en TP, deslizamiento 2 pb, riesgo 0,5 % por operación, apalancamiento ≤ 5×, 1.000 USDT por trader).
Entrada en la apertura de la vela siguiente a la señal. Todos los indicadores son causales (prueba de truncamiento obligatoria).

## Universo (N = 13 traders; parámetros FIJOS en `src/desk15/setups.py`; ventanas en velas de 15 min; ATR = ATR(14))
**Acción de precio** — P01 Envolvente en soporte/resistencia (mín./máx. de 96 velas ± 0,5 ATR) · P02 Pin bar (martillo / estrella fugaz) en techo o suelo de 48 velas ·
P03 Barrido de liquidez (rompe el mín./máx. de 96 velas y cierra de vuelta dentro) · P04 Ineficiencia: Fair Value Gap (hueco de 3 velas > 0,3 ATR) y reentrada al hueco ·
P05 Barra interior + ruptura a favor de la tendencia (EMA 384) · P06 Estrella de la mañana / de la tarde en soporte/resistencia · P07 Doble techo / doble suelo (pivotes de 6 velas, ≤ 0,3 ATR de diferencia, ruptura de la línea de cuello).
**Fórmulas cuantitativas** — Q01 Momentum de series temporales (Moskowitz–Ooi–Pedersen: retorno 24 h normalizado por volatilidad, de acuerdo con 7 d) ·
Q02 Reversión de Ornstein–Uhlenbeck (z-score a 96 velas ≤ −2,5 / ≥ +2,5) · Q03 Cambio de régimen por razón de varianzas de Lo–MacKinlay (VR>1,15 sigue ruptura Donchian 48; VR<0,85 revierte z ±2) ·
Q04 Expansión de volatilidad Garman–Klass (GK corto 16 / largo 192 > 1,5 con ruptura de 24 velas) · Q05 Desequilibrio de flujo (proxy: delta de cierre×volumen, z a 32 velas > 2 con ruptura) ·
Q06 Cruce de medias EMA 96/384 con filtro de tendencia ADX(14) > 25 (CTA clásico, salida por señal contraria).
Stops por estructura/ATR (0,5–3 ATR), take-profit en múltiplos de R o salida por señal, salida por tiempo. Una posición por trader a la vez.

## Aprendizaje (rápido, causal, honesto)
Cada trader base (B) opera todas sus señales. Dos aprendices por trader aprenden SOLO de operaciones ya cerradas antes de la señal:
- **A (individual)**: veta una señal si, en alguna de sus tres dimensiones de contexto —lado respecto a la tendencia de 800 h (a favor/contra), volatilidad (tercil del percentil ATR), sesión UTC (Asia 22-08 / Europa 08-14 / EE. UU. 14-22)— el trader acumula n ≥ 6 operaciones y la R media del nivel es PEOR que su media global con t ≤ −1 (t = (media del nivel − media global)/error típico del nivel).
- **C (colectivo)**: la misma regla con las operaciones de TODA la sala (13 traders), n ≥ 15, para aprender más rápido.
  *Enmienda previa a la ejecución sellada*: la primera versión era absoluta (R media < 0). Una prueba de tubería SOLO sobre el periodo de construcción mostró que vetaba casi todo (con costes la mayoría de contextos pierde) y se cambió a relativa antes de mirar validación o examen.
El aprendiz y su base se evalúan por separado con el mismo motor. El aprendizaje es una HIPÓTESIS estadística: con pocas operaciones puede aprender ruido; por eso los aprendices operan en papel junto a la base y nada toca dinero real.
Cada vez que un veto nuevo se activa se registra «qué aprendió y con qué evidencia» (pestaña Aprendizaje).

## Periodos (se mira cada uno una vez) y puertas
Construcción 2022-06-01→2024-07-01 · Validación 2024-07-01→2025-10-01 · **Examen sellado 2025-10-01→2026-09-29 (una sola vez)**.
Puertas Q1-Q7 idénticas a la mesa de 1 h (≥0,3 ops/día; R>0 en validación y examen; p Holm<0,10 sobre 13; R>0 con costes ×2; truncamiento; sin liquidación y caída<40 %; Sharpe<6).
Un aprendiz «mejora» a su base si R media(A o C) > R media(B) en validación Y en examen con ≥ 30 operaciones; no se adopta nada sin prerregistro nuevo y aprobación del dueño.
Se informan sensibilidad a costes ×1,5/×2/×3 y banda de Monte Carlo del examen.

## Hacia delante
Papel, Deribit 15 min, inicio 2026-10-02 00:00 UTC. Se recalcula desde el inicio en cada ejecución (idempotente) dentro de la rutina horaria
(las decisiones son idénticas a ejecutarlo cada 15 min: la simulación entra en la apertura de la vela siguiente; solo la frescura del panel es de hasta 1 h).
Los aprendices hacia delante continúan aprendiendo con las operaciones nuevas de la base. Dinero real: nada de esto, solo con certificación, ≥150 operaciones hacia delante, p ≥ 0,90 y aprobación EXPRESA del dueño.
Aviso honesto: stops de 15 min son más estrechos y los costes pesan más en R que en 1 h; es plausible que el resultado sea peor. La prueba existe para medirlo.
