# Cazador de traders: setups intradía 2:1/3:1 traducidos a reglas mecánicas

**Método.** Leí el motor y el código de lo ya probado. No usé datos de BTC. Vi de pasada el resumen de la mesa de 15 min, que coincide con el CONTEXTO, y no saqué de él ningún parámetro. Las cifras propias son **sintéticas**: un paseo aleatorio GARCH-t con volatilidad diaria del 3 %, en `scratchpad/agentes/cazador_sim/cazador_sim_fvg.py`.

## 1. Conclusiones
1. No hay backtests mecánicos de ICT/SMC revisados por pares. Los independientes (oro, NQ, divisas G10, ETF) dan R ≤ 0, y el más sistemático ve que tras un barrido el precio **continúa** [1-4].
2. Un 70-80 % de acierto a 2R es marketing: supondría ganar de +1,1 a +1,4 R por operación. Sin ventaja se acierta 1/3, y un 27 % con salida a 4 h (simulación). Como referencia, el 97 % de los day traders persistentes de futuros brasileños pierde [21], y solo un 7 % de 300.000 cuentas de prop firms cobra [22].
3. «Los FVG se rellenan el 80 %» es la tasa base. En la simulación se revisita el 84 % en 20 velas, frente al 83 % de un nivel espejo. Un control con barras al azar daría un 76 %, que es un falso efecto de +7 puntos. Entrar en el FVG acierta el 27 % a 2R, igual que entrar al azar.
4. La única evidencia positiva con reglas claras es el ORB, y algo el VWAP, en acciones de EE. UU. [5-7]. Su ventaja, unos +0,08 R por operación, no paga nuestro coste de 0,2-0,4 R.
5. A lo ya probado le faltaba la forma: la secuencia, la hora de Nueva York con su cambio de horario, la entrada con límite y el objetivo en la liquidez opuesta. Abajo se corrige, aunque las probabilidades de partida siguen siendo bajas.

## 2. Reglas comunes
**Acierto mínimo para R media = 0**, con los costes del motor (el TP sale como maker y el stop como taker):

| Stop | Entrada al cierre (taker) 2R / 3R | Entrada con límite (maker) 2R / 3R |
|---|---|---|
| 0,35 % | 44,5 / 33,8 % | 40,0 / 30,3 % |
| 0,60 % | 40,0 / 30,2 % | 37,3 / 28,2 % |
| 1,00 % | 37,4 / 28,1 % | 35,7 / 26,9 % |

**Horario.** Se usa `tz_convert("America/New_York")` y nunca un UTC fijo. El horario de verano de EE. UU. va del 2.º domingo de marzo al 1.er domingo de noviembre.

| Hora de NY | UTC en verano / invierno |
|---|---|
| Asia, 20-00 | 00-04 / 01-05 |
| Killzone de Londres, 02-05 | 06-09 / 07-10 |
| Killzone de NY, 07-10 | 11-14 / 12-15 |
| Apertura, 09:30 | 13:30 / 14:30 |
| Silver Bullet 03-04, 10-11 y 14-15 | 07-08, 14-15, 18-19 / 08-09, 15-16, 19-20 |

**Causalidad.** Un pivote de k velas se conoce en j+k (k=3 en 5 y 15 m; k=2 en 4 h). Un FVG se conoce al cerrar su 3.ª vela, y un nivel de sesión al cerrar la sesión. El volumen relativo (VolRel) se mide contra los 14 días hábiles anteriores.

**Ejecución.**
- **A**: entrada en la apertura siguiente a la señal, como hace el motor actual.
- **B**: orden límite en el nivel del setup, con caducidad. Hay que ampliar `src/maker/engine.py`. Se llena solo si el precio cruza el límite en 1 pb, y el TP no cuenta en esa vela.

**Para todos los setups.**
- TP de 2R o 3R.
- Salida por tiempo a las 4 h, salvo que se indique otra.
- Una operación por ventana o por día.
- De lunes a viernes, salvo los setups 3 y 7.
- Stop válido entre 0,35 % y 1,0 %. Fuera de ese rango no se opera, y el stop no se ensancha.
- Como máximo, 2R/3R × A/B por setup.

**Poder estadístico.** A 2R, con Holm sobre 8 pruebas, detectar +0,2 R exige unas 260 operaciones, y +0,1 R unas 1.040.

## 3. Setups, de más a menos evidencia y facilidad de mecanizar

### 1) ORB de Nueva York con volumen relativo
**a)** Es el sistema de Crabel y Zarattini-Aziz. Se opera la ruptura del rango de los primeros minutos tras las 09:30 NY, en su misma dirección y con el stop al otro lado. Solo se aplica a valores «en juego», con VolRel alto.

**b)** Velas de 5 m, sin festivos NYSE:
- Rango de apertura (RA): de 09:30 a 09:45 NY.
- Filtro: VolRel(RA) ≥ 1, el umbral del paper; la variante pide ≥ 2.
- Si el RA cierra por encima de su apertura, solo largos; si cierra por debajo, solo cortos.
- Señal: el primer cierre más allá del RA entre las 09:45 y las 12:00 NY.
- Stop en el otro extremo del RA.
- Versión B: límite en el borde roto, válido 6 velas.

**c)** Zarattini, Barbon y Aziz probaron más de 7.000 acciones entre 2016 y 2023, con comisiones pero sin deslizamiento [5]:

| ORB | Total | Sharpe |
|---|---|---|
| 5 m, todas las acciones | +29 % | 0,48 |
| 5 m, solo «en juego» | +1.637 % | 2,81 |
| 15 m, solo «en juego» | +272 % | 1,43 |
| 30 m, solo «en juego» | +21 % | 0,21 |

La R media por operación fue −0,02 con VolRel < 1, +0,08 con VolRel ≥ 1 y +0,38 con VolRel > 30×. En QQQ, con TP de 10R, la versión con TQQQ ganó +1.484 % [6]. En BTC no hay ningún ORB publicado fiable. Solo hay apoyo indirecto: el momentum intradía, porque la primera media hora de mucho volumen predice la última [8, 9], y la volatilidad concentrada en la apertura de EE. UU. [10]. *Fiabilidad:* media en acciones, aunque los autores venden investigación. Baja en BTC, donde solo los días de VolRel extremo pagarían el coste.

**d)** I14 usaba una vela de 1 h fija a las 13 UTC, que en invierno es la **preapertura** de NY. No tenía rango real, VolRel ni stop en el rango.

### 2) VWAP de la sesión de NY: recuperación o rechazo (+ VWAP anclado)
**a)** Lo enseñan Aziz y Shannon. Sobre el VWAP solo se buscan largos, y se compra la recuperación del VWAP perdido. El VWAP anclado (AVWAP) a un evento indica quién controla.

**b)** Velas de 5 m:
- VWAP con precio típico, anclado a las 09:30 NY. Ventana de 10:00 a 14:00 NY.
- Largo: al menos 6 cierres seguidos bajo el VWAP y después un cierre por encima, con volumen ≥ media de 20 velas. Corto simétrico.
- Stop en el extremo del tramo bajo el VWAP − 0,1·ATR(14).
- Salida también a las 16:00 NY, y una operación por lado y día.
- Variante AVWAP anclado al último pivote de 1 h. Versión B: límite en el VWAP, válido 3 velas.

**c)** En QQQ con velas de 1 min, estar largo sobre el VWAP y corto bajo él ganó +671 % entre 2018 y 2023, frente a +126 % de comprar y mantener, con Sharpe 2,1 [7]. Cambia de lado varias veces al día y gana pocos pb por operación, algo inviable con 14 pb de coste. No hay nada en BTC ni sobre AVWAP. *Fiabilidad:* baja.

**d)** I04 hacía lo contrario: reversión al VWAP de las 00 UTC.

### 3) Ruptura y retesteo de PDH/PDL
**a)** El nivel roto cambia de papel. El precio lo rompe, vuelve a él y lo rechaza.

**b)** Velas de 15 m sobre el máximo y el mínimo del día UTC anterior (PDH y PDL):
- Ruptura: cierre por encima de PDH + 0,1·ATR(14), con cuerpo de al menos el 50 % del rango.
- Retesteo, en 16 velas como máximo: mínimo ≤ PDH + 0,1·ATR y cierre por encima de PDH.
- Versión B: límite en PDH + 0,05 %, que se cancela si cierra por debajo de PDH − 0,25·ATR.
- Stop en el mínimo del retesteo − 0,1·ATR. Una operación por nivel y día.
- PDL, simétrico.

**c)** Bulkowski estudió patrones diarios en acciones entre 1991 y 2008 [11]. Si el retroceso no perfora el nivel, la subida media es del 41,3 % (1.717 casos); si lo perfora, del 26,7 % (3.311). El retesteo da mejor precio, pero selecciona las rupturas débiles. Osler halló en divisas que los niveles publicados frenan la tendencia el 60,8 % de las veces, frente al 56,2 % de los arbitrarios [12]. *Fiabilidad:* baja, porque es descriptiva.

**d)** Se probaron rupturas a mercado (I08, Donchian, rango asiático) y retesteos de la línea de cuello (v6), pero nunca el retesteo de un nivel de sesión con orden límite.

### 4) Retroceso a la EMA con estructura multitemporal y gatillo de vela
**a)** Con tendencia en 4 h, se espera un retroceso a la EMA20 de 15 m y una vela de giro.

**b)** Reglas:
- Tendencia: los dos últimos pivotes de 4 h, tanto los máximos como los mínimos, son crecientes.
- Gatillo en 15 m: mínimo ≤ EMA20 + 0,25·ATR, cierre por encima de la EMA20 y una envolvente o un pin bar (según `signals/candles.py`).
- El último máximo de pivote de 4 h debe quedar más allá del objetivo.
- Ventana de 02 a 16 NY.
- Stop en el mínimo de las últimas 5 velas − 0,1·ATR. Corto simétrico.

**c)** No hay ningún backtest intradía creíble. Las cifras de TradingView, como un PF de unos 2 en BTC a 8 h, están optimizadas sobre la propia muestra [13]. *Fiabilidad:* muy baja.

**d)** Ya está casi todo probado (S2, S4 y S5 de la búsqueda v2). Solo cambian la estructura, la ventana y el filtro de recorrido.

### 5) Silver Bullet (ICT)
**a)** Es una operación por ventana de 1 h: tras un barrido, se entra en el primer FVG de desplazamiento hacia la liquidez opuesta.

**b)** Velas de 5 m, en la ventana de 10 a 11 NY (variantes de 03 a 04 y de 14 a 15):
- Piscinas: PDH/PDL del día NY, máximos y mínimos de Asia y de Londres, y el rango de 08:30 a 10:00 NY.
- Sesgo: si entre las 09:00 y las 11:00 NY se barre una piscina inferior, largos; si se barre una superior, cortos; si se barren ambas, nada.
- Gatillo: el primer FVG a favor dentro de la ventana, con vela central de cuerpo ≥ 1·ATR(14).
- Versión B: límite en el borde cercano del FVG, que debe llenarse antes de las 11:00. Versión A: un cierre dentro del FVG que respete su borde lejano.
- Stop en el extremo del barrido ± 0,05 %.
- Solo se opera si la piscina opuesta queda más allá del objetivo. Salida a las 2 h.

**c)** En NQ de 5 m con estas reglas (junio-octubre de 2026): 34 operaciones, 32,4 % de acierto y PF de 0,68 [2]. En XAUUSD de 2020 a 2026, con barrido → MSS → FVG en las 3 ventanas y hora de NY, ninguno de 162 ajustes fue positivo a la vez en desarrollo, validación y test. A 1:2 acertó el 28,4 % con −0,35 R [1]. LuxAlgo reconoce que no hay estadísticas auditadas [14]. *Fiabilidad:* dos pruebas independientes, las dos negativas.

**d)** Nunca se probaron la ventana en hora de NY ni el sesgo por la piscina barrida.

### 6) Modelo ICT completo: barrido → MSS → FVG en killzone (+ breaker)
**a)** Tras barrer una piscina de liquidez, un desplazamiento rompe el último pivote opuesto (MSS) y deja un FVG. Se entra al 50 % del FVG, con el stop tras el barrido y el objetivo en la liquidez opuesta.

**b)** Velas de 5 m, en las killzones de Londres (02-05 NY) y de NY (07-10 NY):
- Piscinas: PDH/PDL del día NY, Asia, Londres, y máximos o mínimos iguales (dos pivotes de 15 m a ≤ 0,1·ATR en 24 h).
- Barrido: el precio supera la piscina y en 6 velas como máximo cierra de vuelta dentro.
- MSS: en 12 velas como máximo, un cierre más allá del último pivote opuesto confirmado anterior al barrido. El tramo debe contener una vela de cuerpo ≥ 1·ATR que deje un FVG.
- Versión B: límite en el 50 % del FVG hasta el final de la killzone. Versión A: un cierre dentro del FVG que respete su borde lejano.
- Stop en el extremo del barrido + 0,1·ATR.
- Solo se opera si la piscina opuesta queda más allá del objetivo.
- Breaker: límite en la última vela contraria anterior al barrido.
- Diagnóstico, no candidata: la regla invertida.

**c)**
- Mahadzva (preprint en SSRN, 2026, divisas G10) [3]: tres reglas de barrido indican **continuación** en 65 de 66 pliegues. La regla CHoCH + FVG funciona mejor invertida, con PF 1,5, aunque solo en 60 operaciones fuera de muestra.
- En XAUUSD se acertó el 57 % con −0,28 R, porque el objetivo estaba más cerca que el stop [1].
- Osler: los stops se agrupan tras los números redondos y su ejecución **acelera** el movimiento [15]. La liquidez existe, pero empuja a favor del movimiento.
- Los repositorios positivos usan 59 días en muestra y eligen la mejor de 12 combinaciones [16].

*Fiabilidad:* la evidencia es negativa.

**d)** P03 era un barrido de 96 velas a cualquier hora, y P04 un FVG suelto. Les faltaba la secuencia completa, las piscinas de sesión, la killzone, la orden límite y el objetivo en la liquidez opuesta.

### 7) Perfil de volumen: regla del 80 % y naked POC
**a)** Según Dalton y Steidlmayer, si el precio vuelve a entrar en el área de valor (VA) de ayer y se acepta dentro, la recorre hasta el otro extremo. Los POC que nadie ha vuelto a tocar (naked) atraen al precio.

**b)** Perfil del día UTC anterior, a partir de velas de 5 m:
- El volumen de cada vela se reparte uniformemente entre su mínimo y su máximo, en casillas del 0,05 %.
- La VA cubre el 70 % del volumen, ampliándose desde el POC.
- Condición: el día abre fuera de la VA y hay dos cierres seguidos de 30 min dentro antes de las 16 UTC.
- Entrada hacia el otro extremo, con stop en el extremo exterior + 0,1·ATR(1 h).
- Solo se opera si el otro extremo, o un naked POC de los últimos 5 días, queda más allá del objetivo.

**c)** No hay backtests con muestra. Un blog dice llegar al 65 % «siendo generoso» [17], y LuxAlgo lo llama «abreviatura de marketing» [18]. Además, llegar al otro extremo no es lo mismo que tocar 2R antes que 1R. *Fiabilidad:* muy baja.

**d)** Nunca se ha probado. El perfil construido con velas de 5 m es aproximado.

### 8) Power of Three / Judas (barrido del rango asiático en Londres)
**a)** El día pasa por tres fases: acumulación en Asia, un falso movimiento en Londres (el Judas) y la distribución en NY.

**b)** Velas de 15 m:
- Om es la apertura de las 00:00 NY. AH y AL son el máximo y el mínimo de 20 a 00 NY.
- Largo: entre las 02 y las 05 NY el precio perfora AL. La señal es el primer cierre por encima de Om antes de las 07 NY.
- Stop en el mínimo de Londres − 0,1·ATR.
- Solo se opera si AH o PDH quedan más allá del objetivo. Corto simétrico.

**c)** No hay evidencia con muestra. Un motor público con 10 activos y 2 años hizo 5.259 operaciones con un 28,9 % de acierto a 1:2, sin ventaja [19]. *Fiabilidad:* nula.

**d)** I01 seguía la ruptura asiática, con horas UTC fijas. El Judas va contra ella.

**Wyckoff, descartado.** Lo mecanizable del spring y el upthrust ya es P03/I11 más volumen. No hay backtests [20], y lo de «85-90 % de acumulaciones con spring» no tiene muestra.

## 4. Tabla resumen

| # | Setup | Evidencia | Mecanizable | Qué faltaba | Probabilidad de partida |
|---|---|---|---|---|---|
| 1 | ORB NY + VolRel | Positiva en acciones | Alta | Rango real, hora de NY, VolRel | Baja-media |
| 2 | VWAP NY | Un paper en ETF | Alta | Lógica de tendencia, ancla en NY | Baja |
| 3 | Ruptura y retesteo | Descriptiva | Alta | Límite en el retesteo | Baja |
| 4 | Retroceso a la EMA | Ninguna | Alta | Casi nada | Muy baja |
| 5 | Silver Bullet | Negativa | Media-alta | Ventana, sesgo, FVG en ventana | Muy baja |
| 6 | ICT completo | Negativa | Media | Secuencia, killzone, límite, objetivo | Muy baja |
| 7 | Perfil de volumen | Solo afirmaciones | Media | Todo | Muy baja |
| 8 | Power of Three / Judas | Ninguna | Media | Ir contra la ruptura | Muy baja |

## 5. Mi top-3
1. **ORB NY con VolRel, versiones A y B.** Es lo único con evidencia positiva publicada y reglas sin ambigüedad.
2. **VWAP NY con límite.** Es nuevo para el proyecto, que solo probó lo contrario, y encaja con la entrada maker.
3. **Ruptura y retesteo de PDH/PDL con límite.** Corrige la entrada a mercado de las rupturas que ya fallaron.

**Sobre ICT.** Si se prueba, que sea con una sola especificación (la n.º 6, versión B) y con su regla invertida como diagnóstico. Necesita más del 40 % de acierto a 2R, cuando el azar da un 27 %.

## Fuentes
[1] github.com/mathematation860-boop/edge-or-myth-video2
[2] github.com/cjosh4toyotas-stack/silver-bullet-backtest
[3] papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998. No pude abrir el PDF (error 403); las cifras salen del resumen y de thortradecopier.com/blog/does-ict-smart-money-concepts-work
[4] statoasis.com/overfit/research/ict-backtest-what-survives
[5] ssrn.com/abstract=4729284
[6] papers.ssrn.com/abstract=4416622
[7] concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/
[8] research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/
[9] ideas.repec.org/a/eee/ecofin/v62y2022ics1062940822000833.html
[10] investmentnews.com/alternatives/bitcoin-volatility-is-more-pronounced-in-us-trading-hours/251428
[11] thepatternsite.com/ThrowPull.html
[12] newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf
[13] ar.tradingview.com/scripts/pullbackentry
[14] luxalgo.com/library/concept/silver-bullet/
[15] newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
[16] github.com/meegol/apex-killzone-engine
[17] quanttradingtips.wordpress.com/2020/02/24/80-rule-value-area/
[18] luxalgo.com/library/concept/80-percent-rule/
[19] github.com/ShiTmoZ/forex
[20] quantifiedstrategies.com/wyckoff-trading-strategy/
[21] papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101
[22] financemagnates.com/forex/analysis/exclusive-only-7-of-300000-prop-trading-accounts-achieved-payouts
