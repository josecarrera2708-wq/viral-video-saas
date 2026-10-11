# Protector · La «entrada de protección»: qué es, qué hace y cómo probarla

## Resumen

1. **Conesa no explica en público cómo hace las coberturas.** En el vídeo del fondo solo nombra el departamento. La única pantalla de ese departamento muestra una *cobertura de beta* de la cartera, a 0 BTC. En su curso gratuito exige stop loss y advierte contra «querer recuperar» pérdidas.
2. **Todas las variantes son reglas que cambian la posición neta según el camino del precio:** promediar, cubrir, girar y martingala. Con un paseo aleatorio, la esperanza bruta es 0: en el Monte Carlo sale entre −0,003 y −0,001 R por operación, con un margen de ±0,004. La esperanza neta es −costes. Lo único que cambia es la forma: el acierto pasa del 34 % al 72 %, y las pérdidas plenas se vuelven más raras, pero cada una equivale a 3,5 ganancias medias.
3. **Hay equivalencias exactas**, verificadas camino a camino (diferencia < 10⁻¹⁵):
   - Cobertura opuesta 1:1 = cerrar en el stop pagando una ida y vuelta extra.
   - Cobertura 2:1 = stop-and-reverse con un 50 % más de costes.
   - Martingala 2× en la misma dirección = promediar 1× con más costes.
4. **A igual riesgo máximo, lo que «mejora» a la versión sin protección es el stop final más ancho:** reduce el nocional y, con él, el coste por unidad de R.
   - Una sola entrada con stop en −2R gana a la regla del dueño en 5 de los 6 mundos simulados.
   - La segunda entrada solo suma, y como mucho +0,04 R sobre su control, cuando el precio revierte después del barrido.
   - Con tendencia, que es el perfil de nuestras mejores estrategias, destruye la ventaja: el capital mediano tras 250 operaciones baja de ×2,04 a ×1,06.
5. Propongo 4 variantes exactas, 2 controles y un diagnóstico previo que decide si merece la pena gastar pruebas.

## 1. Conesa: qué hay verificable

- **Vídeo del fondo:** [«He Creado un Fondo de Inversión Gestionado 100% por IA»](https://www.youtube.com/watch?v=kkute1vusfk), canal CONESA X, 28-09-2026.
  - Min 6:11, cita literal: «también tenemos un departamento de coberturas por si hay que hacer alguna cobertura de alguna operación que no salga bien y haya que protegerla».
  - No hay ninguna mecánica, ni en el vídeo ni en la descripción.
  - La descripción aclara que la sala «opera en simulación (paper trading)» e incluye un enlace de afiliado a Margex. → **Marketing.**
- **Panel «Coberturas»**, en la captura que aportó el dueño (`docs/conesa-evidencia-5-imagenes.md`): «Cobertura de beta 0,0000 BTC, posición +0 $», junto a «Protección de cola: desactivada» en la mesa de opciones. Es una cobertura de la exposición de la cartera, no una segunda entrada por operación.
- **[Curso gratis, vol. 1](https://www.youtube.com/watch?v=0FQOKjo6_hA)** (02-08-2022, min 14:40 y 20:50): «promediar» significa entrar 3 o 4 veces en los retrocesos de una tendencia o hacer compras periódicas. No da niveles, tamaños ni stops.
- **[Curso, vol. 3](https://www.youtube.com/watch?v=BM4gro9KFmo)** (25-08-2022):
  - Min 14:40: «al mercado se tiene que entrar… con un riesgo controlado, con un precio objetivo, con un stop loss».
  - Min 21:10: advierte contra «querer recuperar rápido y de forma descontrolada una racha de pérdidas».
- **Alcance:** los 583 títulos del canal (ninguno trata de coberturas) y 10 transcripciones. No pude transcribir el short «¿Usas stop lose?» (20-08-2026) por el error 429 de YouTube. Instagram y TikTok exigen sesión, y la [cuenta PAMM de InstaForex](https://www.instaforex.com/sp/forex_monitoring/50649849) a su nombre no muestra operaciones sin JavaScript.

**Conclusión:** no hay nada verificable que atribuya a Conesa la regla «si va en contra, mete otra entrada una vez». Su propio curso dice lo contrario.

## 2. Variantes y equivalencias matemáticas

Notación: operación larga, entrada E, stop original en E−1R, primera entrada de tamaño q y objetivo en E+kR. N es la posición neta.

| Variante | Al tocar E−1R | N después | Equivale a | Coste extra |
|---|---|---|---|---|
| a) Promediar 1× | Compra otro q. Stop común en E−2R. Objetivo: *break-even* global, media+1R o el original | +2q | Una posición con stop en E−2R cuyo tamaño se duplica en E−1R | 1 entrada |
| b) Cobertura 1:1 (modo hedge) | Abre un corto de q y mantiene el largo | 0 | **Cerrar en E−1R**. La pérdida queda congelada y el *funding* se compensa. «Desbloquear» después es abrir una operación nueva | 1 ida y vuelta + margen bloqueado |
| b) Cobertura h:1 (h>1) | Abre un corto de h·q | −(h−1)q | **Stop-and-reverse de (h−1)q** | 1 ida y vuelta (con h=2, costes ×1,5) |
| c) Stop-and-reverse | Cierra y abre un corto de q (stop en E, objetivo kR) | −q | — | 1 entrada |
| d) Martingala 2× | Cierra y reabre 2q | +2q / −2q | **a)** si es en la misma dirección; **b) con h=3** si es contraria | 1 ida y vuelta |

**Principio general**

Beneficio = Σ N₍t−1₎·ΔP_t − costes.

Si el precio es un paseo aleatorio (una martingala) y N solo depende del pasado, entonces E[Σ N·ΔP] = 0. Es el [teorema de parada opcional](https://en.wikipedia.org/wiki/Optional_stopping_theorem): ningún sistema de apuestas convierte un juego justo en ganador. Por tanto, E[beneficio] = −E[costes].

Las variantes solo se diferencian en la forma de los resultados:
- **Cóncavas:** a) y d) en la misma dirección. Funcionan como «vender gamma»: muchas ganancias pequeñas y pocas pérdidas grandes. Ganan si hay reversión.
- **Convexas:** b) con h>1, c) y d) contraria. Ganan si hay momentum.

**Ejemplo: A2-BE (promediar y salir en *break-even*), k = 2, sin costes**
- 1/3 de las operaciones llega directo a +2R.
- Las otras 2/3 tocan −1R y promedian. De ellas:
  - 2/3 vuelven al *break-even* (−0,5R) antes de −2R y salen a 0;
  - 1/3 pierden 3R.
- Esperanza: 1/3·2 − 2/9·3 = **0**.
- El acierto más los empates sube del 33 % al 78 %, pero ahora la pérdida plena es de 3R.

**Igualar el riesgo máximo:** la pérdida peor por unidad, con costes, es 1,14 en V0 y 3,28 en A2, así que la primera entrada de A2 tiene un tercio del tamaño. En la práctica, «proteger» es operar más pequeño.

## 3. Monte Carlo sintético (`protector_sim.py`)

**Diseño**
- 400.000 operaciones por mundo.
- Cada camino de precio se evalúa con todas las variantes, así que las comparaciones son pareadas.
- Stop original de 1R, equivalente a 10 σ de un paso de la simulación.
- Objetivo de 2R. Con 3R las conclusiones son las mismas.
- Coste del 0,14 % por entrada con un stop del 1 % (c/D = 0,14).
- Cada variante se dimensiona para que, si saltan todos sus stops, la pérdida con costes sea exactamente 1 R_max = 2 % del capital.
- Secuencias de 250 operaciones; ruina = capital ≤ 50 %.

**Mundos simulados**

| Mundo | Precio | Entrada | VR(200) |
|---|---|---|---|
| RW | Paseo aleatorio | Sin ventaja | 1,00 |
| TEND | Deriva persistente (momentum) | Sin ventaja | 1,39 |
| REV | Paseo aleatorio + componente transitoria que revierte | Sin ventaja | 0,72 |
| REV+ | Como REV | Contraria a la desviación (con ventaja) | 0,72 |
| TEND+ | Como TEND | A favor de la deriva (con ventaja), como los patrones de «dejar correr» | 1,39 |
| BARR+ | Deriva a favor + ruido rápido que barre el stop y vuelve | Con ventaja | 0,59 |

VR(200) es el ratio de varianzas a 200 pasos: 1 en un paseo aleatorio, más de 1 con tendencia, menos de 1 con reversión.

**Tabla 1. Paseo aleatorio.** Valores en R por unidad de riesgo máximo; error estándar ≤ 0,002. La caída es la máxima dentro de cada secuencia de 250 operaciones.

| Variante | R neto | Bruto | Coste | R/sd | Acierto | Gan./pérd. media | Pérd. plena | Peor racha med (p95) | Caída med (p95) | P(ruina) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V0: sin protección | −0,126 | −0,003 | 0,123 | −0,097 | 34 % | +1,68/−1,05 | 66 % | 11 (17) | 59 (77) % | 61 % |
| VW2: control, 1 entrada, stop −2R | −0,067 | −0,002 | 0,065 | −0,070 | 50 % | +0,89/−1,02 | 50 % | 7 (11) | 43 (63) % | 20 % |
| A1: 2.º tramo en −0,5R, stop −1R | −0,144 | −0,003 | 0,141 | −0,110 | 34 % | +1,59/−1,03 | 66 % | 11 (17) | 62 (79) % | 69 % |
| A3: 2.º tramo en −0,5R, stop −1,5R | −0,092 | −0,002 | 0,090 | −0,083 | 43 % | +1,14/−1,02 | 57 % | 8 (13) | 50 (70) % | 38 % |
| A2-BE: promedia en −1R, stop −2R, sale en BE | −0,073 | −0,002 | 0,071 | −0,115 | 72 % | +0,29/−1,02 | 28 % | 4 (6) | 37 (53) % | 8 % |
| A2-T: igual, con el objetivo original | −0,072 | −0,001 | 0,071 | −0,073 | 50 % | +0,87/−1,02 | 50 % | 7 (11) | 44 (64) % | 24 % |
| B1: cobertura 1:1 | −0,184 | −0,003 | 0,182 | −0,153 | 34 % | +1,50/−1,05 | 66 % | 11 (17) | 67 (81) % | 84 % |
| B2: cobertura 2:1 | −0,136 | −0,002 | 0,134 | −0,164 | 57 % | +0,55/−1,07 | 42 % | 6 (9) | 55 (69) % | 60 % |
| C: stop-and-reverse | −0,104 | −0,002 | 0,102 | −0,121 | 58 % | +0,61/−1,08 | 42 % | 6 (9) | 48 (65) % | 38 % |
| D1: martingala 2× | −0,097 | −0,002 | 0,095 | −0,116 | 55 % | +0,65/−1,02 | 45 % | 6 (9) | 46 (64) % | 30 % |

**Tabla 2. R neto por mundo** (error estándar ≈ 0,002). Cada variante debe compararse con el control que tiene su mismo stop final: VW1.5 para A3 y VW2 para A2.

| Variante | RW | TEND | REV | REV+ | TEND+ | BARR+ |
|---|---:|---:|---:|---:|---:|---:|
| V0 | −0,126 | −0,067 | −0,182 | +0,028 | **+0,160** | −0,023 |
| VW1.5 (control) | −0,088 | −0,063 | −0,108 | +0,066 | +0,126 | +0,063 |
| VW2 (control) | −0,067 | −0,064 | −0,062 | +0,079 | +0,095 | +0,109 |
| A1 | −0,144 | −0,103 | −0,182 | +0,006 | +0,094 | −0,015 |
| A3 | −0,092 | −0,086 | −0,094 | +0,058 | +0,078 | +0,083 |
| A2-BE | −0,073 | −0,098 | −0,030 | +0,062 | +0,016 | +0,060 |
| A2-1R | −0,072 | −0,102 | −0,023 | **+0,087** | +0,028 | +0,097 |
| A2-T | −0,072 | −0,088 | −0,046 | +0,068 | +0,045 | **+0,124** |
| C | −0,104 | +0,003 | −0,222 | −0,128 | +0,075 | −0,172 |
| D2 (giro 2×) | −0,097 | **+0,026** | −0,236 | −0,180 | +0,047 | −0,221 |

**Qué muestran las tablas**

1. **Con un paseo aleatorio, el resultado bruto es 0 en todas las variantes.** El neto solo las ordena por su coste por unidad de riesgo. Las que tienen el stop final más ancho «pierden menos» porque mueven menos nocional por cada R. El control VW2, sin segunda entrada, consigue lo mismo y además con mejor R/sd.
2. **La menor caída y la menor ruina de A2-BE (8 % frente a 61 %) se deben al tamaño, no a la protección.** A igual riesgo máximo, A2-BE apuesta menos (sd 0,63 frente a 1,29). Por unidad de volatilidad es peor que V0 (R/sd −0,115 frente a −0,097). Escalada a la misma volatilidad, perdería unos 0,15 R por operación.
3. **Lo que decide si ayuda es la autocorrelación del precio:**
   - Con tendencia, promediar empeora (A2 entre −0,09 y −0,10, frente a −0,07 de V0) y girar mejora (C +0,003; D2 +0,026).
   - Con reversión ocurre al revés (A2-1R −0,023; C −0,222).
   - Las coberturas 1:1 y 2:1 son siempre peores que su equivalente: los mismos caminos con más costes.
4. **Con ventaja de tendencia (TEND+), V0 es la mejor variante y la protección se come la ventaja:** +0,160 R frente a +0,016 R de A2-BE. Con un 2 % de riesgo, el capital mediano tras 250 operaciones es ×2,04 frente a ×1,06.
5. **Con barridos (BARR+) o reversión con ventaja (REV+), casi toda la mejora la aporta el stop ancho:** V0 −0,023 → VW2 +0,109. La segunda entrada añade poco sobre su control (A2-T +0,015, A3 +0,020) o incluso resta (A2-BE −0,049). A2-BE pierde contra VW2 en 5 de los 6 mundos.
6. **Con un stop del 0,5 % (c/D = 0,28)** todo empeora entre 0,06 y 0,12 R, y solo quedan positivas por poco (≤ +0,05 R) algunas variantes con ventaja: la protección no resuelve el coste intradía. Con un 1 % de riesgo, la ruina en paseo aleatorio baja al 0-16 % (V0: 5 %) y el orden no cambia.

## 4. Cuándo puede ayudar de verdad

**Condición matemática para el escalón dentro del stop (A1/P1)**

El segundo tramo en −0,5R gana a V0 solo si la fracción φ de operaciones ganadoras que tocaron −0,5R antes de ganar supera su valor bajo paseo aleatorio: 0,40 con k=2 y 0,43 con k=3, en tiempo continuo.
- Una ventaja direccional **baja** φ, porque las buenas operaciones van directas al objetivo.
- Solo la reversión después del barrido **sube** φ.
- En los mundos simulados con ventaja, A1 nunca superó a V0.

**Escalonar solo es «entrar mejor» si** la entrada ya tiene ventaja, la vuelta tras el barrido está medida (φ claramente por encima de su referencia), el segundo tramo es barato (límite *maker* al 0,02 %) y gana al control de una sola entrada con el mismo stop final.

**Evidencia publicada con números**
- **Stops y autocorrelación.**
  - [Kaminski y Lo (2014, *J. Financial Markets*)](https://dspace.mit.edu/handle/1721.1/114876): con paseo aleatorio, un stop siempre reduce el rendimiento esperado. Con momentum puede añadir valor: en la bolsa de EE. UU. (1950-2004), entre 50 y 100 pb al mes durante los periodos fuera del mercado.
  - [Lo y Remorov (2017, *J. Financial Markets* 34)](https://dspace.mit.edu/handle/1721.1/107017): en acciones de EE. UU. (1964-2014), los stops ajustados rinden menos por los costes, salvo cuando la autocorrelación es alta.
- **Qué ocurre en la zona de stops.** [Osler (2003)](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf) y [Osler (2005)](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf), con unas 9.700 órdenes reales de divisas: los stops se agrupan justo después de los números redondos y, al cruzarlos, el precio se acelera en cascada. Promediar en el nivel del stop es comprar dentro de esa aceleración.
- **Órdenes límite.** [Linnainmaa (2010, *J. Finance*)](https://ideas.repec.org/a/bla/jfinan/v65y2010i4p1473-1506.html): las órdenes límite sufren selección adversa y se ejecutan más cuando el precio va en contra. El segundo tramo se llenará sobre todo en las operaciones perdedoras.
- **Intentar recuperar se paga.**
  - [Coval y Shumway (2005, *J. Finance*)](https://ideas.repec.org/a/bla/jfinan/v60y2005i1p1-34.html): los operadores del CBOT con pérdidas por la mañana asumen más riesgo por la tarde (31,2 % frente a 27 %), y los precios que marcan se revierten antes.
  - [Thaler y Johnson (1990)](https://ideas.repec.org/a/inm/ormnsc/v36y1990i6p643-660.html) describen el «efecto empatar»: tras una pérdida, las apuestas que permiten volver a cero resultan especialmente atractivas. La regla del dueño es ese sesgo convertido en regla.
- **Mantener las perdedoras cuesta.**
  - [Odean (1998)](https://rpc.cfainstitute.org/research/cfa-digest/1999/05/are-investors-reluctant-to-realize-their-losses-digest-summary): al año siguiente, las ganadoras vendidas rindieron unos 3,4 puntos más que las perdedoras que se mantuvieron.
  - [Locke y Mann (2005, *J. Financial Economics*)](https://ideas.repec.org/a/eee/jfinec/v76y2005i2p401-444.html): la disciplina relativa predice el éxito posterior de los profesionales del parqué.
- **Entrar por tramos.** [Vanguard (2012)](https://militarymoneymanual.com/wp-content/uploads/2021/08/Dollar-Cost-Averaging-Just-Means-Taking-Risk-Later-Vanguard.pdf) (copia del informe): invertir todo de golpe ganó a hacerlo por tramos en unos 2/3 de los casos, en EE. UU., Reino Unido y Australia. Con ventaja, retrasar parte de la entrada cuesta.
- **BTC intradía.** [Wen, Bouri, Xu y Zhao (2022)](https://ideas.repec.org/a/eee/ecofin/v62y2022ics1062940822000833.html), BTC 2013-2020: hay momentum *y* reversión intradía, y cuál domina depende de los saltos, la liquidez y la FOMC. Qué pasa en BTC después de tocar el stop es una pregunta empírica.
- **Regulación.** La [norma NFA 2-43(b)](https://www.nfa.futures.org/rulebook/rules.aspx?Section=4&RuleID=RULE%202-43&RuleIDDetail=RULE%202-43) (2009) prohíbe en EE. UU. mantener posiciones opuestas en cuentas minoristas de divisas: obliga a cerrar en orden FIFO. Según [Finance Magnates](https://financemagnates.com/forex/brokers/nfas-new-regulation-demands-a-blow-against-traders-brokers-or-both-part-1-hedging/), el motivo es la falta de beneficio económico y el coste añadido. En Binance existe el [modo hedge](https://www.binance.com/en/support/faq/what-is-hedge-mode-and-how-to-use-it-360041513552), pero no cambia la posición neta.

**Opinión o práctica de profesionales (sin números verificables)**
- Paul Tudor Jones: «[losers average losers](https://www.turtletrader.com/losers-average-losers/)», es decir, los perdedores promedian pérdidas.
- Las Tortugas solo añadían a favor, cada ½N, con stop a 2N de la última unidad ([reglas](https://www.mql5.com/en/articles/23448)).
- Bulkowski: los [patrones fallidos](https://thepatternsite.com/BustedPatterns.html) que rompen por el lado contrario rinden igual o más. Son datos de acciones, en mercados alcistas y sin costes, pero es la base práctica de P4.
- Anécdota: Leeson doblaba para recuperar y hundió Barings con 827 M£ de pérdidas ([fuente](https://en.wikipedia.org/wiki/Nick_Leeson)).

## 5. Variantes exactas para probar y cómo compararlas

**A qué se aplican**
- A cada estrategia de la mesa: patrones en 1 h y 4 h, stop por ATR o por estructura, salida con TP de 3R o «dejar correr» con la EMA50, y su propia salida por tiempo.
- R es la distancia del stop original.
- f es el riesgo máximo por operación, el mismo que en el control.
- E∓ indica la dirección: E−0,5R en un largo y E+0,5R en un corto.

**Qué hay que añadir al motor:** ahora solo admite una posición. Hacen falta un segundo tramo, el stop común, el objetivo recalculado y la secuencia dentro de cada vela usando las velas de 5 min.

| | 2.ª entrada | Tamaños | Stop final | Objetivo tras la 2.ª | Validez | Control |
|---|---|---|---|---|---|---|
| **P1 · Escalón dentro del stop** | Límite *post-only* en E∓0,5R | 50/50 | E∓1R (sin cambios) | El original de la estrategia | 6 velas en 1 h / 2 en 4 h | C0 = original |
| **P2 · Escalón con stop 1,5R** | Límite *post-only* en E∓0,5R | 50/50 | E∓1,5R | El original | 6 / 2 velas | C1.5 = 1 entrada, stop 1,5R |
| **P3 · Regla del dueño** | Límite en E∓1R (sustituye al stop) | 1:1 | E∓2R | *Break-even* global con costes (orden límite); si no, stop o salida por tiempo | Hasta la salida de la estrategia | C2 = 1 entrada, stop 2R; y C0 |
| **P4 · Giro único** | En E∓1R cierra y abre la posición contraria a mercado | 1:1 | E (1R desde el giro) | kR desde el giro, o la salida por tiempo | Inmediata | C0 |

**Reglas comunes**
- **Uso único:** nunca hay una tercera entrada.
- **Tamaño:** q = f·capital / pérdida peor. La pérdida peor suma todas las patas, el stop final y los costes: *taker* 0,05 % + 2 pb por lado en las órdenes a mercado y *maker* 0,02 % en las límite. Así, la pérdida peor de cada variante es f, igual que en el control.
- **Rellenos:** una orden límite solo se ejecuta si el precio la atraviesa por 1 pb, como el `tp_pen` del motor. Si una vela de 5 min toca a la vez el límite y el stop, se asume el peor orden.

**Protocolo de comparación justa**
1. **Prerregistro.** Registrar P1-P4 y los controles C1.5 y C2 en git antes de ejecutar. Son 4 pruebas por estrategia, que hay que sumar al recuento de pruebas (más de 2.044) en el DSR y en la corrección de Holm.
2. **Mismas condiciones.** Las mismas señales, los mismos tramos (construcción, validación y examen), los mismos costes y el mismo f.
3. **Comparación pareada.** Para cada señal, ΔR = R de la variante − R del control, con un IC calculado por bootstrap de bloques.
4. **Criterio para aprobar.** La variante debe ganar a los **dos** controles: el original y el de una sola entrada con su mismo stop final. Además debe pasar las puertas de siempre: R>0 con al menos 20 operaciones, Holm p<0,10, R>0 con costes ×2, caída <30 % y DSR ≥0,80.
5. **Informe de la forma.** Acierto, % de pérdidas plenas, peor racha y caída máxima, con bootstrap de secuencias al riesgo f.
6. **Diagnóstico previo**, que hace el coordinador tras el prerregistro y solo con datos de construcción:
   - φ: la fracción de operaciones ganadoras cuya excursión adversa máxima llegó a −0,5R. Su referencia bajo paseo aleatorio debe calcularse con la misma granularidad de velas.
   - La probabilidad de volver al *break-even* antes de −2R, entre las que tocaron −1R. Referencia ≈ 0,61 con c/D = 0,14.
   - La probabilidad de llegar a −1R−kR antes de volver a E, entre las que tocaron −1R. Referencia 1/(1+k).
   - Si el IC no excluye el valor de referencia, no se prueba la familia correspondiente (P1-P3 o P4). Así se ahorran pruebas.
7. **No probar B1, B2, D1 ni D2.** Son exactamente V0, C y A2 con más costes.

**Expectativa honesta:** nuestras mejores estrategias son de tendencia (acierto del 21-36 % y «dejar correr»), y en ese perfil P3 destruye la ventaja. Lo único con alguna posibilidad es P4 (giro tras un patrón fallido), y solo si el diagnóstico muestra que el precio sigue de largo tras el stop. La alternativa más simple es un stop más ancho con una sola entrada (C1.5 o C2), que ya consigue casi todo lo que la «protección» parecía ofrecer.

---
**Archivos (scratchpad):**
- `agentes/protector_sim.py`: el script. Se ejecuta con `python3 protector_sim.py --trades 400000 --k 2 --cD 0.14 --f 0.02` y tarda unos 2 min.
- `agentes/protector_sim_resultados/`: los JSON y las tablas de 4 corridas: k=2 y k=3 con c/D=0,14 y f=2 %, c/D=0,28, y f=1 %.

Todo con datos sintéticos; no se ha usado ningún dato de BTC.
