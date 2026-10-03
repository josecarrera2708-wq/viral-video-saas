# Evidencia 4 · Capturas de la interfaz "Money Beast Capital – Trading Floor" (aportadas por el dueño, 2026-09-29)

Fuente: 5 fotografías de pantalla. **Marketing/afirmaciones del autor: no son resultados verificados.**

## Qué muestran
- **Oficina** con departamentos; barra superior: "PAPEL realista · sin claves demo", régimen RISK-ON, Fear & Greed.
- **Pestañas:** Sala / Ranking / Equipos / Informe. Botones: Comité, Megáfono, Prueba, Descanso, Pausar todo, Reabrir, Kill switch, Ajustes.
- **Informe:** curva de equity, caída desde máximo, paneles de riesgo, informe semanal, exportación Operaciones CSV y Diario Excel.
- **Equipos · Quant/ML:** meta-etiquetado con regresión logística; "Es la mejora con más riesgo de sobreajuste: el examen final sellado decide." (51 meta-etiquetadas, 9 sistemas probados, 2 superan validación).
- **Infraestructura:** uptime 24/7 97,04 % en 7 días; WebSocket de liquidaciones de Bybit e Hyperliquid conectados; heartbeat (healthchecks.io).
- **Mesa de trading:** 20 traders, 10 con capital del fondo.
- **Ranking de setups:** por α anualizado (hasta ~97 %, t 1,45–2,22), β vs BTC, β de tendencia, R² bajo. Setups: Parabolic SAR + EMA200, Ichimoku, Bollinger + RSI (reversión), Keltner.

## Lectura crítica
- Los t-stats de 1,45–2,22 con muchos setups probados NO sobreviven a corrección por comparaciones múltiples; el "examen sellado" es
  lo valioso y coincide con nuestro protocolo (ciego consumido una vez, DSR, PBO).
- Replicable: regresión alfa/beta/tendencia por trader-setup, meta-etiquetado con examen sellado, métricas de uptime/heartbeat, informe semanal/CSV/Excel.
