# Informe semanal de Millonary · 2026-10-11

## Resumen

- Patrimonio: **984.10 USDT** (inicio 999.59) · retorno de la prueba -1.55% · **esta semana -2.36%**
- Caída máxima de la prueba 3.95% · caída actual 3.48% · exposición actual 0.25×
- Día 10 de la prueba · 62 velas de 4h procesadas (35 esta semana)
- Órdenes: 4 en total, 3 esta semana · comisiones 0.62 USDT (0.33 esta semana)
- Registro de entradas · posiciones cerradas 0: **ganan 0 / pierden 0** · abiertas 1
- Lotes (cada compra) cerrados 0: ganan 0 / pierden 0 · abiertos 2

Decisión del comité: Mantener el objetivo del núcleo: 0.38× de exposición. · Estado: AVISO

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
| S03 Bollinger + RSI (reversión) | +3.07% | 2.6% | 2 | +1 |
| S06 Cruce SMA 7-25 | +1.27% | 2.8% | 3 | -1 |
| S07 SMA 7-25 + filtro 200 (largo) | +0.08% | 2.8% | 1 | +0 |
| S13 Retroceso a EMA20 | -0.67% | 2.8% | 2 | +0 |
| S10 MACD + EMA200 | -0.72% | 3.8% | 4 | +1 |
| S14 Momentum 90 d | -1.33% | 6.3% | 1 | +1 |
| S02 Ichimoku | -1.41% | 4.8% | 3 | -1 |
| S05 RSI(2) retroceso (largo) | -2.18% | 3.8% | 1 | +0 |
| S11 Supertrend 10/3 | -2.46% | 4.4% | 3 | -1 |
| S15 RSI14 + EMA200 | -2.78% | 5.5% | 2 | -1 |
| S08 Canal 20 por tercios | -2.86% | 4.4% | 9 | +0 |
| S09 Donchian 20/10 | -3.77% | 5.7% | 3 | -1 |
| S12 Expansión de volatilidad | -3.91% | 4.9% | 5 | -1 |
| S04 Keltner ruptura | -4.09% | 4.8% | 3 | -1 |
| S01 Parabolic SAR + EMA200 | -5.59% | 6.5% | 5 | +1 |

## Perfeccionamiento continuo (Laboratorio)

Pruebas acumuladas en el ciclo de mejora: 75. Candidatas por etapa: E3 sombra: 21, descartada (E1/E2): 54.
Adoptables (E4, solo en sombra): ninguna todavía (exigen ≥ 90 días hacia delante, ΔSharpe ≥ +0,3, caída ≤ 1,2× y p < 0,10 con Holm).

| Candidata | Días | ΔSharpe hacia delante | Retorno base → variante |
|---|---|---|---|
| S03 Bollinger + RSI (reversión)|O2 solo largos | 11 | +3.55 | +3.07% → +1.88% |
| S15 RSI14 + EMA200|O2 solo largos | 11 | +3.45 | -2.78% → -0.79% |
| S10 MACD + EMA200|O2 solo largos | 11 | +2.30 | -0.72% → +0.34% |
| S09 Donchian 20/10|O2 solo largos | 11 | +0.33 | -3.77% → -2.44% |
| S08 Canal 20 por tercios|O3 tamaño por volatilidad | 11 | +0.21 | -2.86% → -2.05% |

*Todo lo anterior es simulación en papel. Ningún agente ni candidata toca capital; solo el núcleo validado opera y solo Riesgos puede vetar.*
