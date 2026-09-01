# 📐 FASE 05 — Modelo de Análisis Determinístico RC506

## Arquitectura de Análisis Nivel 6
```
  [ KPI RESULTS ] (Fase 04)
        │
        ▼
  ┌───────────────────────────┐
  │  RC506 Rules Registry     │ ──> Reglas declarativas (Compliance, MoM, Trend, Threshold, Concentration)
  └─────────────┬─────────────┘
                │
                ▼
  ┌───────────────────────────┐
  │  Analysis Service         │ ──> Evaluación determinística sin eval() ni LLM
  └─────────────┬─────────────┘
                │
                ▼
  [ AnalysisInsight ] ─────────> Persistencia de observaciones (INFO, POSITIVE, WARNING, CRITICAL)
```

## Principios de Análisis RC506
1. **Determinismo Absoluto:** Todo insight proviene de reglas comparativas algebraicas explícitas.
2. **Cero Causalidad Falsa:** Se reportan observaciones factuales (ej. "El SLA disminuyó 5 pp"), prohibiendo suposiciones no verificadas ("porque faltaron operadores").
3. **Persistencia e Idempotencia:** `run_rc506_analysis` purga análisis previos del mismo período y cliente para evitar duplicación.
