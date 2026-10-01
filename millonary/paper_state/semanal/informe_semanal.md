# Informe semanal de Millonary · 2026-10-01

## Resumen

- Patrimonio: **999.54 USDT** (inicio 999.59) · retorno de la prueba -0.01% · **esta semana -0.01%**
- Caída máxima de la prueba 0.37% · caída actual 0.37% · exposición actual 0.59×
- Día 1 de la prueba · 8 velas de 4h procesadas (8 esta semana)
- Órdenes: 1 en total, 1 esta semana · comisiones 0.29 USDT (0.29 esta semana)
- Registro de entradas · posiciones cerradas 0: **ganan 0 / pierden 0** · abiertas 1
- Lotes (cada compra) cerrados 0: ganan 0 / pierden 0 · abiertos 1

Decisión del comité: Mantener el objetivo del núcleo: 0.62× de exposición. · Estado: OK

## Puertas del protocolo (paso a dinero real mínimo)

- [NO] G1_replica
- [OK] G2_integridad
- [OK] G3_envolvente
- [OK] G4_no_anomalo
- [OK] G5_registro_cuadra

> Un mes no demuestra rentabilidad: el sistema tiene ~0,46 posiciones cerradas al mes y ~27 % de acierto con ganancias ~9× la pérdida media; con ventaja real, 5 de cada 10 meses terminan en pérdida.

## Incubadora de traders (sombra, sin capital)

Certificadas en el examen: 0/15.

| Trader | Retorno hacia delante | Caída | Ops | Posición |
|---|---|---|---|---|
| S02 Ichimoku | +0.00% | 0.0% | 0 | +0 |
| S03 Bollinger + RSI (reversión) | +0.00% | 0.0% | 0 | +0 |
| S04 Keltner ruptura | +0.00% | 0.0% | 0 | +0 |
| S05 RSI(2) retroceso (largo) | +0.00% | 0.0% | 0 | +0 |
| S07 SMA 7-25 + filtro 200 (largo) | +0.00% | 0.0% | 0 | +0 |
| S15 RSI14 + EMA200 | +0.00% | 0.0% | 0 | +0 |
| S06 Cruce SMA 7-25 | -0.08% | 1.0% | 1 | -1 |
| S09 Donchian 20/10 | -0.08% | 1.0% | 1 | -1 |
| S11 Supertrend 10/3 | -0.08% | 1.0% | 1 | -1 |
| S01 Parabolic SAR + EMA200 | -0.08% | 0.6% | 1 | +1 |
| S14 Momentum 90 d | -0.08% | 0.6% | 1 | +1 |
| S10 MACD + EMA200 | -0.45% | 0.6% | 1 | +1 |
| S13 Retroceso a EMA20 | -0.45% | 0.6% | 1 | +1 |
| S12 Expansión de volatilidad | -0.71% | 0.7% | 1 | +0 |
| S08 Canal 20 por tercios | -0.88% | 0.9% | 1 | +0 |

## Perfeccionamiento continuo (Laboratorio)

Pruebas acumuladas en el ciclo de mejora: 75. Candidatas por etapa: E3 sombra: 21, descartada (E1/E2): 54.
Adoptables (E4, solo en sombra): ninguna todavía (exigen ≥ 90 días hacia delante, ΔSharpe ≥ +0,3, caída ≤ 1,2× y p < 0,10 con Holm).

*Todo lo anterior es simulación en papel. Ningún agente ni candidata toca capital; solo el núcleo validado opera y solo Riesgos puede vetar.*
