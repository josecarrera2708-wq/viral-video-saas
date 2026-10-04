# Informe semanal de Millonary · 2026-10-04

## Resumen

- Patrimonio: **1,005.73 USDT** (inicio 999.59) · retorno de la prueba +0.61% · **esta semana +0.61%**
- Caída máxima de la prueba 1.45% · caída actual 1.30% · exposición actual 0.59×
- Día 3 de la prueba · 20 velas de 4h procesadas (20 esta semana)
- Órdenes: 1 en total, 1 esta semana · comisiones 0.29 USDT (0.29 esta semana)
- Registro de entradas · posiciones cerradas 0: **ganan 0 / pierden 0** · abiertas 1
- Lotes (cada compra) cerrados 0: ganan 0 / pierden 0 · abiertos 1

Decisión del comité: Mantener el objetivo del núcleo: 0.63× de exposición. · Estado: OK

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
| S03 Bollinger + RSI (reversión) | +2.15% | 0.3% | 1 | -1 |
| S14 Momentum 90 d | +0.98% | 2.4% | 1 | +1 |
| S07 SMA 7-25 + filtro 200 (largo) | +0.63% | 2.4% | 1 | +1 |
| S10 MACD + EMA200 | +0.60% | 2.4% | 1 | +1 |
| S06 Cruce SMA 7-25 | +0.11% | 2.4% | 2 | +1 |
| S05 RSI(2) retroceso (largo) | +0.00% | 0.0% | 0 | +0 |
| S13 Retroceso a EMA20 | -0.13% | 2.4% | 2 | +1 |
| S15 RSI14 + EMA200 | -0.26% | 2.4% | 1 | +1 |
| S02 Ichimoku | -0.49% | 2.4% | 1 | +1 |
| S08 Canal 20 por tercios | -1.30% | 1.6% | 4 | +0 |
| S01 Parabolic SAR + EMA200 | -1.62% | 2.4% | 2 | +1 |
| S12 Expansión de volatilidad | -1.92% | 2.4% | 3 | +1 |
| S04 Keltner ruptura | -2.58% | 2.6% | 1 | +0 |
| S11 Supertrend 10/3 | -3.59% | 4.1% | 2 | +1 |
| S09 Donchian 20/10 | -4.88% | 5.4% | 2 | +1 |

## Perfeccionamiento continuo (Laboratorio)

Pruebas acumuladas en el ciclo de mejora: 75. Candidatas por etapa: E3 sombra: 21, descartada (E1/E2): 54.
Adoptables (E4, solo en sombra): ninguna todavía (exigen ≥ 90 días hacia delante, ΔSharpe ≥ +0,3, caída ≤ 1,2× y p < 0,10 con Holm).

*Todo lo anterior es simulación en papel. Ningún agente ni candidata toca capital; solo el núcleo validado opera y solo Riesgos puede vetar.*
