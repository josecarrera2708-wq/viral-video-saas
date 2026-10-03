# Fase 2 · lote 2 · entrada maker (orden límite) en las 40 traders base · resultados históricos

Certificadas: **0/40** · maker mejora R en validación Y examen: **32/40** · pruebas acumuladas 309

| Periodo | R medio taker | R medio maker | llenado | traders con R>0 taker → maker |
|---|---|---|---|---|
| construccion | -0.194 | -0.159 | 94% | 0 → 1 |
| validacion | -0.171 | -0.137 | 94% | 6 → 6 |
| examen | -0.207 | -0.168 | 94% | 1 → 2 |

| Trader | llenado ex. | R valid. taker → maker | R examen taker → maker | ops/día ex. maker | R ×2 costes | p Holm | Puertas | Cert. |
|---|---|---|---|---|---|---|---|---|
| intradia · I01 Rango asiático → Londres/NY | 96% | -0.077 → -0.050 | -0.131 → -0.097 | 0.77 | -0.174 | 1.00 | 2/5 | — |
| intradia · I02 Ruptura Donchian 24 h | 96% | -0.024 → -0.026 | -0.099 → -0.099 | 0.92 | -0.175 | 1.00 | 2/5 | — |
| intradia · I03 Bollinger + RSI (reversión) | 97% | -0.192 → -0.161 | -0.175 → -0.168 | 0.62 | -0.235 | 1.00 | 2/5 | — |
| intradia · I04 Reversión a VWAP diaria | 97% | -0.169 → -0.146 | -0.157 → -0.140 | 1.14 | -0.212 | 1.00 | 2/5 | — |
| intradia · I05 Cruce EMA 9/21 + EMA200 | 98% | +0.019 → +0.043 | -0.147 → -0.098 | 0.49 | -0.199 | 1.00 | 2/5 | — |
| intradia · I06 RSI(2) retroceso | 96% | -0.105 → -0.074 | -0.107 → -0.069 | 0.93 | -0.139 | 1.00 | 2/5 | — |
| intradia · I07 Ruptura tras squeeze | 94% | +0.003 → +0.019 | -0.093 → -0.051 | 0.31 | -0.153 | 1.00 | 2/5 | — |
| intradia · I08 Ruptura del máx./mín. de ayer | 98% | +0.000 → +0.001 | -0.128 → -0.039 | 0.66 | -0.137 | 1.00 | 2/5 | — |
| intradia · I09 Supertrend 10/3 | 96% | +0.101 → +0.126 | -0.219 → -0.153 | 0.44 | -0.225 | 1.00 | 2/5 | — |
| intradia · I10 Ráfaga de momentum | 95% | -0.050 → -0.078 | -0.181 → -0.132 | 0.59 | -0.267 | 1.00 | 2/5 | — |
| intradia · I11 Ruptura fallida | 95% | -0.149 → -0.108 | -0.220 → -0.193 | 1.54 | -0.329 | 1.00 | 2/5 | — |
| intradia · I12 Ichimoku 1 h | 98% | +0.043 → +0.060 | -0.048 → -0.045 | 0.41 | -0.117 | 1.00 | 2/5 | — |
| intradia · I13 Parabolic SAR + EMA200 | 96% | +0.017 → +0.043 | -0.056 → -0.042 | 0.89 | -0.131 | 1.00 | 2/5 | — |
| intradia · I14 Apertura de Nueva York | 98% | -0.178 → -0.181 | -0.150 → -0.120 | 0.47 | -0.218 | 1.00 | 2/5 | — |
| mesa15 · P01 Envolvente en soporte/resistencia | 93% | -0.338 → -0.277 | -0.363 → -0.270 | 0.69 | -0.454 | 1.00 | 2/5 | — |
| mesa15 · P02 Pin bar en techo/suelo | 88% | -0.536 → -0.437 | -0.520 → -0.428 | 1.60 | -0.676 | 1.00 | 1/5 | — |
| mesa15 · P03 Barrido de liquidez | 90% | -0.391 → -0.295 | -0.382 → -0.302 | 1.96 | -0.519 | 1.00 | 1/5 | — |
| mesa15 · P04 Ineficiencia (Fair Value Gap) | 88% | -0.445 → -0.363 | -0.466 → -0.383 | 3.16 | -0.679 | 1.00 | 1/5 | — |
| mesa15 · P05 Barra interior + tendencia | 89% | -0.418 → -0.330 | -0.458 → -0.400 | 2.13 | -0.637 | 1.00 | 1/5 | — |
| mesa15 · P06 Estrella de mañana/tarde | 94% | -0.338 → -0.235 | -0.349 → -0.324 | 0.31 | -0.496 | 1.00 | 2/5 | — |
| mesa15 · P07 Doble techo/suelo | 87% | -0.248 → -0.212 | -0.189 → -0.118 | 0.63 | -0.262 | 1.00 | 2/5 | — |
| mesa15 · Q01 Momentum de series temporales | 90% | -0.246 → -0.186 | -0.243 → -0.161 | 0.66 | -0.293 | 1.00 | 2/5 | — |
| mesa15 · Q02 Reversión Ornstein-Uhlenbeck | 91% | -0.289 → -0.238 | -0.315 → -0.229 | 1.16 | -0.350 | 1.00 | 2/5 | — |
| mesa15 · Q03 Régimen por razón de varianzas | 92% | -0.336 → -0.277 | -0.267 → -0.202 | 0.91 | -0.353 | 1.00 | 2/5 | — |
| mesa15 · Q04 Expansión de volatilidad Garman-Klass | 91% | -0.101 → -0.059 | -0.150 → -0.187 | 0.65 | -0.326 | 1.00 | 2/5 | — |
| mesa15 · Q05 Desequilibrio de flujo | 92% | -0.206 → -0.197 | -0.098 → -0.128 | 0.47 | -0.271 | 1.00 | 2/5 | — |
| mesa15 · Q06 CTA EMA 96/384 + ADX | 91% | -0.141 → -0.010 | -0.380 → -0.324 | 0.20 | -0.499 | 1.00 | 1/5 | — |
| mesa1h · P01 Envolvente en soporte/resistencia | 93% | -0.237 → -0.163 | -0.264 → -0.231 | 0.55 | -0.351 | 1.00 | 2/5 | — |
| mesa1h · P02 Pin bar en techo/suelo | 95% | -0.300 → -0.235 | -0.243 → -0.183 | 0.99 | -0.326 | 1.00 | 2/5 | — |
| mesa1h · P03 Barrido de liquidez | 93% | -0.102 → -0.063 | -0.240 → -0.223 | 1.14 | -0.359 | 1.00 | 2/5 | — |
| mesa1h · P04 Ineficiencia (Fair Value Gap) | 91% | -0.152 → -0.124 | -0.173 → -0.133 | 0.79 | -0.261 | 1.00 | 2/5 | — |
| mesa1h · P05 Barra interior + tendencia | 93% | -0.222 → -0.171 | -0.240 → -0.205 | 0.66 | -0.326 | 1.00 | 2/5 | — |
| mesa1h · P06 Estrella de mañana/tarde | 92% | -0.380 → -0.371 | -0.272 → -0.268 | 0.10 | -0.381 | 1.00 | 1/5 | — |
| mesa1h · P07 Doble techo/suelo | 93% | -0.116 → -0.058 | -0.034 → +0.003 | 0.60 | -0.071 | 1.00 | 2/5 | — |
| mesa1h · Q01 Momentum de series temporales | 94% | -0.063 → -0.031 | +0.000 → +0.016 | 0.42 | -0.056 | 1.00 | 2/5 | — |
| mesa1h · Q02 Reversión Ornstein-Uhlenbeck | 97% | -0.154 → -0.129 | -0.106 → -0.072 | 0.27 | -0.143 | 1.00 | 1/5 | — |
| mesa1h · Q03 Régimen por razón de varianzas | 97% | -0.081 → -0.057 | -0.181 → -0.153 | 0.75 | -0.232 | 1.00 | 2/5 | — |
| mesa1h · Q04 Expansión de volatilidad Garman-Klass | 95% | -0.060 → -0.111 | -0.084 → -0.069 | 0.50 | -0.161 | 1.00 | 2/5 | — |
| mesa1h · Q05 Desequilibrio de flujo | 93% | -0.036 → -0.041 | -0.133 → -0.154 | 0.43 | -0.239 | 1.00 | 2/5 | — |
| mesa1h · Q06 CTA EMA 96/384 + ADX | 94% | -0.131 → -0.268 | -0.208 → -0.161 | 0.12 | -0.240 | 1.00 | 1/5 | — |

Periodos propios de cada mesa (intradía: examen 2025-07→2026-09; 15 min y 1 h: examen 2025-10→2026-09). Los exámenes ya se habían abierto: es una segunda mirada.
