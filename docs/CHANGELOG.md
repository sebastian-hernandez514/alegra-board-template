# Changelog — Alegra Board Template

Historial de cambios por sección. El formato es: qué se construyó, qué se cambió y por qué.

---

## Abril 2026

### Headcount slides 2 & 3 rediseñados desde html_prueba (17 Apr — sesión cierre)

**Archivos modificados:** `templates/7_headcount.j2`
**Regenerado:** `output/7_headcount.html` + `output/board_standalone.html`

**Cambios:**

#### Slide 2 — Headcount Summary (nuevo diseño desde `html_prueba/Headcount Summary Alegra.html`)
- Reemplazado completamente el body del slide 2 (el viejo diseño usaba KPI strip + team grid con sparklines + barras de attainment)
- **Nuevo layout:** tabla `.hcs-tbl` (13 columnas) a la izquierda + sidebar de 4 KPI cards a la derecha (`grid 1fr 208px`)
- **Tabla:** 4 categorías P&L (Cost of Revenue · Customer Acquisition Costs · Product & Development · G&A) con sub-equipos. Columnas teal highlight: Closing, Share, MoM%, YoY%, Var HC vs LY. Columnas Forecast: Fcst 26, Actual vs Fcst, % Pred. Columna Interns.
- **KPI cards:** Total HC 505 (+8 interns) · New Hires 7 · Total Attrition 20 · Staff Turnover 3.84
- **Comments bar** al pie en grid 3 columnas (label | Highlights | Lowlights) con fondo `#F8FAFC`, borde `#CBD5E1` para mayor visibilidad
- CSS prefix: `.hcs-*` (headcount summary) — sin colisión con `.hc-*` existentes

#### Slide 3 — People & Talent (nuevo diseño desde `html_prueba/People Talent Alegra.html`)
- Reemplazado el body del slide 3 (el viejo usaba un combo bar+line único + bullets editoriales)
- **Nuevo layout:** 2 chart cards lado a lado (`.pt2-card`, `grid 1fr 1fr`)
  - **Card izquierda:** panel superior = líneas New Hires (teal) + Attrition (rose); panel inferior = barras People EoP (dark)
  - **Card derecha:** panel superior = línea Staff Turnover Rate (rose); panel inferior = barras Attrition % (dark)
- **13 meses de datos** hardcodeados (Mar'25 → Mar'26): newHires, attrition, peopleEoP, turnover, attrPct
- **Labels automáticos** en los últimos 3 puntos (Jan, Feb, Mar) dibujados con `afterDatasetsDraw`
- **Comments** al pie (teal, estilo consistente con slide 2)
- CSS prefix: `.pt2-*` — sin colisión con `.pt-*` existentes del diseño anterior
- Script refactorizado con IIFE `(function(){...})()` para evitar contaminación de scope con el resto de charts
- Datos de Slide 2 sparklines (`hc.teams`, `hc.spark_labels`) mantenidos intactos en el mismo `<script>` block

---

### Board full English + H&L layout + limpieza template 4 (17 Apr — sesión final)

**Archivos modificados:** `templates/1_inicio.j2`, `templates/2_discussion_topic.j2`, `templates/3_arr_walk.j2`, `templates/4_financial_performance.j2`, `templates/5_go_to_market.j2`, `templates/6_rd.j2`, `templates/7_headcount.j2`, `scripts/merge_standalone.py`
**Regenerado:** todos los outputs + `output/board_standalone.html`

**Cambios:**

#### Slide 2 de `1_inicio.j2` — nuevo layout H&L para muchos items
- Rediseño del slide CEO Highlights & Lowlights para soportar 8 highlights + 4 lowlights sin overflow
- Nuevo layout `.hl-outer-grid` (`3fr 2fr`): Highlights ocupa 60% del ancho, Lowlights el 40%
- Highlights internamente divididos en 2 sub-columnas (`.hl-items-2col`) — 4 items por columna
- Nuevo componente `.hl-item-sm` con font-size 9.5px y line-height 1.42 para ajuste compacto
- Contenido H&L de Q1 2026 cargado en `data/editorial/ceo.yaml` (8 highlights, 4 lowlights)

#### Traducción completa a inglés — todos los templates
Todos los textos visibles en los templates traducidos al inglés. **Excepción: highlights y lowlights** (contenido editorial, no se tocan).
- `lang="es"` → `lang="en"` en los 7 templates + `merge_standalone.py`
- `1_inicio.j2`: `Crecimiento` → Growth · `Desempeño financiero` → Financial Performance · `Riesgo y sostenibilidad` → Risk & Sustainability · `Base de clientes` → Customer Base · `pp sobre presupuesto` → pp above budget · `prom` → avg · `Fuente:` → Source · título slide 6 · `Valor`/`Métrica` → Value/Metric
- `3_arr_walk.j2`: `Comentarios` → Comments · `Fuente:` → Source · 2 comentarios Alanube hardcodeados · `Valor`/`Métrica`
- `4_financial_performance.j2`: todos los `Fuente:` → Source · `Ingresos` → Revenue · `Cierres` → Closings · `Cierre Mar` → Mar Close · textos narrativos del Cash Flow
- `5_go_to_market.j2`: `Comentarios` → Comments · textos de placeholder
- `6_rd.j2`: `Churn por producto` → by Product · `Fuente:` → Source · placeholders
- `7_headcount.j2`: `Equipo` → Team

#### `merge_standalone.py` — template 6 añadido
- `6_rd.html` incluido en el orden de merge (antes faltaba)
- `lang="es"` → `lang="en"` en el HTML generado

#### `3_arr_walk.j2` — panel de comentarios eliminado del slide Alanube
- Removido el bloque `.aw-comments-panel` completo del slide 4 (Alanube)
- `padding` del wrapper ajustado a `32px` para que la tabla ocupe todo el ancho

#### `4_financial_performance.j2` — limpieza de insight boxes y traducción
- **Eliminados** insight boxes de slides 2 (`.fp-insight-blue`), 3 (`.fp-insight-green`) y 5 (`.fp-insight-blue`)
- **Traducidos** headers de todos los slides: slides 2, 3, 4, 6, 7 estaban en español
- **Traducidos** 4 insight boxes restantes (slides 4 y 6/7) al inglés

---

### Slide 2 (New Logos) de 5_go_to_market — rediseño y fixes (16 Apr — sesión 4)

**Archivos modificados:** `templates/5_go_to_market.j2`
**Regenerado:** `output/5_go_to_market.html` via `generate.py --template 5_go_to_market`

**Cambios:**
- **Escala compartida en charts:** ambas gráficas (Core y Lite) usan el mismo `sharedLogoMax` calculado del máximo de todos los datos (4 países × 2 segmentos). Antes cada chart escalaba independientemente, lo que distorsionaba la comparación visual.
- **Leyenda de países activada:** `legend: { display: true, position: 'bottom' }` en `mkChart`. Antes estaba oculta y los colores (Colombia, México, Rep. Dom., Costa Rica) eran ilegibles.
- **Stat cards más compactas:** MoM y YoY movidos a la derecha de la card (layout flex row). El número principal queda a la izquierda junto al label del segmento. Font-size reducido de 32px a 26px, padding reducido.
- **Sección de comentarios:** añadido bloque `.nl-comments` al pie del slide (min-height 64px, bordeado) alimentado por `editorial.gtm_new_logos_comments`.
- **Eliminadas tablas S&M:** las tablas de desglose de inversión por componente (People/Paid/Other) se removieron del slide 2 — ya tienen su propio slide 3.
- **Eliminado "Ask to the Board"** del slide 2 — recupera espacio vertical.
- **Eliminado "Key Read"** — el bloque `insight-gtm` fue removido para simplificar el slide.

---

### Slide 3 (Summary Customer Acquisition) de 5_go_to_market — construcción completa (16 Apr — sesión 4)

**Archivos modificados:** `scripts/fetch_metrics.py`, `templates/5_go_to_market.j2`
**Regenerado:** `output/5_go_to_market.html` via `fetch_metrics.py` + `generate.py --template 5_go_to_market`

**Cambios:**
- **Query de inversión expandido:** `_SQL_INVESTMENT` ahora retorna `paid_media_usd`, `people_usd`, `other_usd` además del total. `CACHE_VERSION` bumped a `v7-board-metrics`.
- **Nuevas series en metrics.yaml:** `sm_core_paid_series`, `sm_core_people_series`, `sm_core_other_series` (y equivalentes Lite) — 13 meses, absolutas en USD.
- **Layout dos columnas Core | Lite:** cada columna tiene una KPI card arriba (total de inversión del mes + MoM pill + desglose mix) y un line chart abajo con las 3 líneas (People, Paid Media, Other).
- **Escala compartida entre Core y Lite:** `sharedMax` y `sharedMin` calculados del máximo/mínimo de los 6 datasets combinados.
- **Gráfico de líneas** (`type: 'line'`), tension 0.4, sin fill, con hover points.
- **Altura fija del slide:** `.gtm-slide` tiene `height: var(--slide-height); overflow: hidden` — aplica a todos los slides del template.

---

### Alanube slide (slide 4 de 3_arr_walk) — pulido de columnas YTD (16 Apr — sesión 3)

**Archivos modificados:** `templates/3_arr_walk.j2`
**Regenerado:** `output/3_arr_walk.html` via `generate.py --template 3_arr_walk`

**Cambios:**
- Eliminada columna **YTD'24** de todas las filas de datos (19 filas) — era redundante sin contexto adicional.
- Segundo separador entre el bloque de quarters y el bloque YTD cambiado de `al-sp-col` (6px vacío) a `al-sp-sm` (3px con borde izquierdo sutil `#e2e8f0`) — separa visualmente sin ocupar espacio innecesario.
- Eliminado el primer `YTD Δ%` (que comparaba YTD'25 vs YTD'24, ya sin sentido tras quitar YTD'24). Conservado solo el `YTD Δ%` de la derecha que compara **YTD'26 vs YTD'25**.
- `colspan` de filas de sección/gap/gap actualizados: `13→12` (quarter_end) y `14→13` (monthly).

---

### Alanube slide (slide 4 de 3_arr_walk) — diseño y columnas dinámicas (16 Apr — sesión 3)

**Archivos modificados:** `templates/3_arr_walk.j2`
**Regenerado:** `output/3_arr_walk.html` via `generate.py --template 3_arr_walk`

**Cambios:**
- Slide 4 (Alanube): contenido reemplazado completamente con datos de `html_prueba/arr_walk_alanube.html`.
- Adaptado al sistema de diseño `.aw-sum-table` (igual que Core/Lite): clases `.aw-rb`, `.aw-in`, `.aw-sh`, `.aw-gap`, `.aw-nv`, `.aw-di`, `.aw-comments-panel`.
- Extensiones CSS exclusivas de Alanube (`.al-*`):
  - `.al-cur` → highlight teal (`rgba(48,184,183,…)`) para columnas del período activo (Jan/Feb o 1Q26).
  - `.al-sp-col` → separador ancho (6px) entre quarters históricos y período activo.
  - `.al-sp-sm` → separador delgado (3px + borde) entre período activo y YTD.
  - `.al-tb` → borde superior en filas EoP (Logo EoP, ARR EoP).
- **Columnas dinámicas** según `metrics.is_quarter_end`:
  - `True` (cierre de Q): muestra `1Q26` + `QoQ%` (1 columna activa).
  - `False` (mes): muestra `Jan-26` + `Feb-26` + `MoM A%` (2 columnas activas).
  - Label "ARR Growth Rate" también cambia entre QoQ y MoM.
- Panel de comentarios `.aw-comments-panel` a la derecha (igual que Core/Lite).
- 3 secciones: **Logo Walk** · **ARR Walk (MM USD)** · **Finance Metrics** · **Operation Metrics**.

---

### Slides 2-3 de 3_arr_walk — panel de comentarios (16 Apr — sesión 3)

**Archivos modificados:** `templates/3_arr_walk.j2`
**Regenerado:** `output/3_arr_walk.html` via `generate.py --template 3_arr_walk`

**Cambios:**
- Añadido `.aw-comments-panel` (width: 220px, fondo `#f1f5f9`, borde radius 10px) a la derecha de la tabla en slides Core y Lite.
- Layout `.aw-body-row` (flex row) conteniendo `.aw-sum-wrap` (flex:1) + `.aw-comments-panel`.
- Panel muestra 4 slots de comentarios vacíos — listos para ser llenados en `data/editorial/`.

---

### ARR Walk por segmento (Core/Lite) en slides 2-3 de 3_arr_walk (16 Apr — sesión 2)

**Archivos modificados:** `scripts/fetch_metrics.py`, `templates/3_arr_walk.j2`
**Regenerado:** `output/3_arr_walk.html` via `fetch_metrics.py --month 2026-03` + `generate.py --template 3_arr_walk`

**Cambios en `fetch_metrics.py`:**
- Loop post-`arr_walk_table` que itera `out["arr_walk_products"]` y agrega `arr_walk_table` a cada producto usando `seg_metrics.get(seg).get("quarters")` — datos filtrados por segmento.
- Misma estructura de secciones/filas que el global. Helper `_sqraw(key, _sq, _s5)` con default args para evitar closure issues en el loop.

**Cambios en `templates/3_arr_walk.j2`:**
- CSS `.aw-sum-*` copiado (mismo sistema que `1_inicio.j2` slide 6) — prefijos `.aw-rb`, `.aw-in`, `.aw-rt`, `.aw-sh`, `.aw-gap`, `.awdp-b/o/n`, `.aw-di-*`.
- Slides 2-3 (loop `{% for product in metrics.arr_walk_products %}`): reemplazado hero band + chart por tabla `aw-sum-table` referenciando `product.arr_walk_table`.
- Se mantienen: slide-header con action title + badge de color por segmento, slide-footer con fuente.
- Guard `{% if product.arr_walk_table %}` por si un segmento no tiene datos.

**⚠️ Pendiente:** Validar números cuando vuelva `fact_customers_mrr`.

---

### ARR Walk Summary — diseño completo alineado a arrwalk_v2.html (16 Apr — sesión 2)

**Archivos modificados:** `scripts/fetch_metrics.py`, `templates/1_inicio.j2`
**Regenerado:** `output/1_inicio.html` via `fetch_metrics.py --month 2026-03` + `generate.py --template 1_inicio`

**Cambios en `fetch_metrics.py`:**
- Reescritura completa del bloque `arr_walk_table` (antes: `logo_rows` + `arr_rows` planos, ahora: `sections` con filas enriquecidas).
- Nueva estructura por fila: `label`, `type`, `dot`, `cells[5]`, `qoq`, `qoq_good`, `yoy`, `yoy_good`, `ytd_prev`, `ytd_cur`, `nv`.
- Helpers añadidos: `_pill_pct`, `_pill_pp`, `_aw_row`, `_aw_na_row`, `_qraw`.
- Nuevas métricas calculadas: **Logo Monthly New Adds %** (`l_new / (3 * l_bop)`), **Net Expansion** (`a_upsell + a_down`), **Net Churn/Expansion %** (`(a_churn + net_exp) / a_bop`).
- **Logo Monthly Churn %** toma de `l_churn_pct` (tasa mensual promedio ya calculada por el query RS).
- Sección **SaaS Metrics** añadida con S&M Spend, CAC Payback, FX COP/USD, FX MXN/USD en `N/A` (fuente pendiente).
- Campo `ytd_labels` añadido al dict raíz (`[_last5q[0], _last5q[-1]]`).

**Cambios en `templates/1_inicio.j2`:**
- Slide 6: loop cambiado de `logo_rows`/`arr_rows` a `sections → rows`.
- Header de tabla: añadidas columnas **QoQ**, **YoY**, **YTD'25**, **YTD'26** (10 columnas total).
- Pills de delta con lógica `is sameas true/false` para distinguir `None` (neutral) de `False` (negativo).
- CSS añadido: `.aw-sum-table thead th.aw-ytd` y `td.aw-ytd`.
- `colspan` de filas `aw-gap` actualizado a 10.

**⚠️ Pendiente — validación de números:**
- `dwh_facts.fact_customers_mrr` está **vacía** (detectado 16 Apr). Los valores del slide usan cache RS del 15 Apr pero no han sido validados contra datos reales de Mar 2026.
- Cuando vuelva la fact table: correr `fetch_metrics.py --month 2026-03 --refresh` y validar totales vs fuente.
- Valores en N/A que requieren fuente: S&M Spend (quarterly), CAC Payback (histórico por quarter), FX COP/USD, FX MXN/USD.

---

### ARR Walk Summary rediseñado — nuevo formato tabla 5-quarter (16 Apr)

**Archivos modificados:** `templates/1_inicio.j2`, `slides/1_inicio.html`
**Regenerado:** `output/1_inicio.html` via `generate.py --template 1_inicio`

**Cambios:**
- **CSS:** Reemplazado sistema `.awt-*` por `.aw-sum-*`. Nueva paleta colorblind-safe: azul (`#185FA5`) para positivo, naranja (`#E87722`) para negativo.
- **Layout:** De dos paneles separados (Logo Walk | ARR Walk USD) a una sola tabla unificada con secciones (Logo Walk / ARR Walk Spot) y columnas QoQ/YoY (muestran `—` hasta que `fetch_metrics.py` las compute).
- **Action title:** Header del slide ahora declara el insight: *"Net New ARR global se comprime a $0.2M — adiciones + recuperaciones cubren solo el 79% del churn en 1Q26"*
- **Headline bar:** Caja navy `#0f172b` con resumen del período encima de la tabla.
- **Datos:** Siguen viniendo de `metrics.arr_walk_table` (Redshift). Los loops Jinja2 se mantienen; solo cambia el CSS y la estructura HTML.
- **Slide 7 (Global Country Performance):** Añadido a `slides/1_inicio.html` — ya existía en `output/` pero faltaba en `slides/`.

**Regla aprendida:** Los cambios de diseño van en `templates/*.j2`, no en `slides/*.html`. Después de editar el template, siempre correr:
```bash
uv run --with jinja2 --with pyyaml python3 scripts/generate.py --template 1_inicio
```
El output de `slides/` es solo referencia estática — el que el usuario abre es `output/`.

**Pendiente (para siguiente sesión):**
- Agregar columnas QoQ/YoY reales en `fetch_metrics.py` → `arr_walk_table`
- SaaS Metrics section (S&M, CAC Payback, FX rates) como tercera sección de la tabla

---

### Pipeline y lógica de Q corregida (15 Apr)

**`scripts/fetch_metrics.py` — 4 correcciones:**

1. **Flag `--csv-only`**: re-corre solo los merges de CSV (Budget, P&L, Payback) sin tocar Redshift. Útil cuando se actualiza un CSV sin datos nuevos de RS.

2. **Bug Payback**: `merge_payback()` buscaba fecha en formato `M/1/YYYY` pero el CSV usa `YYYY-MM`. Siempre quedaba N/A. Corregido.

3. **New Logos / New MRR en cierre de Q**: `new_logos` y `new_mrr` (valor principal del slide) ahora muestran la **suma de los 3 meses del Q** cuando `is_quarter_end=True`. Antes mostraban solo el mes de cierre.

4. **vs Budget en cierre de Q**: `merge_budget()` ahora suma el budget de los 3 meses del Q para comparar contra el real acumulado. Antes comparaba el real del Q contra el budget de un solo mes (generaba +176% falsos).

5. **Fórmula de churn corregida** (validada con Jhon Gallego — Retention):
   - Antes: `l_nc_pct = nc_l / avg(BoP, EoP)` — denominador incorrecto
   - Ahora: `(logos_churn - logos_react) / BoP` por mes, promedio de los 3 meses en cierre de Q
   - Aplica a `logo_churn_core` y `logo_churn_global`

---

### N-1 parcial — Action titles aplicados en S1 (10 Apr)
**4 action titles implementados en `1_inicio.html`:**
- Slide 2: "Crecemos en ARR, pero churn elevado y EBITDA bajo plan exigen decisión en {{Month}}"
- Slide 4 (ks-headline): "ARR $27.4M, +39% YoY y +6% vs plan — Logo Churn en 3.5% (0.8pp sobre presupuesto) comprime el crecimiento neto"
- Slide 5 (ks-headline): "ARR 6% sobre plan y +39% YoY — el crecimiento es de ARPA, no de volumen: new logos −9% YoY"
- Slide 6: "Net New ARR colapsó a $0.2M en 1Q26 — churn +47% YoY absorbe el 89% de las nuevas adiciones"

**Slide 4 también resuelve N-2:** la señal de churn ahora lidera el headline.

**Creado `docs/NARRATIVE.md`** — guión editorial con action title, insight declarado y línea HTML a editar para cada slide. Progreso: 4/21 slides.

---

### Quick wins del backlog aplicados (10 Apr)
**4 mejoras implementadas del IMPROVEMENT_BACKLOG.md:**
- **V-1 (🔴 CRÍTICO):** Eliminado doble eje Y de todos los charts ARR Walk (`3_arr_walk.html` slides 2–3, `1_inicio.html` slide 6). Net New ARR ahora aparece como anotaciones de texto sobre el área del chart (usando `afterDraw`). Elimina las correlaciones visuales falsas señaladas por Few.
- **C-1 (🟠 ALTO):** Paleta colorblind-safe aplicada en todos los archivos. Rojo (#E24B4A, #dc2626, #FF7A7A) reemplazado por naranja (#DD6B20, #C2410C, #FB923C) en barras, badges y tokens de `base.css`. `7_headcount.html` actualizado también.
- **CT-1 (🟠 ALTO):** Fuente de datos añadida al footer de todos los slides con métricas: `Fuente: Redshift · fact_customers_mrr · {{Month}} {{Year}}`. CSS `.footer-source` añadido a `base.css`.
- **CL-1 (🟡 MEDIO):** `@media print { .slide-divider { display: none; } }` añadido a `base.css`. Los dividers de navegación se ocultan en exportación PDF.

---

### DataViz Review completada (10 Apr)
Revisión experta del template completo usando framework Knaflic/Tufte/Few/Cairo.
- Veredicto: **ADEQUATE** — funciona como reporte de estado, falla como herramienta de decisión
- Backlog generado en `docs/IMPROVEMENT_BACKLOG.md` — 27 mejoras clasificadas por importancia
- **2 críticos:** action titles en todos los slides (N-1), eliminar doble eje Y del ARR Walk (V-1)
- **Quick wins identificados:** CT-1 (fuente de datos), C-1 (paleta colorblind-safe), CL-1 (ocultar dividers en print)

---

### v0.9 — Butterfly layout + bar sparklines (10 Apr)
**Country Performance rediseñado.**
- Slides 5–8 de `3_arr_walk.html`: nuevo layout butterfly para los 4 países (CO, MX, DR, CR)
  - Summary cards arriba: Core ARR | Lite ARR con MoM/YoY
  - Tabla butterfly: nombre de métrica centrado, Core espejado a la izquierda (YoY · MoM · Value · spark), Lite a la derecha (spark · Value · MoM · YoY)
  - 9 métricas: Investment, Net New ARR, Total Logos Growth, New Logos, New ARR, ARPA, CAC, Churn, Payback
  - CSS prefix `.bf-` para aislamiento total
- Sparklines convertidas de `<polyline>` a barras SVG (`<rect>`, 5 barras, `rx="1"`)
  - 3 patrones: RISE (barras crecientes), FALL (decrecientes), FLAT (estables)
  - Colores: Core `#534AB7` · Lite `#1D9E75` · negativo `#D85A30`
- Script `scripts/rebuild_country_slides.py` — reconstruyó los 4 cp-inner via Python
- Script `scripts/fix_sparklines_bars.py` — reemplazó todos los polyline con barras

**Decisiones:**
- Ancho 960px (nuestro estándar), no 1200px del ejemplo de referencia
- Insight boxes removidos de todos los Country Performance (estaban entre hero y tabla)
- ARR como métrica principal del hero (antes era Investment) — Investment se movió a la tabla como primera fila

---

### v0.8 — Monthly & YTD Performance (10 Apr)
**Slides 4 y 5 de `1_inicio.html` reemplazadas.**
- Slide 4: Monthly Performance — secciones Crecimiento (ARR, New MRR, New Logos), Desempeño financiero (Net Revenue, Gross Margin, EBITDA Margin), Riesgo y sostenibilidad (Logo Churn, Payback)
- Slide 5: YTD Performance — misma estructura con tema verde (`#1D9E75`), badge "On track vs plan", fila adicional Base de clientes (SMB Logos, Accountant Logos EoP)
- CSS prefix `.ks-` para aislamiento; DM Sans + DM Mono añadidos a los font imports de ese archivo

**Decisiones:**
- Diseño heredado de referencia del usuario (DM Sans/Mono, paleta ink/green/red propia)
- Tres niveles de métricas: primary row (grande), secondary row (media), tertiary row (compacta)

---

### v0.7 — Headcount Summary completo (09 Apr)
**Sección 7 completada.**
- Slide 1: Section cover (navy)
- Slide 2: Headcount by Team — KPI strip (5 cards), tabla por equipo con sparklines + attainment bars + insight cards + note bar
- Slide 3: People & Talent — 2 charts (hires/attrition/headcount EoP + attrition%/turnover), bullets grid (360°, eNPS, compensación, cultura, riesgos, key hires)

**Decisiones:**
- Slide 2: DM Sans/Mono, prefijo `.hc-` — mismo sistema que Financial Performance
- Slide 3: system-ui fonts (heredado del diseño del usuario), prefijo `.pt-`

---

### v0.6 — Financial Performance parcial (09 Apr)
**Sección 4 iniciada.**
- Slide 1: Section cover (navy)
- Slide 2: Product Performance — 4 product cards (Accounting, Payroll, POS, Invoicing) con sparklines, KPI strip, signal boxes "Where to focus / Risks"
- Slide 3: Placeholder — contenido pendiente de definición

**Decisiones:**
- Diseño heredado del usuario (DM Sans/Mono, paleta ink/green/red propia) — prefijo `.pp-` para aislamiento de CSS

---

### v0.5 — Go to Market completo (09 Apr)
**Sección 5 completada.**
- Slide 2: New Logos — stat cards + stacked bar charts (Core/Lite × 4 países) + S&M tables
- Slide 3: Summary Customer Acquisition — line chart Paid Media % (DM Sans/Mono)
- Slide 4: Acquisition Funnel — grid 4 países con CVR line + volume bars
- Slide 5: Accountant Flywheel — SVG charts (New Adds vs Churn + Stock) + insight cards
- Slide 6: Placeholder (Accountant Flywheel cont. — pendiente definición)

**Decisiones:**
- Slides 3-5 usan DM Sans + DM Mono heredado de los diseños del usuario — se respetó en lugar de forzar Inter
- CSS aislado por prefijo (`.acq-`, `.fml-`, `.fly-`) para evitar conflictos de nombres en el mismo HTML

---

### v0.4 — ARR Walk completo (08 Apr)
**Sección 3 completada.**
- Slide 1: Section cover
- Slides 2-4: ARR Walk Core / Lite / Alanube — tabla waterfall + 4 KPI mini cards
  - ⚠️ Marcados con banner "Pending Redesign" — waterfall en tabla, no visual de barras
- Slides 5-8: Country Performance (Colombia, México, DR, Costa Rica)
  - Hero section con alineación Core/Lite usando CSS Grid proporcional
  - Strip table con 8 métricas y bar sparklines
  - Insight box con key read + sub-nota

**Problema resuelto:** Alineación del divisor Core/Lite — el hero usaba `1fr 1fr` (divider a ~452px) pero la tabla tenía el divider a ~535px. Fix: `grid-template-columns: minmax(0,1.2fr) minmax(0,2.67fr) 0.5px minmax(0,2.67fr)` con spacer vacío, aplicado igual en `.hero` y `.gh`.

---

### v0.3 — Discussion Topic (07 Apr)
**Sección 2 completada.**
- 3 temas × 2 slides = 6 slides totales
- Tema 1: GTM Strategy for Accountants
- Tema 2: Product Benchmark MX (Alegra vs Contalink) — tabla con badges Strong/Weak/Partial
- Tema 3: AI in Product — estado actual + roadmap agentes Q2/Q3

**Estructura estándar establecida:** Section divider navy + slide de contenido con 2-col Context/Proposal + "Ask to the Board" chips.

---

### v0.2 — Inicio de presentación (06 Apr)
**Sección 1 completada.**
- Slide 1: Cover (navy completo)
- Slide 2: CEO Highlights & Lowlights (2 columnas verde/rojo)
- Slide 3: Table of Contents — **rediseñado** de grid a lista 2 columnas con números teal y separador vertical
- Slide 4: Key Summary Metrics — 8 KPI cards en grid 2×4
- Slide 5: Key Summary Metrics Core/Lite — tabla comparativa con badges

**Cambio:** TOC original era un grid de cards. Cambiado a lista numerada por preferencia del usuario (el grid no transmite jerarquía).

---

### v0.1 — Setup inicial (06 Apr)
- Definición de formato: HTML por sección, 960px, scroll vertical
- Creación de `styles/base.css` con tokens compartidos
- Definición de paleta navy/teal + sistema Core (purple) / Lite (green)
- Estructura de carpetas inicial

---

## Deuda técnica activa

| Item | Sección | Descripción |
|------|---------|-------------|
| Waterfall visual | S3 slides 2–4 | ARR Walk en tabla. Pendiente rediseño a barras de cascada visuales |
| Flywheel cont. | S5 slide 6 | Placeholder — contenido pendiente de definición |
| Financial Performance slide 3 | S4 slide 3 | Placeholder — contenido pendiente de definición |
| R&D | S6 | Archivo no creado — estructura pendiente de definición |
| Appendix | S8 | Archivo no creado — tablas de detalle pendientes de definición |
