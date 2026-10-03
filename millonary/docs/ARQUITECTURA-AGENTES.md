# Millonary · Trading Floor: agentes y departamentos

La idea original (Conesa) es un fondo gestionado por equipos de IA especializados, con comité, escuela y laboratorio.
Millonary lo implementa con esta regla de oro: **los departamentos analizan, recomiendan y aprenden; la operativa la fija el
núcleo validado y solo la capa de riesgo determinista puede vetar.** Todo lo no validado corre en MODO SOMBRA.

```
 DATOS (Binance/Vision, macro, FOMC, funding)
        │
        ▼
 ┌──────────── COMITÉ (Dirección) ───────────────────────────────────────────┐
 │ Riesgos(veto) · Macro · Análisis · Cartera · Mesa · Derivados · Lab · Escuela · Infra │
 └───────────────────────────────┬───────────────────────────────────────────┘
                                 ▼
        Núcleo validado ──► capa de riesgo ──► Mesa (papel → dinero real tras protocolo)
                                 ▲
        Laboratorio (sombra) ────┘   promoción solo con: ≥90 días, Sharpe ≥ núcleo+0,3, caída ≤ 1,2×, embudo superado
```

Cómo se ejecuta: `python -m src.live.daily` (actualiza la cuenta de papel, convoca al comité y escribe `paper_state/briefing.md`
e `informe_prueba.md`). Estado de cada departamento: ver la tabla "Organigrama" de cada informe.

## Ciclo de mejora por prueba y error (Laboratorio + Escuela)
1. Idea (minero, Escuela, revisión) → se declara la regla ANTES de probarla.
2. Prueba única sobre historia previa al ciego, contra el núcleo, con IC bootstrap → se anota en `reports/registro_pruebas.md`.
3. Si pasa: sombra hacia delante ≥ 90 días. Si no: se descarta (p. ej. el recorte de exposición en el FOMC).
4. Promoción solo con la regla del protocolo; cualquier cambio del núcleo = versión nueva y reloj de 30 días nuevo.

## Honestidad sobre los agentes de IA
- El minero genético NO demostró que su ranking sirva (ρ = 0,06 entre entrenamiento y validación).
- Los patrones de velas y el price action se informan pero no tienen ventaja demostrada.
- Un LLM solo puede REDACTAR el informe (opcional, `ANTHROPIC_API_KEY`); no decide ni cambia límites.
