# Millonary · Operar desde España: regulación, plataformas e impuestos

**Estado:** investigación del 2026-09-29 con fuentes SECUNDARIAS (blogs, notas de prensa de plataformas). Las fuentes se
contradicen en algún punto. **Nada de esto es asesoramiento legal ni fiscal: hay que verificarlo en los términos oficiales
de la plataforma (en español), en la CNMV y con un gestor/asesor fiscal antes de operar con dinero real.**

## 1. Lo que dicen las fuentes
| Tema | Qué se encontró | Fiabilidad |
|---|---|---|
| Binance | Según varias fuentes, desde el 1-jul-2026 no puede ofrecer trading, depósitos nuevos ni Earn a residentes de la UE (retiró su solicitud de licencia MiCA el 24-jun). | Media: coincide en varias webs, no verificado en fuente oficial |
| Perpetuos y CNMV | La CNMV ha comunicado que los futuros perpetuos / "spot-quoted futures" vendidos a minoristas españoles deben tratarse como **CFD**, con las restricciones de apalancamiento de los CFD. ESMA sostiene que los perpetuos caen bajo las reglas de CFD. | Media (varias fuentes de prensa financiera) |
| Quién puede ofrecer perpetuos a minoristas UE | Solo plataformas con licencia MiCA (CASP) **y** MiFID II. Se citan Kraken, OKX (X-Perps, contratos con vencimiento a 5 años, hasta 10×), One Trading, Perpetuals.com. | Media |
| Bybit EU | Contradicción: una fuente dice que ofrece perpetuos en España; otra, que sus perpetuos de alto apalancamiento NO se ofrecen a minoristas del EEE (licencia MiCA austriaca de mayo de 2025, sin MiFID II). | **Baja: comprobar en su web** |
| Apalancamiento | Para CFD sobre cripto a minoristas, ESMA fijó históricamente 2:1 (dato de ESMA de 2018, no verificado hoy en estas búsquedas). Un tope general "de ~10×" aparece en algunas fuentes. | Baja: verificar |
| IRPF | Las ganancias/pérdidas por cripto tributan como ganancias/pérdidas patrimoniales en la base del ahorro: 19 % hasta 6.000 €, 21 % hasta 50.000 €, 23 % hasta 200.000 €, 28 % por encima. Cada venta o permuta es un hecho imponible desde el primer euro. | Media-alta (varias fuentes coinciden) |
| Modelo 721 | Declaración informativa de criptos en custodia en el extranjero si superan 50.000 € a 31-dic (plazo 31 de marzo). | Media-alta |
| Derivados / perpetuos / funding en IRPF | **No se encontró información fiable.** | Sin datos |

Fuentes consultadas (secundarias): blog.nebeus.com, qualebroker.com, lacryptoguia.com, guiafiscal.es, financemagnates.com,
thetradenews.com, financefeeds.com, zitadelleag.com, businesswire.com (OKX), blockeden.xyz, taxdown.es, blockpit.io, contasimple.com.

## 2. Consecuencias para Millonary
1. **Binance queda descartado para dinero real** (y usarlo con VPN incumpliría sus términos y no lo recomiendo). Los datos
   públicos históricos de Binance Vision siguen sirviendo para investigar y para el paper trading (es información, no un servicio).
2. **El apalancamiento de 5× no estará disponible para un minorista en España** con casi total seguridad. No es un problema: el
   sistema está diseñado con tope efectivo 2× y exposición media 0,25×; en 2017-2025 la exposición máxima fue 0,84×.
3. **El núcleo es implementable en SPOT** (sin derivados, sin apalancamiento, sin funding, sin liquidación), porque es solo largos y
   nunca necesitó más de 1×. Es la vía más simple y la que evita la clasificación CFD. Requiere validar que el resultado aguanta las
   comisiones de una plataforma spot (mayores que las del perpetuo): ver el informe de sensibilidad de costes.
4. **Impuestos:** cada rebalanceo con venta parcial es un hecho imponible. Con ≈ 7,5 órdenes al mes habrá muchas transmisiones;
   el rendimiento NETO tras impuestos será menor que el del backtest. Hace falta llevar el registro por lotes (ya lo hacemos: FIFO)
   y un gestor. El diario de lotes de Millonary exporta CSV utilizables.
5. **Zona horaria:** España es UTC+1/+2; los cierres de vela de 4h caen a las 02:00, 06:00, 10:00, 14:00, 18:00 y 22:00 (hora de
   verano) o a las 01:00, 05:00, ... (invierno).

## 3. Qué tienes que hacer tú (comprobaciones que yo no puedo hacer)
- [ ] Elegir plataforma autorizada en España para **spot** de BTC/EUR (o USDT) y comprobar en su web oficial la comisión de taker/maker.
- [ ] Si más adelante quisieras derivados: confirmar en la web oficial y en la CNMV que la plataforma está autorizada (MiCA + MiFID II)
  y qué apalancamiento máximo aplica a minoristas.
- [ ] Consultar con un gestor/asesor fiscal cómo tributan tus operaciones (spot y, si procede, derivados) y el registro de lotes.
