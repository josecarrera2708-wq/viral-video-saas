# Mesa de 1 h (acción de precio + fórmulas cuantitativas) · Prerregistro v1 — antes de ejecutar nada

Fecha 2026-10-02. Petición del dueño: los mismos traders de la mesa de 15 min deben operar también en velas de 1 h. Sistema aparte (`paper_state/mesa1h/`); la mesa intradía I01–I14 no se toca.
- **Traders:** los 13 de `config/mesa15_prerregistrada.md` con TODAS las ventanas ÷4 (24 h = 24 velas; EMA tendencia 96; DONCHIAN 12; etc.) y los mismos umbrales en ATR/z/ratios. Código fijo: `src/desk1h/setups.py`.
- **Datos:** velas de 1 h construidas desde las de 15 min de Deribit (exigen las 4 velas; funding = suma de los 4 trozos), 2022-06 → hoy. Mismo motor, mismos costes, 1.000 USDT por trader, riesgo 0,5 %.
- **Aprendices A/C:** igual que en 15 min (n_min 6 / 15, veto relativo t ≤ −1), con contexto: EMA 800 h y percentil ATR sobre 500 velas.
- **Periodos y puertas Q1–Q7:** idénticos a la mesa de 15 min (construcción 2022-06→2024-07, validación →2025-10, examen 2025-10→2026-09-29, una sola mirada de esta mesa).
- **Aviso:** los precios del examen ya se vieron con la mesa de 15 min; estos 13 traders en 1 h son versiones nuevas sin ajuste sobre ese examen, pero no es independencia total. Certificar exige además hacia delante.
- **Hacia delante:** papel, inicio 2026-10-02 00:00 UTC, rutina horaria. Dinero real: nada, solo con certificación, ≥150 operaciones hacia delante, p ≥ 0,90 y aprobación EXPRESA del dueño.
