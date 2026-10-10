# Informe semanal de Millonary · 2026-10-10

## Resumen

- Patrimonio: **981.53 USDT** (inicio 999.59) · retorno de la prueba -1.81% · **esta semana -2.52%**
- Caída máxima de la prueba 3.95% · caída actual 3.74% · exposición actual 0.25×
- Día 9 de la prueba · 56 velas de 4h procesadas (35 esta semana)
- Órdenes: 4 en total, 3 esta semana · comisiones 0.62 USDT (0.33 esta semana)
- Registro de entradas · posiciones cerradas 0: **ganan 0 / pierden 0** · abiertas 1
- Lotes (cada compra) cerrados 0: ganan 0 / pierden 0 · abiertos 2

Decisión del comité: Mantener el objetivo del núcleo: 0.28× de exposición. · Estado: OK

## Puertas del protocolo (paso a dinero real mínimo)

- [OK] G1_replica
- [OK] G2_integridad
- [OK] G3_envolvente
- [OK] G4_no_anomalo
- [OK] G5_registro_cuadra

> Un mes no demuestra rentabilidad: el sistema tiene ~0,46 posiciones cerradas al mes y ~27 % de acierto con ganancias ~9× la pérdida media; con ventaja real, 5 de cada 10 meses terminan en pérdida.

## Incubadora de traders (sombra, sin capital)

Certificadas en el examen: 0/15.

| Trader | Retorno hacia delante | Caída | Ops | Posición |
|---|---|---|---|---|
| S06 Cruce SMA 7-25 | +2.35% | 2.8% | 3 | -1 |
| S03 Bollinger + RSI (reversión) | +2.00% | 2.6% | 2 | +1 |
| S07 SMA 7-25 + filtro 200 (largo) | +0.08% | 2.8% | 1 | +0 |
| S10 MACD + EMA200 | -0.33% | 3.1% | 3 | +0 |
| S02 Ichimoku | -0.36% | 4.8% | 3 | -1 |
| S13 Retroceso a EMA20 | -0.67% | 2.8% | 2 | +0 |
| S08 Canal 20 por tercios | -1.32% | 4.4% | 8 | -1 |
| S11 Supertrend 10/3 | -1.41% | 4.4% | 3 | -1 |
| S15 RSI14 + EMA200 | -1.75% | 3.8% | 2 | -1 |
| S14 Momentum 90 d | -2.35% | 6.3% | 1 | +1 |
| S09 Donchian 20/10 | -2.74% | 5.7% | 3 | -1 |
| S12 Expansión de volatilidad | -2.88% | 3.2% | 5 | -1 |
| S05 RSI(2) retroceso (largo) | -2.91% | 3.8% | 1 | +1 |
| S04 Keltner ruptura | -3.07% | 4.5% | 3 | -1 |
| S01 Parabolic SAR + EMA200 | -4.81% | 5.4% | 4 | +0 |

## Perfeccionamiento continuo (Laboratorio)

Pruebas acumuladas en el ciclo de mejora: 75. Candidatas por etapa: E3 sombra: 21, descartada (E1/E2): 54.
Adoptables (E4, solo en sombra): ninguna todavía (exigen ≥ 90 días hacia delante, ΔSharpe ≥ +0,3, caída ≤ 1,2× y p < 0,10 con Holm).

| Candidata | Días | ΔSharpe hacia delante | Retorno base → variante |
|---|---|---|---|
| S01 Parabolic SAR + EMA200|O3 tamaño por volatilidad | 10 | +0.00 | -4.81% → -3.59% |
| S02 Ichimoku|O2 solo largos | 10 | +0.00 | -0.36% → -3.07% |
| S02 Ichimoku|O3 tamaño por volatilidad | 10 | +0.00 | -0.36% → -0.24% |
| S03 Bollinger + RSI (reversión)|O2 solo largos | 10 | +0.00 | +2.00% → +0.82% |
| S03 Bollinger + RSI (reversión)|O4 stop 3×ATR | 10 | +0.00 | +2.00% → +0.53% |

*Todo lo anterior es simulación en papel. Ningún agente ni candidata toca capital; solo el núcleo validado opera y solo Riesgos puede vetar.*
