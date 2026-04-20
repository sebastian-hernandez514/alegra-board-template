# Template Board — Contexto para Claude

## Qué es esto
Sistema para generar automáticamente el board ejecutivo mensual de Alegra.
Jinja2 templates + datos de Redshift + YAMLs editoriales → HTML → PDF.

## Stack
- **Python** con `uv run --with boto3 --with pyyaml --with jinja2`
- **Redshift**: cluster `redshift-cluster-2`, db `data_table_bi`, user `datauser45`
- **Seguridad**: siempre usar `redshift_guard.py` (está en `/Users/sebastian_alegra/Alegra IA/`)
- **Autenticación RS**: perfil AWS SSO `alegra` (`~/aws-cli-v2/aws-cli/aws sso login --profile alegra`)

## Estado de implementación
| Componente | Estado |
|---|---|
| Templates Jinja2 (1,2,3,4,5,7) | ✅ Completo |
| `scripts/fetch_metrics.py` | ✅ Completo |
| `scripts/generate.py` | ✅ Completo |
| `data/editorial/` (ceo, arr_walk, discussion_topics) | ✅ Completo |
| `scripts/fetch_sheets.py` | ⏳ Pendiente |
| `scripts/export_pdf.py` | ⏳ Pendiente |

## Flujo de trabajo — ÚNICO flujo válido

```
templates/*.j2  →  diseño y estructura
data/metrics.yaml  →  datos Redshift (fetch_metrics.py)
data/editorial/*.yaml  →  textos que humanos llenan
        ↓
    generate.py
        ↓
output/*.html  →  resultado final (abrir en Chrome)
```

**Regla:** cambio de diseño = editar `templates/*.j2` + correr `generate.py`. Nunca editar `output/` a mano.
La carpeta `slides/` fue eliminada (16 Apr 2026) — era deuda técnica del período pre-pipeline.

## Archivos clave
- `scripts/fetch_metrics.py` — RS + CSVs → `data/metrics.yaml` (pipeline completo)
- `scripts/generate.py` — YAMLs + templates → `output/*.html`
- `data/config.yaml` — período activo (month_label, quarter_label)
- `data/editorial/` — contenido que humanos llenan antes del board
- `csv/Metricas_budget.csv` — budget anual completo (año completo, no cambia)
- `csv/P&L Histórico- ACtual.csv` — P&L real histórico (actualizar mensualmente)
- `csv/P&L Histórico - Budget.csv` — P&L budget (actualizar mensualmente)
- `docs/ARCHITECTURE.md` — arquitectura completa y decisiones de diseño
- `docs/DATA_SPEC.md` — contrato: variable del template → fuente → query

## Cómo correr el pipeline
```bash
# 1a. Mes nuevo — RS + CSVs (usa caché RS si no hay --refresh)
uv run --with boto3 --with pyyaml python3 scripts/fetch_metrics.py --month 2026-03

# 1b. Solo actualizaste un CSV (Payback, P&L, Budget) — sin tocar RS
uv run --with boto3 --with pyyaml python3 scripts/fetch_metrics.py --month 2026-03 --csv-only

# 2. Renderizar (repetir sin costo de RS)
uv run --with jinja2 --with pyyaml python3 scripts/generate.py

# Solo un template
uv run --with jinja2 --with pyyaml python3 scripts/generate.py --template 1_inicio
```

### Regla de oro
`metrics.yaml` es la única fuente que lee `generate.py`. Si el YAML no cambió, el HTML no cambia.
Nunca editar `metrics.yaml` a mano — siempre pasar por `fetch_metrics.py`.

## Queries RS (fetch_metrics.py)
| Query | Tabla | Para qué |
|---|---|---|
| `_SQL_FACT_SUMMARY` | `dwh_facts.fact_customers_mrr` | ARR Walk Core/Lite por país/segmento |
| `_SQL_LOGOS_ALL` | `dwh_facts.fact_customers_mrr` | Logos consolidados (sin doble conteo) |
| `_SQL_INVESTMENT` | `db_finance.fact_cac_version_segments` | Investment por país/segmento (13 meses) |

## Lógica de conversión FX (amount_mrr → USD)

Todas las métricas monetarias (ARR, New ARR, Churn ARR, Expansion, etc.) usan `amount_mrr` como fuente base. La conversión a USD se aplica en `_apply_fx_to_row()` **antes** de cualquier agregación:

| País (`app_version`) | Fuente de tasa | Lógica |
|---|---|---|
| `colombia`, `mexico`, `argentina`, `peru`, `spain` | `csv/paises_fx.csv` | `amount_mrr / round(tasa, N decimales)` |
| Todos los demás (DR, CR, Panama, USA, etc.) | `amount_usd_mrr` directo | Sin conversión — ya está en USD |

**Decimales por país:** CO/AR → entero · MX/PE → 1 decimal · ES → 3 decimales

**Archivo FX:** `csv/paises_fx.csv` — columnas `pais, fecha, valor`. Actualizar mensualmente.

**Nota DR (pendiente):** República Dominicana cambió de cobrar en USD a cobrar en DOP en julio 2025. Por ahora usa `amount_usd_mrr` como fallback. Confirmar con Finance la tasa oficial DOP/USD para actualizar.

**Cache version actual:** `v10-board-metrics-expansion-delta` — incrementar si se modifica cualquier lógica de RS.

## Lógica del ARR Walk (_SQL_FACT_SUMMARY)

El SQL usa un **CTE con LAG** para capturar el MRR del mes anterior por logo. Reglas críticas:

| Métrica | Fórmula | Por qué |
|---|---|---|
| **Churn MRR** | `COALESCE(prev_mrr_local, 0)` WHERE CHURN | `amount_mrr = 0` cuando churna — LAG obligatorio |
| **Upsell** | `amount_mrr - COALESCE(prev_mrr_local, 0)` WHERE EXPANSION | Delta, no total — sin esto infla 6-7x |
| **Downsell** | `amount_mrr - COALESCE(prev_mrr_local, 0)` WHERE CONTRACTION | Delta, no total |
| **Net Churn** (Python) | `react_m - churn_m` | Negativo cuando hay más churn que reactivaciones |
| **FX Impact** (Python) | `EoP - (BoP + New + Recov + React - Churn + Up + Down)` | Residual que hace cuadrar el walk |

**NUNCA** usar `amount_mrr` directo para Churn, Upsell o Downsell — los tres requieren LAG.
Ver detalles completos: `memory/feedback_mrr_walk.md`

## CSV merges automáticos (fetch_metrics.py)
| Función | CSV | Qué calcula |
|---|---|---|
| `merge_budget()` | `Metricas_budget.csv` | vs Budget para ARR, New MRR, New Logos, Churn |
| `merge_pnl()` | `P&L Histórico- ACtual.csv` + `P&L Histórico - Budget.csv` | Net Revenue, Gross Margin %, EBITDA Margin % con MoM/YoY/vs Budget |
| `merge_payback()` | `Payback.csv` | `payback_core` y `payback_lite` (Type=Todos del mes). `payback_hist`=16 hardcodeado (prom 2025: Core 16.5, Lite 16.6) |

### Lógica de signos P&L
- **Income** (Operating Income, Refunds): vienen negativos → `abs()`. Total Revenue = abs(OpInc) - abs(Refunds)
- **CoR, CAC, Product, G&A**: `sum as-is → display abs()`
- **D&A, Taxes**: `abs() → restar`
- **Non-Op, Financial Yield**: vienen negativos → `sum as-is → restar` (doble negativo = sumar)
- **Provisions**: `sum * -1`
- **Interco**: Operating Income y Non-Op Income `* -1`; Expenses, CoD, Taxes `as-is`. Total = (Inc inv) - (Exp + CoD + Taxes)
- **Gross Margin** = (Revenue - CoR) / Revenue
- **EBITDA** = Gross Income - (CAC + Product + G&A)
- **Net Income** = EBITDA - Non_Op - D&A - Fin_Yield - Taxes

## Variables pendientes (placeholders "N/A" en metrics.yaml)
- Datos de Headcount — requieren fuente People & Talent

## Fuente de datos — decisión arquitectural
**Fuente única: `dwh_facts.fact_customers_mrr`** para todos los datos de logos y MRR.
- `bi_strategic.arr_walk_monthly_summary` fue eliminada como fuente — tiene delays y datos incompletos para el mes en curso.
- Cache version actual: `v6-board-metrics`
- Queries activas: `_SQL_FACT_SUMMARY` (reemplaza summary + new logos country + churn country), `_SQL_LOGOS_ALL`, `_SQL_INVESTMENT`

## Template 1 — MoM vs QoQ (decisión)
- **Meses normales** (ene, feb, abr, may, jul, ago, oct, nov): comparación **MoM**
- **Cierre de quarter** (mar, jun, sep, dic): comparación **QoQ** (quarter actual vs quarter anterior)
- Auto-detectado en `fetch_metrics.py`: `is_quarter_end = int(mes) in (3, 6, 9, 12)`
- Variables QoQ en `metrics.yaml`: `arr_qoq`, `new_mrr_qoq`, `new_logos_qoq` (+ `_positive`)
- El template `1_inicio.j2` usa `{% if metrics.is_quarter_end %}` para cambiar pill y valor
- P&L (Net Revenue, Gross Margin, EBITDA) siempre muestra MoM — son métricas mensuales

### Comportamiento en cierre de Q
- `new_logos` y `new_mrr` (valor principal) = **suma de los 3 meses del Q**
- `new_logos_vs_budget` y `new_mrr_vs_budget` = real Q vs **suma de budget de los 3 meses del Q**
- `logo_churn_core` / `logo_churn_global` = **promedio de las 3 tasas mensuales del Q**
- ARR EoP y Churn vs Budget siempre usan el mes puntual (no suma)

### Fórmula de Churn (validada con Jhon Gallego — Retention)
```
Churn Rate mensual = (logos CHURN - logos REACTIVATED) / BoP
BoP = logos activos del mes anterior = COUNT DISTINCT WHERE event_logo NOT IN ('CHURN', 'AWAITING PAYMENT')
En cierre de Q: promedio de los 3 Churn Rate mensuales del Q
```

## Template 1 — Slide 7: Global Country Performance (último slide de 1_inicio.j2)
Mismo formato butterfly (Core vs Lite) que Template 3, pero con datos **globales** (todos los países, sin filtro).

### Fuente de datos global
- **ARR, New ARR, New Logos, Logos Growth, Net New ARR, ARPA, Churn Rate** → `segs_raw["Core"]` / `segs_raw["Lite"]` — vienen del query `_SQL_FACT_SUMMARY` agregado sin filtro de país. Incluye CO, MX, DR, CR y cualquier otro país en la BD.
- **Investment** → suma de todos los países en el dict `investment` (que viene de `_SQL_INVESTMENT`). Actualmente cubre los 4 países principales.
- **CAC** → Investment global / New Logos global
- **Payback** → `csv/Payback.csv` con `Type="Todos"`, segmentos `Core` y `Lite`
- Variable en `metrics.yaml`: `global_country` (mismo esquema que cada entry de `countries`)

### Regla de colores de deltas (aplica también a Template 3)
- **Investment**: delta en negro/neutro — sin verde/rojo
- **Churn Rate, CAC**: delta invertido — negativo = verde (mejora), positivo = rojo (deterioro)
- **Resto**: positivo = verde, negativo = rojo

## Template 3 — Country Performance (3_arr_walk.j2)
Butterfly rows por país (CO/MX/DR/CR) · Core vs Lite. Tabla `<table>` de 7 columnas: YoY | MoM(QoQ) | Valor | Métrica | Valor | MoM(QoQ) | YoY.

| Métrica | Fuente | Estado |
|---|---|---|
| Investment | RS `db_finance.fact_cac_version_segments` · 13 meses · `_SQL_INVESTMENT` | ✅ |
| CAC | Investment / New Logos (calculado) | ✅ |
| ARPA | MRR EoP / Logos EoP (mensual, sin ×12) | ✅ |
| Payback | `csv/Payback.csv` · serie completa por país/segmento | ✅ |
| Churn Rate | `(logos_churn - logos_react) / logos_BoP` · directo desde `fact_customers_mrr` | ✅ |
| New Logos | `fact_customers_mrr` con `event_logo = 'NEW'` y `segment_type_def` | ✅ |

## Preferencias
- Comunicación en español
- No leer archivos completos si la tarea es un reemplazo puntual — pedir línea exacta
- **NUNCA lanzar Agent para editar archivos ya leídos** — usar Edit directo, en paralelo si son múltiples archivos. Un Agent mal usado costó ~20K tokens en ediciones simples de HTML.
