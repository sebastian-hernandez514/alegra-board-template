# Architecture — Alegra Board Automatizado
*Definida: 11 Apr 2026 · Actualizada: 11 Apr 2026*

---

## Visión

El board ejecutivo mensual/trimestral se genera solo. Los dueños de cada sección llenan sus datos en Google Sheets. Las métricas se obtienen automáticamente de Redshift. Un script Python combina ambos y produce el HTML final listo para PDF.

```
RS → metrics.yaml  ┐
Google Sheets       ├→ generate.py → output/*.html → PDF
editorial.yaml      ┘
```

**Sin intervención manual en el código.** Sin copiar y pegar números. Sin abrir un editor HTML.

---

## Estructura de carpetas actual

```
Template Board/
├── templates/              ← Moldes Jinja2 (un archivo por sección)  ✅ COMPLETO
│   ├── 1_inicio.j2
│   ├── 2_discussion_topic.j2
│   ├── 3_arr_walk.j2
│   ├── 4_financial_performance.j2
│   ├── 5_go_to_market.j2
│   └── 7_headcount.j2
│
├── data/
│   ├── config.yaml         ← Período activo: month_label, quarter_label  ✅
│   ├── metrics.yaml        ← Generado por fetch_metrics.py (output)
│   └── editorial/          ← Archivos que humanos (o IA) llenan antes del board  ✅
│       ├── ceo.yaml            ← CEO highlights, lowlights, rule of 40
│       ├── arr_walk.yaml       ← Asks por producto (Core/Lite) + Alanube insight
│       └── discussion_topics.yaml ← Discussion Topics (layouts: two_col / table)
│
├── output/                 ← HTML generado por generate.py (no editar a mano)
│
├── slides/                 ← HTML originales hardcodeados (referencia)
│
├── scripts/
│   ├── fetch_metrics.py    ← Redshift → data/metrics.yaml  ✅ IMPLEMENTADO
│   ├── generate.py         ← Orquestador: YAMLs + templates → output/*.html  ✅
│   ├── fetch_sheets.py     ← Google Sheets → data/sheets.yaml  ⏳ PENDIENTE
│   └── export_pdf.py       ← HTML → PDF  ⏳ PENDIENTE
│
├── styles/
│   └── base.css
│
└── docs/
    ├── ARCHITECTURE.md     ← Este archivo
    ├── DATA_SPEC.md        ← Contrato de datos: variable → fuente → query
    └── ...
```

---

## Capa de datos: tres fuentes, un contrato

La regla es simple: **cada dato va a su fuente natural.** El script `generate.py` no sabe ni le importa de dónde vino cada número — solo consume los YAMLs intermedios y renderiza.

```
fetch_metrics.py → lee Redshift + CSVs → data/metrics.yaml  ┐
fetch_sheets.py  → lee Sheets (⏳)   → data/sheets.yaml     ├→ generate.py → output/*.html → PDF
editorial/*.yaml → humanos los llenan                        ┘
```

### Fuente 1 — Redshift (métricas automáticas)
Todo número que viva en RS. `fetch_metrics.py` corre las queries definidas en `DATA_SPEC.md` y escribe `data/metrics.yaml`.

**Qué va aquí:** ARR, MRR, logos, churn, ARPA, CAC, CVR, payback, headcount numérico, funnel conversión.

### Fuente 2 — Google Sheets (datos que viven en Sheets)
Datos que el equipo ya mantiene en Sheets y no tiene sentido duplicar en RS. `fetch_sheets.py` los lee via API y escribe `data/sheets.yaml`.

**Qué va aquí:** eNPS, benchmark salarial, investment S&M por canal, datos de HR que no están en RS, KPIs de R&D que el equipo lleva en Sheets.

**Sheets relevantes identificadas:**

| Sheet / Tab | Dueño | Contenido |
|-------------|-------|-----------|
| People & Talent | HR | eNPS, attrición detalle, benchmark salarial, key hires |
| Investment S&M | Marketing | Desglose People / Paid Media / Other por país |
| R&D KPIs | CTO | Features shipped, bugs críticos, uptime, milestones |
| Config | Data team | Período activo, mes, año, FX rates |

### Fuente 3 — YAML local (contenido editorial puro)
Archivos de texto que un humano (o la IA) llena antes del board. Sin APIs, sin credenciales — solo editar un archivo y correr el script.

**Qué va aquí:** CEO H&L, Discussion Topics (cambian cada período, se definen ~1 día antes, pueden ser redactados con IA y revisados por el responsable).

```
data/editorial/
├── ceo.yaml                 ← CEO llena: highlights, lowlights, rule_of_40, monthly_headline
├── arr_walk.yaml            ← Asks al Board por producto (Core/Lite) + Alanube insight
└── discussion_topics.yaml   ← Discussion Topics: layout two_col o table, asks
```

**Ejemplo `ceo.yaml`:**
```yaml
highlights:
  - "ARR Core cruza hito histórico en Colombia — +31% YoY"
  - "Multi-Cuenta beta MX — 480 cuentas activadas en 2 semanas"
lowlights:
  - "Churn Lite supera 1.8% mensual en DR"
  - "SAT XML sync sigue con incidencias en MX"
rule_of_40: "<strong>Rule of 40:</strong> ARR growth YoY (+28%) + EBITDA (-4%) = 24"
monthly_headline: "Febrero cierra con ARR récord — lideran CO y MX en new adds."
```

**Ejemplo `arr_walk.yaml`:**
```yaml
products:
  - id: core
    action_title: "Core acelera en LatAm — ¿sostenemos expansión en MX?"
    asks:
      - title: "Churn threshold"
        text: "Net churn Core superó 1.2% en MX — ¿presupuesto defensivo o nuevos adds?"
  - id: lite
    action_title: "Lite lidera new adds — validar conversión a Core"
    asks:
      - title: "Conversión a Core"
        text: "Cohort Lite Jan-26: 6% convirtió a Core en 90 días. ¿Ajustamos el trigger?"
alanube_title: "Alanube ARR Walk — Documentos electrónicos"
alanube_insight: "Principal riesgo: cuentas emitiendo debe superar 70% antes de Q2."
```

---

## Capa de templates: Jinja2

Los archivos `templates/*.j2` son los HTML actuales de `slides/` con los valores hardcodeados reemplazados por variables Jinja2.

**Ejemplo — antes (hardcodeado):**
```html
<span class="ks-val">$27.4M</span>
<span class="ks-delta ks-pos">▲ 39% YoY</span>
```

**Ejemplo — después (template):**
```html
<span class="ks-val">{{ metrics.arr_total | format_usd }}</span>
<span class="ks-delta {{ 'ks-pos' if metrics.arr_yoy > 0 else 'ks-neg' }}">
  {{ metrics.arr_yoy | format_pct }} YoY
</span>
```

**Convenciones de variables:**
- `metrics.*` → valores numéricos de Redshift
- `editorial.*` → textos y narrativas de Google Sheets
- `config.*` → período activo, mes, año
- `spark.*` → datos de sparklines (arrays de 5 valores)

---

## Script orquestador: generate.py

**Flujo:**
1. Carga `data/config.yaml` (período, labels)
2. Carga `data/metrics.yaml` (output de `fetch_metrics.py`)
3. Carga todos los `data/editorial/*.yaml` y los funde en un solo contexto
4. Inyecta los `asks` de `arr_walk.yaml` en los productos de `metrics.arr_walk_products`
5. Renderiza cada `templates/*.j2` → `output/<nombre>.html`

**Uso:**
```bash
# Paso 1 — Fetch datos de Redshift (una vez por mes)
uv run --with boto3 --with pyyaml python3 scripts/fetch_metrics.py --month 2026-02

# Paso 2 — Renderizar (se puede repetir sin reconectar a RS)
uv run --with jinja2 --with pyyaml python3 scripts/generate.py

# Renderizar solo una sección
uv run --with jinja2 --with pyyaml python3 scripts/generate.py --template 3_arr_walk
```

---

## Clasificación de slides: automático vs editorial

| Sección | Slide | Tipo | Fuente |
|---------|-------|------|--------|
| S1 | Cover | Automático | `config.period` |
| S1 | CEO H&L | Editorial | Google Sheets `CEO_HL` |
| S1 | TOC | Estático | Template fijo |
| S1 | Monthly Performance | Automático | Redshift |
| S1 | YTD Performance | Automático | Redshift |
| S1 | ARR Global | Automático | Redshift |
| S2 | Discussion × 3 | Editorial | Google Sheets `Discussion_0N` |
| S3 | ARR Walk Core/Lite/Alanube | Automático | Redshift |
| S3 | Country Performance × 4 | Automático | Redshift |
| S4 | Product Performance | Automático | Redshift |
| S5 | New Logos | Automático | Redshift |
| S5 | Customer Acquisition | Automático | Redshift |
| S5 | Funnel | Automático | Redshift |
| S5 | Flywheel | Automático | Redshift |
| S6 | R&D | Mixto | RS (métricas) + Sheets (narrativa) |
| S7 | Headcount by Team | Mixto | RS (números) + Sheets (narrativa) |
| S7 | People & Talent | Mixto | RS (números) + Sheets (narrativa) |
| S8 | Appendix | Automático | Redshift |

**Resultado: ~80% automatizable desde Redshift. ~20% editorial que humanos llenan en Sheets.**

---

## Hoja de ruta de implementación

### ✅ Fase 1 — Data Spec
`docs/DATA_SPEC.md` documenta el contrato: cada variable del template → su fuente y query.

### ✅ Fase 2 — Templates
`slides/*.html` → `templates/*.j2` completo para las 6 secciones principales (1, 2, 3, 4, 5, 7).

### ✅ Fase 3 — fetch_metrics.py
Implementado. Corre 3 queries en Redshift y produce `data/metrics.yaml`:

| Query | Tabla | Para qué |
|-------|-------|----------|
| `_SQL_FACT_SUMMARY` | `dwh_facts.fact_customers_mrr` | ARR Walk Core/Lite por país/segmento — quarters, months, YTD. **Fuente única** (reemplazó `arr_walk_monthly_summary`) |
| `_SQL_LOGOS_ALL` | `dwh_facts.fact_customers_mrr` | Logos consolidados (COUNT DISTINCT, evita doble conteo entre segmentos) |
| `_SQL_INVESTMENT` | `db_finance.fact_cac_version_segments` | Investment S&M por país/segmento — últimos 13 meses |

Genera también:
- Sparklines SVG inline para el butterfly table de países
- `q_cards` (BoP/EoP por quarter) para los chart cards del ARR Walk
- Arrays de chart para Chart.js: `arr_new_rec`, `arr_churn`, `arr_net_new`, `logos_new`, etc.

Métricas cubiertas por CSV merges (no requieren RS):
- Budget: `arr_vs_budget`, `new_mrr_vs_budget`, `new_logos_vs_budget` · `merge_budget()`
- Financiero: `gross_margin`, `ebitda_margin`, `net_revenue` · `merge_pnl()`
- Payback: `payback_core`, `payback_lite` · `merge_payback()`

Métricas **no** cubiertas (pendientes de fuente):
- Headcount — requiere People & Talent

### ✅ Fase 4a — Editorial YAML local
Archivos en `data/editorial/` que humanos (o la IA) llenan antes del board:

| Archivo | Responsable | Contenido |
|---------|-------------|-----------|
| `config.yaml` | Data team | `month_label`, `quarter_label`, `prev_year` |
| `ceo.yaml` | CEO | Highlights, lowlights, rule of 40, headline |
| `arr_walk.yaml` | Product/Finance | Asks al Board por producto, insight Alanube |
| `discussion_topics.yaml` | Responsable por tema | Hasta 3 discussion topics (layout `two_col` o `table`) |

### ✅ Fase 5 — generate.py
Orquestador implementado. Lee los 3 YAML sources, inyecta `asks` editoriales en los productos de métricas, y renderiza todos los templates.

### ⏳ Fase 4b — fetch_sheets.py
Conectar a Google Sheets para leer datos financieros (P&L), eNPS, S&M investment, headcount detalle. Produce `data/sheets.yaml`. Requiere Google Sheets API credentials.

### ⏳ Fase 6 — export_pdf.py
Export automatizado a PDF. Opciones: Playwright (headless Chrome) o WeasyPrint.

---

## Decisiones de diseño

| Decisión | Razón |
|----------|-------|
| Jinja2 para templates | Estándar Python, sintaxis simple, sin dependencias pesadas |
| YAML para datos intermedios | Legible por humanos, debuggeable, permite revisar los datos antes de renderizar |
| Google Sheets para editorial | Los dueños de sección no tocan código — solo llenan una hoja |
| Redshift como fuente de verdad | Los números siempre vienen de la misma fuente que usa el equipo de datos |
| `--skip-fetch` flag | Permite iterar el diseño del template sin reconectar a RS en cada prueba |
| Un .j2 por sección | Espeja la estructura actual de slides — mínimo cambio organizacional |
