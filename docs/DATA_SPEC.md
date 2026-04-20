# DATA_SPEC — Alegra Board
*Contrato de datos: qué variable del template, de dónde viene, qué query la produce.*
*Última actualización: 15 Apr 2026*

---

## Cómo leer este documento

Cada entrada tiene:
- **Variable** — nombre en el template Jinja2 (`{{ metrics.arr_total }}`)
- **Fuente** — RS / Sheets / YAML
- **Tabla / Sheet** — origen exacto
- **Lógica** — qué query o transformación produce el valor
- **Estado** — ✅ query validada · ⏳ pendiente · ❓ fuente por confirmar

---

## Config global

| Variable | Fuente | Valor / Lógica |
|----------|--------|----------------|
| `config.period` | Manual | `"2026-03"` — YYYY-MM del período activo |
| `config.month_label` | Manual | `"March 2026"` |
| `config.prev_month_label` | Manual | `"February 2026"` |
| `config.quarter_label` | Manual | `"1Q26"` |
| `config.year` | Manual | `2026` |

---

## Sección 1 — Inicio

### Slide 4 · Monthly Performance

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.arr_total` | RS | `fact_customers_mrr` | `SUM(amount_mrr * 12)` WHERE `date_month = period` AND `event_logo NOT IN ('CHURN','AWAITING PAYMENT')` — vía `_SQL_FACT_SUMMARY`. Para CO/MX/AR/PE/ES se divide por FX de `paises_fx.csv` (tasa redondeada al entero); resto se usa tal cual (ya en USD). | ✅ |
| `metrics.arr_mom` | RS | `fact_customers_mrr` | ARR período actual vs período anterior, % cambio | ⏳ |
| `metrics.arr_yoy` | RS | `fact_customers_mrr` | ARR período actual vs mismo mes año anterior, % cambio | ⏳ |
| `metrics.arr_vs_plan` | Sheets | Plan sheet | (arr_actual - arr_plan) / arr_plan | ❓ |
| `metrics.new_mrr` | RS | `fact_customers_mrr` | Mes normal: MRR new del mes (`event_logo='NEW'`). Cierre de Q: **suma de los 3 meses del Q**. Vía `_SQL_FACT_SUMMARY` + `build_yaml` | ✅ |
| `metrics.new_mrr_mom` | RS | `fact_customers_mrr` | % cambio vs mes anterior | ✅ |
| `metrics.new_mrr_vs_budget` | CSV | `Metricas_budget.csv` | Mes normal: real vs budget del mes. Cierre de Q: **suma Q real vs suma Q budget** · `merge_budget()` | ✅ |
| `metrics.new_logos` | RS | `fact_customers_mrr` | Mes normal: logos new del mes. Cierre de Q: **suma de los 3 meses del Q** · `build_yaml` | ✅ |
| `metrics.new_logos_mom` | RS | `fact_customers_mrr` | % cambio vs mes anterior | ✅ |
| `metrics.new_logos_vs_budget` | CSV | `Metricas_budget.csv` | Mes normal: real vs budget del mes. Cierre de Q: **suma Q real vs suma Q budget** · `merge_budget()` | ✅ |
| `metrics.logo_churn_core` | RS | `fact_customers_mrr` | `(logos CHURN - logos REACTIVATED) / BoP` · BoP = logos activos mes anterior (excl. CHURN y AWAITING PAYMENT). Cierre de Q: **promedio de las 3 tasas mensuales**. Validado con Jhon Gallego (Retention) | ✅ |
| `metrics.logo_churn_global` | RS | `fact_customers_mrr` | Ídem para todos los segmentos combinados | ✅ |
| `metrics.logo_churn_vs_budget_pp` | CSV | `Metricas_budget.csv` | churn_real - churn_budget (en pp) · `merge_budget()` | ✅ |
| `metrics.net_revenue` | CSV | `P&L Histórico- ACtual.csv` | abs(Operating Income) - abs(Refunds) · `merge_pnl()` | ✅ |
| `metrics.gross_margin` | CSV | `P&L Histórico- ACtual.csv` | (Revenue - CoR) / Revenue × 100 · `merge_pnl()` | ✅ |
| `metrics.ebitda_margin` | CSV | `P&L Histórico- ACtual.csv` | (Gross Income - CAC - Product - G&A) / Revenue × 100 · `merge_pnl()` | ✅ |
| `metrics.payback_core` | CSV | `Payback.csv` | Fila `Type=Todos, Segment=Core` del mes activo · `merge_payback()` | ✅ |
| `metrics.payback_lite` | CSV | `Payback.csv` | Fila `Type=Todos, Segment=Lite` del mes activo · `merge_payback()` | ✅ |
| `metrics.payback_hist` | Hardcoded | — | Promedio 2025 = **16 mo** (Core avg 16.5, Lite avg 16.6) · constante en `merge_payback()` | ✅ |

### Slide 5 · YTD Performance

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.ytd_arr` | RS | `fact_customers_mrr` | ARR EoP del período actual | ⏳ |
| `metrics.ytd_arr_vs_plan` | Sheets | Plan sheet | % vs plan acumulado YTD | ❓ |
| `metrics.ytd_new_logos` | RS | `fact_customers_mrr` | `COUNT(DISTINCT id_company)` WHERE `event_logo IN ('NEW','REACTIVATED')` AND `date_month BETWEEN year_start AND period` | ⏳ |
| `metrics.ytd_new_logos_yoy` | RS | `fact_customers_mrr` | New logos YTD actual vs YTD mismo período año anterior | ⏳ |
| `metrics.smb_logos_eop` | RS | `fact_customers_mrr` | `COUNT(DISTINCT CASE WHEN event_logo != 'CHURN' THEN id_company END)` WHERE `date_month = period` — logos activos EoP (excluye churn) | ✅ |
| `metrics.accountant_logos_eop` | RS | `fact_customers_mrr` | Logos activos con `channel_name = 'Accountant'` EoP | ⏳ |

### Slide 6 · ARR Global — Flujo de Suscriptores

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `spark.arr_global[N]` | RS | `fact_customers_mrr` | ARR total últimos 13 meses (array) | ⏳ |
| `spark.new_arr[N]` | RS | `fact_customers_mrr` | New ARR últimos 13 meses (array) | ⏳ |
| `spark.churn_arr[N]` | RS | `fact_customers_mrr` | Churn ARR últimos 13 meses (array) | ⏳ |
| `metrics.net_new_arr_qtd` | RS | `fact_customers_mrr` | Net New ARR acumulado del trimestre actual | ⏳ |
| `metrics.net_new_arr_qtd_prev` | RS | `fact_customers_mrr` | Net New ARR trimestre anterior | ⏳ |

---

## Sección 3 — ARR Walk

### Slides 2–3 · ARR Walk Core / Lite

> Aplica por producto (`product_name IN ('Core','Lite')`). Las variables tienen sufijo `_core` o `_lite`.

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.arr_bop_{p}` | RS | `fact_customers_mrr` | ARR EoP del mes anterior = BoP del mes actual | ⏳ |
| `metrics.new_arr_{p}` | RS | `fact_customers_mrr` | `SUM(amount_mrr)` WHERE `event_logo = 'NEW'` → convertido a USD vía `paises_fx.csv` | ⏳ |
| `metrics.expansion_upsell_{p}` | RS | `fact_customers_mrr` | `SUM(amount_mrr)` WHERE `event_logo = 'EXPANSION UPSELL'` → convertido a USD vía `paises_fx.csv` | ⏳ |
| `metrics.expansion_cross_{p}` | RS | `fact_customers_mrr` | `SUM(amount_mrr)` WHERE `event_logo = 'EXPANSION CROSS SELLING'` → convertido a USD vía `paises_fx.csv` | ⏳ |
| `metrics.contraction_down_{p}` | RS | `fact_customers_mrr` | `SUM(amount_mrr)` WHERE `event_logo = 'CONTRACTION DOWNSELL'` → convertido a USD vía `paises_fx.csv` | ⏳ |
| `metrics.contraction_cross_{p}` | RS | `fact_customers_mrr` | `SUM(amount_mrr)` WHERE `event_logo = 'CONTRACTION CROSS SELLING'` → convertido a USD vía `paises_fx.csv` | ⏳ |
| `metrics.churn_{p}` | RS | `fact_customers_mrr` | `SUM(amount_mrr)` WHERE `event_logo = 'CHURN'` → convertido a USD vía `paises_fx.csv` | ⏳ |
| `metrics.reactivated_{p}` | RS | `fact_customers_mrr` | `SUM(amount_mrr)` WHERE `event_logo IN ('REACTIVATED','RECOVERED')` → convertido a USD vía `paises_fx.csv` | ⏳ |
| `metrics.arr_eop_{p}` | RS | `fact_customers_mrr` | ARR EoP = BoP + todos los movimientos | ⏳ |
| `metrics.net_new_arr_{p}` | RS | `fact_customers_mrr` | New + Expansion − Contraction − Churn + Reactivated | ⏳ |

### Slides 5–8 · Country Performance (CO, MX, DR, CR)

> Aplica por país (`team IN ('CO','MX','DR','CR')`) y por producto. Variables con sufijo `_{country}_{p}`.

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.arr_{c}_{p}` | RS | `fact_customers_mrr` | ARR EoP por país y producto | ⏳ |
| `metrics.arr_mom_{c}_{p}` | RS | `fact_customers_mrr` | % cambio MoM | ⏳ |
| `metrics.arr_yoy_{c}_{p}` | RS | `fact_customers_mrr` | % cambio YoY | ⏳ |
| `metrics.net_new_arr_{c}_{p}` | RS | `fact_customers_mrr` | New + Expansion − Contraction − Churn + Reactivated | ⏳ |
| `metrics.new_logos_{c}_{p}` | RS | `fact_customers_mrr` | `COUNT(DISTINCT id_company)` WHERE `event_logo IN ('NEW','REACTIVATED')` | ⏳ |
| `metrics.churn_logos_{c}_{p}` | RS | `fact_customers_mrr` | `COUNT(DISTINCT id_company)` WHERE `event_logo = 'CHURN'` | ⏳ |
| `metrics.arpa_{c}_{p}` | RS | `fact_customers_mrr` | ARR EoP / logos activos EoP | ⏳ |
| `metrics.investment_{c}_{p}` | Sheets | Investment S&M | S&M spend mensual por país y producto | ❓ |
| `metrics.cac_{c}_{p}` | RS + Sheets | `fact_customers_mrr` + Investment | Investment / New Logos | ⏳ |
| `metrics.payback_{c}_{p}` | RS + Sheets | `fact_customers_mrr` + Investment | CAC / (ARPA × gross_margin) | ⏳ |
| `spark.arr_{c}_{p}[N]` | RS | `fact_customers_mrr` | ARR últimos 5 meses por país y producto (array para sparkline) | ⏳ |

---

## Sección 5 — Go to Market

### Slide 2 · New Logos

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.new_logos_{p}` | RS | `fact_customers_mrr` | `COUNT(DISTINCT id_company)` WHERE `event_logo IN ('NEW','REACTIVATED')` por producto | ⏳ |
| `metrics.new_logos_mom_{p}` | RS | `fact_customers_mrr` | % cambio vs mes anterior | ⏳ |
| `metrics.new_logos_yoy_{p}` | RS | `fact_customers_mrr` | % cambio vs mismo mes año anterior | ⏳ |
| `spark.new_logos_{p}_{c}[N]` | RS | `fact_customers_mrr` | New logos últimos 13 meses por producto y país (array para stacked bar) | ⏳ |
| `metrics.sm_people_{p}` | Sheets | Investment S&M | Gasto People del período por producto | ❓ |
| `metrics.sm_paid_{p}` | Sheets | Investment S&M | Gasto Paid Media del período por producto | ❓ |
| `metrics.sm_other_{p}` | Sheets | Investment S&M | Gasto Other del período por producto | ❓ |

### Slide 3 · Customer Acquisition

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.paid_media_pct_{p}` | RS + Sheets | `fact_customers_mrr` + Investment | Logos adquiridos vía Paid Media / total logos × 100 | ⏳ |
| `spark.paid_media_pct_{p}[N]` | RS + Sheets | idem | Últimos 13 meses (array para line chart) | ⏳ |
| `metrics.top2_concentration` | RS | `fact_customers_mrr` | % de logos cubiertos por los 2 canales principales | ⏳ |

### Slide 4 · Acquisition Funnel

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.cvr_{c}` | RS | `bi_funnel_master_table` | Logos convertidos / signups totales × 100 por país | ⏳ |
| `metrics.cvr_avg_{c}` | RS | `bi_funnel_master_table` | Promedio histórico de CVR por país | ⏳ |
| `metrics.signups_{c}` | RS | `bi_funnel_master_table` | Total signups del período por país | ⏳ |
| `spark.cvr_{c}[N]` | RS | `bi_funnel_master_table` | CVR últimos 13 meses por país (array para line chart) | ⏳ |

### Slide 5 · Accountant Flywheel

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.flywheel_new_adds[N]` | RS | `fact_customers_mrr` | Logos nuevos canal Accountant por mes (array 13m) | ⏳ |
| `metrics.flywheel_churn[N]` | RS | `fact_customers_mrr` | Logos churned canal Accountant por mes (array 13m) | ⏳ |
| `metrics.flywheel_gap` | RS | `fact_customers_mrr` | New Adds − Net Churn del período | ⏳ |
| `metrics.flywheel_stock[N]` | RS | `fact_customers_mrr` | Logos activos canal Accountant acumulado (array 13m) | ⏳ |

---

## Sección 7 — Headcount

### Slide 2 · Headcount by Team

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.hc_total` | Sheets | People & Talent | Headcount total EoP | ❓ |
| `metrics.hc_engineering` | Sheets | People & Talent | HC equipo Engineering | ❓ |
| `metrics.hc_sales` | Sheets | People & Talent | HC equipo Sales | ❓ |
| `metrics.hc_marketing` | Sheets | People & Talent | HC equipo Marketing | ❓ |
| `metrics.hc_operations` | Sheets | People & Talent | HC equipo Operations | ❓ |
| `metrics.hc_plan_{team}` | Sheets | People & Talent | HC plan por equipo | ❓ |
| `spark.hc_{team}[N]` | Sheets | People & Talent | HC últimos 5 meses por equipo (array) | ❓ |

### Slide 3 · People & Talent

| Variable | Fuente | Tabla | Lógica | Estado |
|----------|--------|-------|--------|--------|
| `metrics.enps` | Sheets | People & Talent | Score eNPS del período | ❓ |
| `metrics.enps_prev` | Sheets | People & Talent | eNPS período anterior | ❓ |
| `metrics.attrition_pct` | Sheets | People & Talent | % attrición del mes | ❓ |
| `metrics.turnover_pct` | Sheets | People & Talent | % turnover acumulado | ❓ |
| `spark.hires[N]` | Sheets | People & Talent | Hires últimos 6 meses (array) | ❓ |
| `spark.attrition[N]` | Sheets | People & Talent | Attrición últimos 6 meses (array) | ❓ |
| `editorial.key_hires` | YAML | `editorial/headcount.yaml` | Lista de key hires del período | ⏳ |
| `editorial.talent_risks` | YAML | `editorial/headcount.yaml` | Riesgos de talento identificados | ⏳ |

---

## Sección 2 — Discussion Topics (100% editorial)

| Variable | Fuente | Archivo | Lógica | Estado |
|----------|--------|---------|--------|--------|
| `editorial.discussion[0].title` | YAML | `editorial/discussion_01.yaml` | Título del tema | ⏳ |
| `editorial.discussion[0].context` | YAML | `editorial/discussion_01.yaml` | Párrafo de contexto | ⏳ |
| `editorial.discussion[0].proposal` | YAML | `editorial/discussion_01.yaml` | Propuesta o análisis | ⏳ |
| `editorial.discussion[0].asks` | YAML | `editorial/discussion_01.yaml` | Lista de preguntas al board (2-3) | ⏳ |
| *(ídem para discussion[1] y discussion[2])* | | | | |

---

## Sección 1 — CEO H&L (100% editorial)

| Variable | Fuente | Archivo | Estado |
|----------|--------|---------|--------|
| `editorial.highlights[0..2]` | YAML | `editorial/ceo.yaml` | ✅ |
| `editorial.lowlights[0..2]` | YAML | `editorial/ceo.yaml` | ✅ |

---

## Estado de fuentes por confirmar (❓)

Estas variables necesitan que el equipo confirme en qué Sheet viven exactamente:

| Variable | Necesita |
|----------|---------|
| `metrics.*_vs_plan` | Sheet de presupuesto/plan — nombre y tab |
| `metrics.gross_margin`, `metrics.ebitda_margin`, `metrics.net_revenue` | ✅ Resuelto — `csv/P&L Histórico- ACtual.csv` vía `merge_pnl()` |
| `metrics.investment_*` | Sheet de S&M Investment — nombre y tab |
| `metrics.hc_*` | Sheet de People & Talent — nombre y tab |
| `metrics.enps`, `metrics.attrition_pct` | Sheet de People & Talent — nombre y tab |

---

## Leyenda de sufijos

| Sufijo | Valores posibles |
|--------|-----------------|
| `{p}` | `core` · `lite` · `alanube` |
| `{c}` | `co` · `mx` · `dr` · `cr` |
| `[N]` | Array de N valores para charts/sparklines |
