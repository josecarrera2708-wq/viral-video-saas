# Informe semanal de Millonary · 2026-10-05

## Resumen

- Patrimonio: **1,007.30 USDT** (inicio 999.59) · retorno de la prueba +0.77% · **esta semana +0.77%**
- Caída máxima de la prueba 1.45% · caída actual 1.15% · exposición actual 0.59×
- Día 4 de la prueba · 26 velas de 4h procesadas (26 esta semana)
- Órdenes: 1 en total, 1 esta semana · comisiones 0.29 USDT (0.29 esta semana)
- Registro de entradas · posiciones cerradas 0: **ganan 0 / pierden 0** · abiertas 1
- Lotes (cada compra) cerrados 0: ganan 0 / pierden 0 · abiertos 1

Decisión del comité: Mantener el objetivo del núcleo: 0.64× de exposición. · Estado: OK

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
| S03 Bollinger + RSI (reversión) | +1.87% | 0.7% | 1 | -1 |
| S14 Momentum 90 d | +1.25% | 2.4% | 1 | +1 |
| S07 SMA 7-25 + filtro 200 (largo) | +0.89% | 2.4% | 1 | +1 |
| S10 MACD + EMA200 | +0.56% | 2.4% | 1 | +0 |
| S06 Cruce SMA 7-25 | +0.38% | 2.4% | 2 | +1 |
| S13 Retroceso a EMA20 | +0.13% | 2.4% | 2 | +1 |
| S15 RSI14 + EMA200 | +0.00% | 2.4% | 1 | +1 |
| S05 RSI(2) retroceso (largo) | +0.00% | 0.0% | 0 | +0 |
| S02 Ichimoku | -0.23% | 2.4% | 1 | +1 |
| S01 Parabolic SAR + EMA200 | -1.36% | 2.4% | 2 | +0 |
| S08 Canal 20 por tercios | -1.37% | 1.7% | 4 | +0 |
| S12 Expansión de volatilidad | -1.81% | 2.4% | 3 | +0 |
| S04 Keltner ruptura | -2.58% | 2.6% | 1 | +0 |
| S11 Supertrend 10/3 | -3.33% | 4.1% | 2 | +1 |
| S09 Donchian 20/10 | -4.63% | 5.4% | 2 | +1 |

## Perfeccionamiento continuo (Laboratorio)

Pruebas acumuladas en el ciclo de mejora: 75. Candidatas por etapa: E3 sombra: 21, descartada (E1/E2): 54.
Adoptables (E4, solo en sombra): ninguna todavía (exigen ≥ 90 días hacia delante, ΔSharpe ≥ +0,3, caída ≤ 1,2× y p < 0,10 con Holm).

*Todo lo anterior es simulación en papel. Ningún agente ni candidata toca capital; solo el núcleo validado opera y solo Riesgos puede vetar.*
