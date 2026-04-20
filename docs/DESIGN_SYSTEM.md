# Design System — Alegra Board Presentation

Sistema de diseño del template HTML del board ejecutivo de Alegra. Documenta tokens, tipografía, componentes y decisiones de diseño tomadas.

---

## 1. Paletas de color

El template usa **dos sistemas de color** según el contexto de la slide.

### Paleta principal (base.css · secciones 1–4)

| Token CSS | Hex | Uso |
|-----------|-----|-----|
| `--color-navy` | `#0f172b` | Slide-header (nav top), cover slide, section dividers |
| `--color-bg` | `#ffffff` | Fondo de todas las slides (regla absoluta) |
| `--color-surface` | `#f8fafc` | Cards y superficies secundarias |
| `--color-border` | `#e2e8f0` | Bordes de cards y separadores |
| `--color-teal` | `#14b8a6` | Acento principal: fechas, labels, highlights |
| `--color-teal-light` | `#f0fdfa` | Fondo de insight boxes |
| `--color-positive` | `#16a34a` | Variaciones positivas ▲ |
| `--color-negative` | `#dc2626` | Variaciones negativas ▼ |
| `--color-neutral` | `#64748b` | Texto secundario, variaciones neutras — |
| `--color-text-primary` | `#0f172b` | Texto principal |
| `--color-text-secondary` | `#64748b` | Labels, texto de apoyo |

### Paleta GTM / Country (sección 3 countries + sección 5)
Usada para diferenciar los dos productos comerciales. Definida inline en cada archivo.

| Variable | Hex | Uso |
|----------|-----|-----|
| `--purple` | `#534AB7` | Core — color primario |
| `--purple-l` | `#AFA9EC` | Core — versión clara (sparklines) |
| `--green` | `#1D9E75` | Lite — color primario |
| `--teal-l` | `#9FE1CB` | Lite — versión clara (sparklines) |
| `--coral` | `#D85A30` | Valores negativos / churn / alertas |
| `--c-border` | `#e5e5e5` | Bordes internos en slides GTM |
| `--c-bg2` | `#f5f5f3` | Superficies secundarias GTM |
| `--c-dim` | `#999` | Texto terciario GTM |

**Regla:** La paleta GTM no reemplaza a la principal — coexisten. El slide-header y slide-footer siempre usan los tokens de `base.css`.

### Paleta DM Slides (slides 3 y 4 de GTM — Customer Acquisition y Funnel)
Heredada de los diseños de referencia del usuario. Solo se usa en esas dos slides.

| Variable | Hex | Uso |
|----------|-----|-----|
| Accent | `#C04828` | Paid Media · Lite, alertas |
| Blue | `#185FA5` | Paid Media · Core |
| CVR blue | `#1a3d6e` | Línea de conversión en funnel |
| Muted text | `#6b6a64` | Texto secundario |
| Tertiary | `#a09e98` | Labels de monospace |

---

## 2. Tipografía

### Familias

| Familia | Uso | Cómo cargar |
|---------|-----|-------------|
| **Inter** | Tipografía base de toda la presentación | `family=Inter:wght@400;500;600;700` |
| **DM Sans** | Slides GTM: Customer Acquisition, Funnel, Flywheel | `family=DM+Sans:wght@300;400;500` |
| **DM Mono** | Labels numéricos, monospace en slides GTM | `family=DM+Mono:wght@400;500` |

**Google Fonts link completo (slides que usan todas):**
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Escala tipográfica (Inter — secciones 1–3)

| Rol | Tamaño | Peso | Color |
|-----|--------|------|-------|
| Título de sección header | 16px | 600 | blanco |
| KPI principal | 32–40px | 700 | text-primary |
| Título de bloque | 10px | 700 | teal, uppercase, letter-spacing 1.5px |
| Body / bullets | 13px | 400 | text-secondary |
| Tabla header | 9–10px | 500–600 | dim |
| Badge / variación | 11px | 500 | positive/negative/neutral |
| Footer | 11px | 400 | neutral |

### Escala tipográfica (DM Sans/Mono — slides GTM)

| Rol | Tamaño | Familia | Peso |
|-----|--------|---------|------|
| Headline principal | 22–28px | DM Sans | 300 |
| Emphasis en headline | igual | DM Sans | 500 |
| Stat number grande | 30–36px | DM Sans | 300–400 |
| Label de stat | 10–11px | DM Mono | 400 |
| KPI value (funnel) | 16–20px | DM Sans | 500 |
| Labels de eje / tick | 9–10px | DM Mono | 400 |
| Annotation tag | 9px | DM Mono | 500 |

---

## 3. Layout

| Parámetro | Valor |
|-----------|-------|
| Ancho de slide | `960px` |
| Ratio | `16:9` (height auto — scroll vertical) |
| Navegación | Scroll dentro del mismo archivo HTML |
| Padding interno base | `var(--slide-pad-y) var(--slide-pad-x)` (definido en base.css) |
| Gap entre slides | `24px` |
| Border radius de cards | `8–12px` |
| Box shadow de slides | `0 4px 24px rgba(0,0,0,0.10)` |

**Regla absoluta de fondo:** Todas las slides van en fondo blanco `#ffffff`. El navy solo aparece en:
1. Cover slide completa (excepción por diseño de portada)
2. `.slide-header` (barra superior de navegación de cada slide)
3. Section dividers entre temas de Discussion Topic

---

## 4. Componentes construidos

### `base.css` — CSS compartido

Importar en todos los HTMLs:
```html
<link rel="stylesheet" href="../styles/base.css">
```

Contiene: `.slide`, `.slide-header`, `.slide-body`, `.slide-footer`, `.kpi-card`, `.kpi-grid`, `.insight-box`, `.data-table`, `.badge`, `.slide-divider`, cover/TOC styles.

---

### Slide Header (`.slide-header`)
```
Fondo: var(--color-navy) #0f172b
Padding: 14px var(--slide-pad-x)
Layout: flex space-between
  Izquierda: título de slide (16px, 600, blanco)
  Derecha: período (13px, 500, var(--color-teal))
```

---

### KPI Card (`.kpi-card`)
```
Fondo: blanco | Borde: 0.5px var(--color-border) | Border-radius: 8px
Padding: 20px 24px
  Label: 10px, uppercase, letter-spacing 1.5px, teal
  Valor: 32–40px, 700, text-primary
  Variaciones: 12px, con ▲▼— y color positivo/negativo/neutral
```

---

### Insight Box (`.insight-box`)
```
Fondo: var(--color-teal-light) #f0fdfa
Borde izquierdo: 3px solid var(--color-teal)
Padding: 12px 16px
Texto: 13px, text-secondary, línea 1.6
```
Versión GTM (`.insight-gtm`):
```
Fondo: var(--c-bg2) #f5f5f3
Layout: flex con label izquierda (KEY READ) + separador + texto derecha
```

---

### Data Table (`.data-table`)
```
Ancho: 100% | border-collapse: collapse
Header row: fondo navy, texto blanco, 10px
Filas: border-top 1px solid var(--color-border), 13px
Badges inline: .badge.positive / .badge.negative / .badge.neutral
```

---

### Hero Section (Country Performance)
```
CSS Grid: minmax(0,1.2fr) minmax(0,2.67fr) 0.5px minmax(0,2.67fr)
  Col 1: spacer vacío (alinea con metric label de la tabla)
  Col 2: card Core (ARR, MoM, YoY, sparkline)
  Col 3: divider vertical 0.5px
  Col 4: card Lite (ídem)
CRÍTICO: el group header (.gh) de la strip table usa EXACTAMENTE la misma proporción
para que el divisor Core/Lite quede alineado visualmente.
```

---

### Butterfly Table (Country Performance — `.bf-`)
```
Layout general por país:
  Summary cards: .bf-cards → flex row con .bf-card (Core) y .bf-card (Lite)
  Tabla: .bf-table → columnas por fila: [.bf-core] [.bf-metric] [.bf-lite]

.bf-core   → flex row-reverse: spark | YoY | MoM | Value (Core izquierda espejado)
.bf-lite   → flex row: Value | MoM | YoY | spark (Lite derecha)
.bf-metric → fondo navy claro, centrado, texto uppercase pequeño
.bf-val    → 66px, text-align right (Core) / left (Lite)
.bf-delta  → 50px, texto pequeño
.bf-spark  → 44px × 14px, contiene SVG de barras

.bf-pos    → #1D9E75 (mejora de negocio)
.bf-neg    → #D85A30 (deterioro de negocio)
.bf-head   → fila de cabecera con labels (COLOR: #bbb, 9px uppercase)
```

**SVG Bar sparklines (5 barras):**
```html
<!-- viewBox="0 0 80 16", 5 rect con rx="1" -->
<!-- RISE: alturas [5,8,10,12,14], x: 2,18,34,50,66, ancho 12 -->
<svg class="bf-spark" viewBox="0 0 80 16">
  <rect x="2"  y="11" width="12" height="5"  fill="#534AB7" rx="1"/>
  <rect x="18" y="8"  width="12" height="8"  fill="#534AB7" rx="1"/>
  <rect x="34" y="6"  width="12" height="10" fill="#534AB7" rx="1"/>
  <rect x="50" y="4"  width="12" height="12" fill="#534AB7" rx="1"/>
  <rect x="66" y="2"  width="12" height="14" fill="#534AB7" rx="1"/>
</svg>
<!-- Patrones: RISE (creciente), FALL (decreciente), FLAT (estable) -->
<!-- Colores: Core #534AB7 · Lite #1D9E75 · negativo #D85A30 -->
```

---

### Monthly / YTD Performance (`.ks-`)
```
Usada en slides 4 y 5 de 1_inicio.html. DM Sans + DM Mono.

.ks-content    → contenedor principal con padding y gap entre secciones
.ks-headline-blue / .ks-headline-green → pill de período (navy / verde)
.ks-p-row      → primary metrics — valores grandes (ARR, New MRR, New Logos)
.ks-sec-row    → secondary metrics — tamaño medio (Revenue, Margin, EBITDA)
.ks-ter-row    → tertiary metrics — compacta (Churn, Payback, Base clientes)
.ks-d-compact  → card de dato compacta dentro de ter-row
.ks-d-tag-pill → badge tipo pill dentro de cards
.ks-pos        → #1D9E75 (variación positiva)
.ks-neg        → #D85A30 (variación negativa)
.ks-ins        → insight box base
.ks-ins-blue   → insight box navy (slide 4)
.ks-ins-green  → insight box verde (slide 5)
```

---

### Flywheel SVG Chart
```
SVG inline viewBox="0 0 820 170"
Y scale: min=100, max=500 → range 400 sobre 140px → 1px = 2.857 units
  y = 145 − (val − 100) / 400 × 140
X: 26 puntos, x de 40 a 790, step = 30px
Líneas: polyline (no path) con stroke-linejoin="round"
Gap fill: polygon con linearGradient teal 18%→4%
Gap bracket: líneas SVG manuales con texto "+N"
```

---

### Insight Cards (Flywheel)
```
Grid 3 columnas iguales, gap 9px
Tipos: .fly-icard.insight (azul) | .fly-icard.risk (coral) | .fly-icard.action (verde)
Border-left: 3px solid color correspondiente
Tags: 9px, monospace uppercase
```

---

## 5. Chart.js — Convenciones

**Versión:** 4.4.1 (CDN cloudflare)
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
```

**Configuración estándar:**
```js
{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },  // Siempre custom legend, nunca la de Chart.js
    tooltip: { enabled: false, external: customTooltipFn }
  },
  scales: {
    x: { grid: { display: false }, border: { display: false },
         ticks: { font: { size: 9, family: 'Inter' }, color: '#999' } },
    y: { grid: { color: 'rgba(128,128,128,.07)' }, border: { display: false },
         ticks: { font: { size: 9, family: 'Inter' }, color: '#999' } }
  }
}
```

**Tooltip custom (#tt):** Elemento `<div id="tt">` en el DOM, posicionado con `position:fixed` y controlado via `external` callback. Muestra título (mes + año), rows por dataset con colores, y total.

---

## 6. Slide Footer

```
Fondo: var(--color-surface) | Borde top: 1px solid var(--color-border)
Padding: 10px var(--slide-pad-x)
Layout: flex space-between
  Izquierda: número de página (11px, neutral)
  Derecha: "Alegra · Confidential" (11px, neutral)
```

---

## 7. Decisiones de diseño — registro

| Decisión | Razón |
|----------|-------|
| Fondo blanco obligatorio | El board necesita slides limpias; el navy como fondo completo es visualmente pesado y dificulta la lectura |
| TOC como lista, no grid de cards | El grid de cards se vea visualmente desordenado y no transmite jerarquía |
| Dos sistemas de tipografía | Las slides de GTM vinieron con diseño propio (DM Sans/Mono) del usuario — se respetó ese diseño en lugar de forzar Inter |
| SVG para el Flywheel (no Chart.js) | La visualización de área entre dos líneas + bracket de gap es más limpia y controlable en SVG puro |
| CSS Grid para alineación Country | El único problema de alineación del Core/Lite divider se resolvió con proporciones idénticas en hero y strip table headers |
| Scroll vertical, no paginación | Facilita la revisión y el export a PDF |
| Butterfly layout en Country Performance | El board necesita ver Core vs Lite de forma simétrica y comparar métricas fácilmente; el layout espejado centra la métrica y hace el contraste inmediato |
| ARR como hero de Country Performance | Investment es dato de input, ARR es el output del negocio — Investment se movió a primera fila de la tabla |
| SVG rect en lugar de polyline para sparklines | Las barras son más legibles a tamaños pequeños (44px wide); la polyline a esa escala pierde definición |
| Prefijos CSS por sección | `.bf-` (butterfly) · `.ks-` (Key Summary) · `.hc-` (Headcount) · `.pp-` (Product Performance) · `.pt-` (People & Talent) — evitan colisiones en el mismo HTML |
