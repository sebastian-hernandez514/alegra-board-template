# Narrative — Alegra Board Template
*Guión editorial: action titles por sección y slide*
*Última actualización: 10 Apr 2026*

---

## Regla global

**Todo slide de contenido debe declarar el insight en el título, no la categoría.**

- Incorrecto: "ARR Walk — Core" (etiqueta descriptiva)
- Correcto: "Core Net New ARR cayó 88% QoQ — churn supera adiciones por primera vez en 4 trimestres" (insight accionable)

Cuando los datos reales lleguen, actualizar primero este archivo y luego editar la línea HTML indicada en cada entrada.

---

## Sección 1 — Inicio (`slides/1_inicio.html`)

### Slide 1 · Cover
> No requiere action title — es portada.

---

### Slide 2 · CEO Highlights / Lowlights
**Action title:** `Crecemos en ARR, pero churn elevado y EBITDA bajo plan exigen decisión en {{Month}}`
**Insight declarado:** El ARR crece sólidamente, pero los dos lowlights estructurales (churn sobre target y EBITDA bajo presupuesto) requieren atención explícita del board.
**Dónde editar:** `slide-header > span.title` (línea ~113)

---

### Slide 3 · Table of Contents
> No requiere action title — es navegación.

---

### Slide 4 · Monthly Performance
**Action title:** `ARR $27.4M, +39% YoY y +6% vs plan — Logo Churn en 3.5% (0.8pp sobre presupuesto) comprime el crecimiento neto`
**Insight declarado:** El crecimiento de ARR es sólido, pero el riesgo principal es el churn que supera el presupuesto y comprime el crecimiento neto de logos.
**Dónde editar:** `.ks-headline.ks-headline-blue` (línea ~248)
**Nota:** Este slide no tiene `slide-header` tradicional — el `.ks-headline` es el título visible.

---

### Slide 5 · YTD Performance
**Action title:** `ARR 6% sobre plan y +39% YoY — el crecimiento es de ARPA, no de volumen: new logos −9% YoY`
**Insight declarado:** El año va bien en ARR, pero la calidad del crecimiento es diferente al plan: más revenue por logo, menos logos nuevos. Señal a monitorear para sostenibilidad.
**Dónde editar:** `.ks-headline.ks-headline-green` (línea ~346)
**Nota:** Mismo patrón que slide 4 — `.ks-headline` es el título visible.

---

### Slide 6 · ARR Global — Flujo de Suscriptores
**Action title:** `Net New ARR colapsó a $0.2M en 1Q26 — churn +47% YoY absorbe el 89% de las nuevas adiciones`
**Insight declarado:** El flujo de suscriptores muestra un deterioro severo en 1Q26: el churn creció 47% YoY y la adición neta quedó en $0.2M vs $2.4M el trimestre anterior.
**Dónde editar:** `slide-header > span` (línea ~583)

---

## Sección 2 — Discussion Topics (`slides/2_discussion_topic.html`)

### Slide 2 · GTM Strategy for Accountants *(content slide)*
**Action title:** `¿Convertimos el canal contador a freemium? Piloto MX activo — el Board debe avalar el escalamiento`
**Insight declarado:** Modelo propuesto: accountant $0 + revenue share $10 USD/SMB activado. Piloto en MX desde Jan 2026. El board debe decidir si escalar.
**Dónde editar:** `slide-header > span.title` (línea ~134)

---

### Slide 4 · Product Benchmark — Alegra MX vs. Contalink *(content slide)*
**Action title:** `Alegra lidera en SMB (POS, inventario, CRM) pero pierde en cumplimiento SAT — brecha crítica a cerrar en Q2`
**Insight declarado:** Ventaja competitiva en stack SMB (POS, inventario, CRM); gap en SAT/RFC compliance que impulsa preferencia por Contalink entre contadores.
**Dónde editar:** `slide-header > span.title` (línea ~203)

---

### Slide 6 · AI in Product — Current State & Roadmap *(content slide)*
**Action title:** `IA en producción con adopción limitada — ¿aceleramos el Financial Advisor agent ante la presión de Fintoc y Xepelin?`
**Insight declarado:** Anomaly detection con baja adopción por discoverability. Q2: reconciliation agent + collections copilot. Q3: Financial Advisor agent. Board debe decidir prioridad e inversión.
**Dónde editar:** `slide-header > span.title` (línea ~286)

---

## Sección 3 — ARR Walk (`slides/3_arr_walk.html`)

### Slide 1 · Section Cover
> No requiere action title — es cover de sección.

---

### Slide 2 · ARR Walk — Core
**Action title:** `Net New ARR Core −88% QoQ a $0.2M — churn +44% YoY supera las nuevas adiciones`
**Insight declarado:** Net New ARR colapsó de $1.6M (4Q25) a $0.2M. Churn -$0.75M (+26% QoQ, +44% YoY) absorbe la mayor parte de la adición nueva.
**Dónde editar:** `slide-header > div > span:first-child` (línea ~341) — estructura custom, NO span.title

---

### Slide 3 · ARR Walk — Lite
**Action title:** `Lite Net New ARR llegó a $0.0M en 1Q26 — crecimiento de logos se detuvo completamente`
**Insight declarado:** Net New ARR Lite cayó de $0.8M (4Q25) a $0.0M. Logos 18,000 sin crecimiento neto.
**Dónde editar:** `slide-header > div > span:first-child` (línea ~430) — estructura custom, NO span.title

---

### Slide 4 · ARR Walk — Alanube
**Action title:** `Alanube +38% MoM a $232K ARR — 31 de 36 nuevas cuentas en onboarding, upside real aún por realizarse`
**Insight declarado:** ARR subestima el potencial real: 31 nuevas cuentas pagan pero no emiten aún. Impacto completo en 30-60 días.
**Dónde editar:** `slide-header > span.title` (línea ~518)

---

### Slide 5 · Colombia
**Action title:** `🇨🇴 Colombia lidera en ARR ($8.2M Core) pero cae −12.6% YoY — Net New ARR negativo en ambos segmentos`
**Insight declarado:** Mercado más grande pero con contracción YoY en Core y Lite. Net New ARR negativo en ambos segmentos.
**Dónde editar:** `slide-header > span.title` (línea ~596)

---

### Slide 6 · México
**Action title:** `🇲🇽 México: churn Core en 5.8% con +55% MoM — el mercado de mayor deterioro del trimestre`
**Insight declarado:** Churn Core 5.8% es el más alto del portfolio y subió 55% MoM. Net New ARR negativo en Core y Lite.
**Dónde editar:** `slide-header > span.title` (línea ~625)

---

### Slide 7 · República Dominicana
**Action title:** `🇩🇴 DR: único mercado verde — Net New ARR positivo en Core (+82% YoY) y Lite (+64% YoY)`
**Insight declarado:** Único país con ARR creciendo YoY en ambos segmentos. Net New ARR positivo y acelerándose.
**Dónde editar:** `slide-header > span.title` (línea ~654)

---

### Slide 8 · Costa Rica
**Action title:** `🇨🇷 Costa Rica: ARR Core +22.8% YoY con Net New positivo — CAC $110 y Payback 4.8m, el más eficiente del portfolio`
**Insight declarado:** Crecimiento sólido en ambos segmentos con las mejores métricas de eficiencia de adquisición del portfolio.
**Dónde editar:** `slide-header > span.title` (línea ~683)

---

## Sección 4 — Financial Performance (`output/4_financial_performance.html`)

### Slide 2 · P&L Quarterly vs Prior Year
**Action title:** `EBITDA margin pasa de −14.8pp en Q1 2025 a +10.3pp en Q1 2026 — mejora de 25pp en un año`
**Dónde editar:** `slide-header-title` (slide 2 de `templates/4_financial_performance.j2`)

### Slide 3 · P&L Quarterly vs Budget 2026
**Action title:** `Q1 2026 supera Budget en todos los frentes — EBITDA margin +13.7pp sobre el plan`
**Dónde editar:** `slide-header-title` (slide 3)

### Slide 4 · OpEx YTD Mar
**Action title:** `S&M se ejecuta 17% bajo budget — eficiencia en Paid Media y eventos libera $412K de OpEx`
**Dónde editar:** `slide-header-title` (slide 4)

### Slide 5 · GLO Revenue Bridge
**Action title:** `New Logos y recuperación de ciclos pendientes impulsan +$129K de Revenue en Marzo`
**Dónde editar:** `slide-header-title` (slide 5)

### Slide 6 · Accumulated Cash Flow
**Action title:** `Saldo de Caja cierra Q1 en $4,097K — +97% vs Budget, outflows $1,020K bajo el plan`
**Dónde editar:** `slide-header-title` (slide 6)

### Slide 7 · Saldo de Caja + Cash Burn
**Action title:** `Saldo de Caja $4,097K en Q1 26 — +94% vs Budget y burn trimestral en mínimo histórico`
**Dónde editar:** `slide-header-title` (slide 7)

---

## Sección 5 — Go to Market (`slides/5_go_to_market.html`)

### Slide 2 · New Logos
**Action title:** `New Logos Core −20.5% YoY mientras Lite rebota +35% MoM — la inversión S&M Lite está traccionando`
**Insight declarado:** Divergencia Core/Lite: Core cae YoY pero Lite crece con S&M +27%. La inversión en Lite está generando resultados.
**Dónde editar:** `slide-header > span.title` (línea ~561)

---

### Slide 3 · Summary Customer Acquisition
**Action title:** `Paid Media representa el 57% de adquisición Lite (máximo histórico) — concentración en un canal es riesgo si el CAC sube`
**Insight declarado:** Máximo histórico de Paid Media en Lite. Top 2 canales = ~81% de adquisición. Diversificación orgánica es prioridad H1.
**Dónde editar:** `slide-header > span.title` (línea ~661)

---

### Slide 4 · Acquisition Funnel
**Action title:** `Funnel heterogéneo — DR y CR en máximos históricos de CVR, MX volátil, CO en recuperación`
**Insight declarado:** Divergencia entre mercados: DR rompe techo histórico, CR cierra año récord al 11.2%, MX sin tendencia consolidada.
**Dónde editar:** `slide-header > span.title` (línea ~735)

---

### Slide 5 · Accountant Flywheel
**Action title:** `Gap Flywheel cayó a +68 (mínimo del período) — si el churn no cede en Q2, el canal contador deja de crecer`
**Insight declarado:** Gap neto = +68 (mínimo histórico). Churn +34% en 2 meses. Meta Q2: gap >100 vía KAM + CX en primeras 4 semanas.
**Dónde editar:** `slide-header > span.title` (línea ~825)

---

### Slide 6 · Accountant Flywheel (cont.)
> Placeholder sin contenido — no requiere action title hasta definir el contenido.

---

## Sección 7 — Headcount (`slides/7_headcount.html`)

### Slide 2 · Headcount Summary
**Action title:** `Team 39 personas bajo plan — Acquisition a 87% del forecast pone el pipeline en riesgo estructural`
**Insight declarado:** Acquisition −16.9% YoY y 6 meses consecutivos bajo plan. Turnover 3.6 vs 2.76 FY24. Prod & Dev único equipo creciendo (+8.9%).
**Dónde editar:** `slide-header > span.title` (línea ~345)

---

### Slide 3 · People & Talent
**Action title:** `eNPS cayó 11 pts y attrición lleva 3 meses al alza — el benchmark salarial de H1 es la decisión crítica de retención`
**Insight declarado:** eNPS 59 pts (−11 vs H2 2025). Attrición 3.68% en enero, 3er mes consecutivo al alza. Drivers: compensación y bienestar. Benchmark salarial en curso.
**Dónde editar:** `slide-header > span.title` (línea ~530)

---

## Progreso

| Sección | Slides con action title | Total slides de contenido |
|---------|------------------------|--------------------------|
| S1 Inicio | 4 / 4 ✅ | 4 |
| S2 Discussion | 3 / 3 ✅ | 3 |
| S3 ARR Walk | 7 / 7 ✅ | 7 |
| S4 Financial | 6 / 6 ✅ | 6 |
| S5 GTM | 4 / 4 ✅ | 4 |
| S7 Headcount | 2 / 2 ✅ | 2 |
| **Total** | **26 / 26** | **26** |
