# Carry de funding en papel junto al núcleo · Prerregistro v1 (2026-10-02, antes de la primera vela)

Petición del dueño: «pon el carry de funding a operar junto al núcleo en papel». Base: F06 de la mesa de fondos, única estrategia
certificada (5/5) en `reports/fondos_resultados.md`. No es una prueba estadística nueva (misma regla): es su puesta en marcha operativa.

- **Cuenta:** subcuenta propia de 1.000 USDT (`paper_state/carry/`, código `src/live/carry.py`). La cuenta oficial del núcleo y su
  protocolo (G1–G5) NO se tocan: cambiarlos invalidaría su prueba. El panel suma ambas como «cartera principal» (2 × 1.000 USDT).
- **Regla (idéntica a F06):** al cierre diario (00:00 UTC) dentro si la media de las 21 tasas de funding de los últimos 7 días es > 0,
  fuera si no; dentro = largo contado + corto perpetuo con la misma cantidad de BTC (nocional 1×, lote 0,001 hacia abajo); reajuste a 1×
  si el nocional sale de la banda del 20 %. Costes: contado 10 pb + 2 pb, perpetuo 5 pb + 2 pb por lado. Equity marcada cada 4 h,
  perpetuo liquidado al cierre de cada vela, funding en cada marca de 8 h.
- **Datos:** Binance Vision (contado y perpetuo 4 h, ≤ 1 día de retraso). Funding del mes aún no publicado: fórmula de Binance sobre el
  índice de prima de 1 min (comprobada en jul-sep 2026: error medio 1,2e-6, máx. 8e-6); se corrige a la tasa real al publicarse el mes.
  Esta estimación sustituye también al 0,01 % fijo en la cuenta del núcleo y en la mesa de fondos (solo cambia lo provisional).
- **Inicio:** primera decisión con el cierre del 2026-10-02 (vela que cierra el 2026-10-03 00:00 UTC). Rutina diaria y horaria (idempotente).
- **Seguimiento:** frente a F06 de la mesa de fondos (misma regla, contabilidad diaria sin lotes): deben moverse juntas.
- **Dinero real: nada.** Requisitos antes de proponerlo: ≥ 90 días en papel sin desviarse de su envolvente histórica (caída ≤ 3 %),
  revisión del riesgo de contraparte (exchange, desapalancamiento automático, margen del corto con el contado como garantía) y
  aprobación EXPRESA del dueño.
