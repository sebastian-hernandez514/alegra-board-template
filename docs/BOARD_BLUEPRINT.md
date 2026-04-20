# Board Blueprint — Alegra Executive Dashboard

Fuente de verdad del contenido y estructura de cada slide. Para cada sección se documenta: qué pregunta responde al board, qué componentes visuales tiene, qué datos muestra, y cuál es la narrativa esperada.

---

## Principios de storytelling

1. **Pregunta antes que datos** — Cada slide debe responder una pregunta concreta del board.
2. **Máximo 1 insight accionable por slide** — El insight box lleva la conclusión, no la descripción.
3. **Core / Lite siempre separados** — El board necesita ver los dos productos de forma diferenciada.
4. **Tendencia antes que punto** — Mostrar siempre el contexto histórico (MoM, YoY, sparkline).
5. **Riesgo explícito** — Si hay algo que puede salir mal, decirlo directamente en el board.

---

## Sección 1 — Inicio de presentación
**Archivo:** `slides/1_inicio.html`
**Cadencia:** Mensual y Q (sin diferencia estructural)

---

### Slide 1 · Cover
**Pregunta:** ¿De qué período es esta presentación?
**Componentes:**
- Fondo navy completo
- Logo Alegra (texto)
- Título: "Board Meeting"
- Período: "{{Month}} {{Year}}"
- Subtítulo: "Confidential · Executive Review"

**Nota:** Única slide con fondo navy completo. Todas las demás tienen fondo blanco.

---

### Slide 2 · CEO Highlights & Lowlights
**Pregunta:** ¿Cuáles son las 3 cosas más importantes del mes — positivas y negativas?
**Componentes:**
- 2 columnas: Highlights (verde) | Lowlights (rojo)
- 3 bullets por columna máximo
- Sin gráficas — solo texto ejecutivo

**Narrativa esperada:** El CEO preselecciona. No es un resumen automático, es editorial.

**Formato de bullet:**
```
[Métrica en negrita]: contexto breve. Implicación o acción.
```

---

### Slide 3 · Table of Contents
**Pregunta:** ¿Qué vamos a revisar hoy?
**Componentes:**
- Lista numerada en 2 columnas
- Teal numbers, texto plano
- Separador vertical entre columnas

**Secciones listadas:** Discussion Topics | ARR Walk | Financial Performance | Go to Market | R&D | Headcount

---

### Slide 4 · Monthly Performance
**Pregunta:** ¿Cómo cerró el negocio en el mes?
**Componentes (3 niveles de métricas):**
- **Primary row** (tamaño grande): ARR total · New MRR · New Logos
- **Secondary row** (tamaño medio): Net Revenue · Gross Margin · EBITDA Margin
- **Tertiary row** (compacta): Logo Churn · Payback
- Headline pill navy con label del período
- Insight box azul navy al pie

**Tema visual:** navy (`#0f172b`) · CSS prefix `.ks-`

---

### Slide 5 · YTD Performance
**Pregunta:** ¿Cómo vamos versus el plan en lo que va del año?
**Componentes:**
- Misma estructura 3 niveles que Monthly Performance
- Badge "On track vs plan" en header
- Fila adicional en tertiary: SMB Logos EoP · Accountant Logos EoP
- Insight box verde

**Tema visual:** verde (`#1D9E75`) · CSS prefix `.ks-` (compartido con slide 4)

---

## Sección 2 — Discussion Topic
**Archivo:** `slides/2_discussion_topic.html`
**Cadencia:** Ad-hoc — el contenido cambia cada período según agenda del board

---

### Estructura estándar de cada tema (2 slides por tema)

**Slide A · Section Divider (navy)**
- Eyebrow: "Discussion · 0X"
- Título del tema
- Período

**Slide B · Contenido**
- Header navy con título
- 2-col grid: Contexto | Propuesta / Análisis
- "Ask to the Board" — 2-3 chips con preguntas específicas

**Temas actuales (Feb 2026):**
1. GTM Strategy for Accountants — modelo free + revenue share
2. Product Benchmark — Alegra MX vs Contalink
3. AI in Product — estado actual y roadmap agentes

**Nota:** Esta sección se reemplaza completamente cada período. Los temas no son acumulativos.

---

## Sección 3 — ARR Walk
**Archivo:** `slides/3_arr_walk.html`
**Cadencia:** ⭐ En meses Q (mar, jun, sep, dic) mostrar acumulado trimestral además del mes

---

### Slide 1 · Section Cover (navy)

---

### Slides 2–4 · ARR Walk Core / Lite / Alanube
**Pregunta:** ¿Cómo evolucionó el ARR de inicio a fin del período?
**Estado:** ⚠️ Pending Redesign (banner amarillo activo)

**Componentes actuales:**
- Tabla waterfall: Inicio de período → New → Expansion Upsell → Expansion Cross → Contraction Down → Contraction Cross → Churn → Reactivaciones → Fin de período
- 4 KPI mini cards: ARR EoP | New ARR | Net Churn | Net New ARR

**Eventos del waterfall (orden de fila en la tabla):**
```
Inicio de período (BoP)
+ New
+ Expansion Upsell
+ Expansion Cross Selling
− Contraction Downsell
− Contraction Cross Selling
− Churn
+ Reactivaciones / Recuperados
= Fin de período (EoP)
```

**⚠️ Diseño pendiente:** El waterfall está en formato tabla. Pendiente rediseño a barras de cascada visuales.

---

### Slides 5–8 · Country Performance (CO, MX, DR, CR)
**Pregunta:** ¿Cómo está cada país en ARR, logos y métricas de adquisición?
**Cadencia:** Siempre mensual (no se agrega por Q)

**Layout: Butterfly (rediseñado Apr 2026)**

**Componentes (por país):**
- Header navy con bandera + nombre del país
- **Summary cards:** Core ARR (valor, MoM, YoY) | Lite ARR (valor, MoM, YoY)
- **Tabla butterfly:** métrica centrada, Core espejado a la izquierda, Lite a la derecha
  - Core side: [sparkline] [YoY] [MoM] [Value]
  - Centro: nombre de métrica (fondo navy claro)
  - Lite side: [Value] [MoM] [YoY] [sparkline]

**Métricas en tabla butterfly (9 filas):**
| # | Métrica | Descripción |
|---|---------|-------------|
| 1 | Investment | S&M spend mensual |
| 2 | Net New ARR | New + Expansion − Contraction − Churn |
| 3 | Total Logos Growth | Logos EoP − Logos BoP |
| 4 | New Logos | logos con event_logo IN ('NEW','REACTIVATED') |
| 5 | New ARR | ARR de logos nuevos |
| 6 | ARPA | ARR / logos activos |
| 7 | CAC | Investment / New Logos |
| 8 | Churn | Logos perdidos (event_logo = 'CHURN') |
| 9 | Payback | CAC / (ARPA × margen) |

**Sparklines (SVG barras):**
- 5 barras `<rect>` con `rx="1"`, viewBox="0 0 80 16"
- Patrones: RISE (barras crecientes) · FALL (decrecientes) · FLAT (estables)
- Core: `#534AB7` · Lite: `#1D9E75` · negativo: `#D85A30`

**Colores de delta:**
- `.bf-pos` = `#1D9E75` (mejora respecto a período anterior — lógica de negocio, no signo)
- `.bf-neg` = `#D85A30` (deterioro — ej. churn que sube = negativo aunque el % sea positivo)

---

## Sección 4 — Financial Performance
**Archivo:** `slides/4_financial_performance.html` ⏳ PENDIENTE
**Cadencia:** ⭐ En Q, mostrar acumulado trimestral vs budget trimestral

**Slides planeados:**
- Slide 1: Section cover
- Slide 2: P&L Insights — Revenue vs Budget, Gross Margin, EBITDA
- Slide 3+: Country drilldown financiero

### Slide 2 · Product Performance ✅
**Pregunta:** ¿Cuál es el estado de salud de cada producto — creciendo, estable o en riesgo?
**Componentes:**
- KPI strip: Total subs | Total logos (con delta 6 meses)
- Grid 4 columnas — una card por producto (Accounting, Payroll, POS, Invoicing)
  - Accent bar de color (verde = growing, rojo = at risk, gris = stable)
  - Status tag, suscribers, delta 6 meses, sparkline 6 meses, churn %, avg ticket
- Signal boxes 2 columnas: "Where to focus" | "Risks requiring a decision"
- Fondo con grid sutil (pattern CSS)

**Paleta propia de esta slide:**
- `#1D9E75` growing | `#D85A30` at risk | `#888780` stable | `#1A1A18` ink

### Slide 3 · [Pendiente] ⏳
Contenido por definir. Placeholder activo.

---

## Sección 5 — Go to Market
**Archivo:** `slides/5_go_to_market.html`
**Cadencia:** Mensual (pendiente definir qué se agrega en Q)

---

### Slide 1 · Section Cover (navy)

---

### Slide 2 · New Logos
**Pregunta:** ¿Cuántos logos nuevos adquirimos este mes y qué invertimos?
**Componentes:**
- 2 stat cards: Core (count, MoM, YoY) | Lite (count, MoM, YoY)
- 2 stacked bar charts: últimos 13 meses, apilado por país (CO, MX, DR, CR)
- 2 tablas S&M: desglose People / Paid Media / Other vs período anterior y año anterior
- Insight box: read de Core y Lite

**Métricas mostradas:**
- New Logos: count de logos nuevos del período (NEW + REACTIVATED)
- S&M: desglose People / Paid Media / Other vs período anterior y año anterior

---

### Slide 3 · Summary Customer Acquisition
**Pregunta:** ¿Qué canal está dominando la adquisición y cuál es el riesgo de concentración?
**Componentes:**
- 3 stat blocks izquierda: % Paid Media Lite | % Team Core | % concentración top-2
- Line chart: tendencia de Paid Media % (Lite y Core) + Team Core — 13 meses
- "Para el board" annotation: pregunta accionable

**Narrativa:** Paid Media en Lite llegó a 57% (máximo histórico). Concentración de canal = riesgo.

---

### Slide 4 · Acquisition Funnel: Signups → Logo
**Pregunta:** ¿Cuál es la tasa de conversión de signup a logo en cada país?
**Componentes (por país — grid 2×2):**
- Nombre del país + insight de tendencia
- KPI strip: CVR último mes | CVR promedio | Signups | Logos
- Line chart: CVR % histórico con average line
- Bar chart: volumen mensual (logos convertidos vs no convertidos apilados)

**Métricas mostradas:**
- CVR % mensual: logos convertidos / signups totales × 100
- CVR promedio del período (línea punteada de referencia)
- Volumen mensual: signups totales apilados (convertidos vs no convertidos)

---

### Slide 5 · Accountant Flywheel
**Pregunta:** ¿Está creciendo el ecosistema de contadores o están abandonando la plataforma?
**Componentes:**
- Alert pill: gap actual (New Adds − Net Churn)
- SVG line chart: New Adds vs Net Churn, con área de gap rellena (teal)
- SVG bar chart: Stock Entities acumulado — base total de contadores
- 3 insight cards: Insight | Riesgo | Acción

**Narrativa:** Gap cayó a +68 (mínimo del período). Churn acelerado = señal de alarma.

---

### Slide 6 · Accountant Flywheel (cont.)
**Estado:** ⏳ Placeholder — contenido pendiente de definición con el responsable del área.

---

## Sección 6 — R&D
**Archivo:** `slides/6_rd.html` ⏳ PENDIENTE
**Cadencia:** Mensual

**Slides planeados (inferidos del PDF de referencia):**
- Slide 1: Section cover
- Slide 2: Investment en R&D — headcount técnico, capex vs opex
- Slide 3: Roadmap progress — milestones del trimestre, % completado
- Slide 4: KPIs de producto — features shipped, bugs críticos, uptime

**⚠️ Requiere input del usuario:** Estructura exacta, métricas de ingeniería relevantes para el board.

---

## Sección 7 — Headcount Summary
**Archivo:** `slides/7_headcount.html` ✅ Completo
**Cadencia:** Mensual

### Slide 1 · Section Cover (navy)

### Slide 2 · Headcount by Team
**Pregunta:** ¿Cuánta gente tiene cada equipo y cómo evolucionó?
**Componentes:**
- KPI strip (5 cards): Total HC · Engineering · Sales · Marketing · Operations
- Tabla por equipo: sparkline · HC actual · attainment bar vs plan · delta
- Insight cards + note bar al pie
- CSS prefix `.hc-` · DM Sans/Mono

### Slide 3 · People & Talent
**Pregunta:** ¿Qué tan sana es la organización en cultura, talento y riesgo?
**Componentes:**
- 2 charts: Hires / Attrition / HC EoP (barras + línea) · Attrition% / Turnover (línea)
- Bullets grid 360°: eNPS, compensación, cultura, riesgos, key hires
- CSS prefix `.pt-`

---

## Sección 8 — Appendix
**Archivo:** `slides/8_appendix.html` ⏳ PENDIENTE
**Cadencia:** Mensual

**Contenido típico:**
- Tablas de detalle que respaldan slides anteriores
- Métricas por cohort
- Datos históricos extendidos

**⚠️ Requiere input del usuario:** Qué tablas de detalle necesita el board tener disponibles.

---

## Componentes visuales reutilizables

### Hero Section (Country Performance)
```
Grid: [spacer 1.2fr] [Core 2.67fr] [divider 0.5px] [Lite 2.67fr]
Contenido por segmento: valor ARR | label | MoM | YoY | sparkline SVG
```

### Strip Table (métricas por país)
```
Group headers (Core | Lite) en misma proporción que hero
Filas de métrica: nombre | valores Core (3 períodos) | divider | valores Lite (3 períodos)
Bar sparklines: div flex con .b.c / .b.l / .b.w + .hi para valor actual
```

### Insight Box estándar
```
Fondo gris claro | padding 12px 18px
Label "KEY READ" izquierda, separador vertical, texto de insight derecha
```

### KPI Card estándar
```
Borde 0.5px | border-radius 10px | padding 14px 18px
Dot de color (Core/Lite) | label segmento | valor grande | MoM | YoY
```
