# Mesa de fondos (estrategias célebres de fondos y traders) · Prerregistro v1 — antes de ejecutar nada sobre datos reales

Fecha 2026-10-02. Petición del dueño: «poner a todos a trabajar con las estrategias matemáticamente probadas que usan los grandes fondos y
las personas que han ganado millones». Sistema aparte (`src/fondos/`, `paper_state/fondos/`); núcleo v1, incubadora y mesas intradía no se tocan.
Código fijo en este commit: `src/fondos/estrategias.py` (reglas), `src/fondos/data.py` (datos), `src/fondos/evaluar.py` (contraste).
**Ningún parámetro se ha elegido mirando BTC: son los publicados por sus autores.** Cambiar algo tras ejecutar = prueba nueva en el registro.

## Universo (10 pruebas nuevas: n.º 252–261 del registro)
| # | Estrategia | Fuente | Regla (velas diarias UTC) |
|---|---|---|---|
| F01 | Tortugas, Sistema 1 | R. Dennis y W. Eckhardt (1983); C. Faith, *Way of the Turtle* (2007) | Ruptura stop de 20 d (largo/corto); N = ATR Wilder 20; unidad = 0,25 % del capital por N (= 0,5 % de riesgo a 2N); +1 unidad cada ½N hasta 4; stop 2N de la última; salida canal 10 d; se salta la ruptura si la anterior fue ganadora salvo ruptura de 55 d |
| F02 | Tortugas, Sistema 2 | ídem | Ruptura 55 d, salida canal 20 d, sin regla de salto |
| F03 | Momentum de series temporales 12 m | Moskowitz, Ooi y Pedersen (JFE 2012); AQR / CTA | Signo del retorno de 365 d × (25 % / σ EWMA com 60 d), tope 2×; reajuste a fin de mes; largo y corto |
| F04 | Media de 200 días | Paul Tudor Jones; Faber (2007) | Largo 1× si cierre > SMA 200; fuera si no |
| F05 | Ruptura de volatilidad | Larry Williams (1999; Robbins Cup 1987) | Compra stop en apertura + 0,5 × rango de ayer; sale al cierre del día; solo largos; 1× |
| F06 | Carry de funding (cash-and-carry) | Schmeling, Schrimpf y Todorov, *Crypto carry* (BIS WP 1087, 2023) | Largo contado + corto perpetuo (mismos BTC) si la media del funding de 7 d > 0; nocional 1×, banda de reajuste 20 %; desde 2020 (requiere perpetuo) |
| F07 | Cartera gestionada por volatilidad | Moreira y Muir (JF 2017) | Peso = media expansiva de varianzas mensuales / varianza del último mes (≥ 12 meses de historia), tope 2×, reajuste mensual, solo largos |
| F08 | Turtle Soup +1 | L. B. Raschke y L. Connors, *Street Smarts* (1995) | Día t: nuevo mínimo de 20 d con cierre ≤ mínimo anterior (de hace ≥ 3 d); t+1 compra stop en ese mínimo; stop bajo el mínimo de t; salida al cierre del 3.er día; espejo corto; riesgo 0,5 % |
| F09 | NR7 | Toby Crabel (1990) | Tras el día de rango más estrecho de 7: stops OCO en su máximo/mínimo; stop en el extremo contrario; salida al cierre; riesgo 0,5 % |
| F10 | Cartera multiestrategia | práctica de fondos multiestrategia (paridad de riesgo) | F01–F09 con peso ∝ 1/σ de 90 d, decidido a fin de mes, suma 1; coste del reajuste incluido |

Supuestos de ejecución (iguales para todas): niveles stop conocidos al abrir el día; cuando un día toca dos niveles se asume el orden PEOR
(entrada/añadido antes que el stop); perpetuo 5 pb + 2 pb por lado, contado 10 pb + 2 pb; funding real desde 2020 (sintético 0,01 %/8 h antes),
los largos lo pagan si siguen abiertos al cierre; exposición direccional nunca > 2× al abrir el día. Adaptaciones obligadas por las reglas del
proyecto (no por los datos): riesgo 0,5 % por operación (decisión #9; las Tortugas usaban 2 % por unidad a 2N: solo cambia la escala, no el Sharpe),
c causal en Moreira-Muir (el artículo usa toda la muestra) y día UTC como «sesión».

## Datos y periodos
Contado BTCUSDT de Binance (4 h → diario, con el empalme de feb-2018 del núcleo) 2017-08 → último día cerrado; perpetuo y funding desde 2020-01.
Evaluación desde 2018-09-01 (calentamiento de 365 d); carry desde 2020-01-01. Subperiodos: A 2018-09→2019-12 · B 2020-01→2023-12 · C 2024-01→hoy.
No hay entrenamiento: nada se ajusta, así que toda la muestra es fuera de muestra respecto a los parámetros. Aviso honesto: estas fechas ya se
usaron en otras pruebas del proyecto y estas estrategias son célebres PORQUE funcionaron en su época (sesgo de supervivencia de la fama);
por eso se exige corrección por comparaciones múltiples y confirmación hacia delante.

## Contraste (`src/fondos/evaluar.py`, ejecución única)
Retornos diarios netos. C1 Sharpe > 0 y p unilateral de la media diaria (HAC, 5 retardos) con Holm sobre las 10 < 0,10 · C2 Sharpe > 0 en cada
subperiodo · C3 Sharpe > 0 con costes ×2 · C4 Deflated Sharpe ≥ 0,80 con n = 251 + 10 = 261 pruebas y varianza del Sharpe bajo la nula (1/T)
(la transversal se informa: estas 10 mezclan familias de escala muy distinta) · C5 ≥ 30 operaciones o reajustes.
**Certificada = C1–C5.** Diagnóstico aparte (no decide): «aporta al núcleo» si la mezcla 50/50 en riesgo con el núcleo v1 tiene más Sharpe que
el núcleo solo en el mismo periodo; correlación con el núcleo, α frente a BTC y al factor de tendencia, Kelly completo (μ/σ²; nunca se usa más de ¼–½).

## Hacia delante (papel)
Inicio 2026-10-03 00:00 UTC (primeras decisiones con el cierre del 2026-10-02), 1.000 USDT por estrategia, recálculo completo en cada ejecución
(rutina horaria; los datos diarios de Binance Vision llegan con ≤ 1 día de retraso). Lote fino en papel: con 1.000 USDT reales las unidades de las
Tortugas (~70 USDT) quedarían bajo el nocional mínimo de 100 USDT.
**Dinero real: nada.** Solo con certificación histórica, ≥ 90 días hacia delante sin desviarse de su envolvente y aprobación EXPRESA del dueño.
