# Informe semanal de Millonary · 2026-10-09

## Resumen

- Patrimonio: **996.89 USDT** (inicio 999.59) · retorno de la prueba -0.27% · **esta semana -1.57%**
- Caída máxima de la prueba 2.23% · caída actual 2.23% · exposición actual 0.75×
- Día 8 de la prueba · 50 velas de 4h procesadas (35 esta semana)
- Órdenes: 2 en total, 1 esta semana · comisiones 0.38 USDT (0.08 esta semana)
- Registro de entradas · posiciones cerradas 0: **ganan 0 / pierden 0** · abiertas 1
- Lotes (cada compra) cerrados 0: ganan 0 / pierden 0 · abiertos 2

Decisión del comité: Mantener el objetivo del núcleo: 0.76× de exposición. · Estado: OK

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
| S03 Bollinger + RSI (reversión) | +1.18% | 2.6% | 1 | +0 |
| S10 MACD + EMA200 | +0.73% | 2.4% | 2 | +0 |
| S06 Cruce SMA 7-25 | +0.47% | 2.8% | 3 | -1 |
| S07 SMA 7-25 + filtro 200 (largo) | +0.08% | 2.8% | 1 | +0 |
| S14 Momentum 90 d | -0.47% | 3.7% | 1 | +1 |
| S13 Retroceso a EMA20 | -0.67% | 2.8% | 2 | +0 |
| S15 RSI14 + EMA200 | -0.79% | 2.8% | 1 | +0 |
| S05 RSI(2) retroceso (largo) | -1.04% | 1.0% | 1 | +1 |
| S12 Expansión de volatilidad | -1.94% | 2.4% | 4 | +0 |
| S02 Ichimoku | -2.19% | 4.8% | 3 | -1 |
| S08 Canal 20 por tercios | -3.13% | 4.4% | 8 | -1 |
| S11 Supertrend 10/3 | -3.23% | 4.4% | 3 | -1 |
| S01 Parabolic SAR + EMA200 | -3.79% | 4.4% | 3 | +0 |
| S04 Keltner ruptura | -4.14% | 4.1% | 2 | +0 |
| S09 Donchian 20/10 | -4.53% | 5.7% | 3 | -1 |

## Perfeccionamiento continuo (Laboratorio)

Pruebas acumuladas en el ciclo de mejora: 75. Candidatas por etapa: E3 sombra: 21, descartada (E1/E2): 54.
Adoptables (E4, solo en sombra): ninguna todavía (exigen ≥ 90 días hacia delante, ΔSharpe ≥ +0,3, caída ≤ 1,2× y p < 0,10 con Holm).

*Todo lo anterior es simulación en papel. Ningún agente ni candidata toca capital; solo el núcleo validado opera y solo Riesgos puede vetar.*
