# Alegra Board — Design System
**Guía oficial para agregar o modificar slides del board ejecutivo.**
Actualizado: Abril 2026

---

## Dimensiones de slide — CRÍTICO

Todas las slides son exactamente **960 × 540 px**.

| Parámetro | Valor |
|---|---|
| **Ancho** | **960 px** |
| **Alto** | **540 px** |
| Overflow | `hidden` — nada debe salir de ese rectángulo |
| Proporción | 16:9 |
| Padding horizontal | 56 px (`--slide-pad-x`) |
| Padding vertical | 48 px (`--slide-pad-y`) |
| Border radius | 10 px |
| Box shadow | `0 4px 24px rgba(0,0,0,0.10)` |

> Si estás diseñando en una herramienta externa (Figma, Canva, etc.) antes de pasarlo a HTML, trabaja a 960×540. Si agregas contenido y se desborda, la slide lo corta — no aparece ningún scroll.

**CSS base del contenedor:**
```css
.slide {
  width: 960px;
  height: 540px;
  overflow: hidden;
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.10);
  display: flex;
  flex-direction: column;
}
```

---

## Estructura de una slide

Toda slide tiene exactamente tres zonas. Los tres son `flex-shrink: 0` excepto `.slide-body` que crece con `flex: 1`.

```
┌─────────────────────────────────────────────┐  ← .slide-header  (~48px)
│  TÍTULO DE SLIDE                   Mar 2026 │     navy, título blanco, período teal
├─────────────────────────────────────────────┤
│                                             │
│                .slide-body                  │  ← flex: 1, overflow: hidden
│     (charts, tablas, KPIs, texto)           │     aquí va el contenido
│                                             │
├─────────────────────────────────────────────┤
│  Alegra · Confidential               Pág X  │  ← .slide-footer  (~32px)
└─────────────────────────────────────────────┘
```

**Espacio útil para contenido (.slide-body):** ≈ 460 px de alto × 960 px de ancho.

---

## Paleta de colores

### Colores primarios

| Token CSS | Hex | Uso |
|---|---|---|
| `--color-navy` | `#0f172b` | Header de slide, fondos section cover |
| `--color-teal` | `#14b8a6` | Acento de marca, período activo, highlights |
| `--color-teal-light` | `#f0fdfa` | Fondo de insight boxes |
| `--color-bg` | `#ffffff` | Fondo de slide — **siempre blanco** |
| `--color-surface` | `#f8fafc` | Cards secundarias, filas de sección |
| `--color-border` | `#e2e8f0` | Bordes de tabla, divisores |

### Colores semánticos

| Token CSS | Hex | Uso |
|---|---|---|
| `--color-positive` | `#16a34a` | Deltas positivos (verde) |
| `--color-negative` | `#C2410C` | Deltas negativos (naranja/rojo) |
| `--color-neutral` | `#64748b` | Texto secundario, badges neutros |
| `--color-text-primary` | `#0f172b` | Títulos y labels principales |
| `--color-text-secondary` | `#64748b` | Texto de soporte |

### Colores de producto

| Producto | Hex | Uso |
|---|---|---|
| Core | `#534AB7` | Líneas, puntos y labels de segmento Core |
| Lite | `#1D9E75` | Líneas, puntos y labels de segmento Lite |

### Paleta de deltas en tablas (colorblind-safe)

Usar azul/naranja en lugar de verde/rojo en tablas densas.

| Dirección | Hex | Cuándo usar |
|---|---|---|
| Positivo | `#185FA5` (azul) | Crecimiento, mejora de métricas |
| Negativo | `#E87722` (naranja) | Caída, deterioro de métricas |
| Neutro | `#64748b` (gris) | Sin cambio, N/A |

> **Regla:** Churn Rate y CAC tienen delta **invertido** — una caída es positiva (verde/azul), un alza es negativa (rojo/naranja).

---

## Tipografía

### Familias

| Familia | Uso principal |
|---|---|
| **Inter** | Base de la presentación: tablas, cuerpo, KPIs |
| **DM Sans** | Slides de GTM (Acquisition, Funnel, Flywheel), headlines editoriales |
| **DM Mono** | Números en charts, labels de ejes, valores de tabla |

```html
<!-- Pegar en el <head> de cualquier template nuevo -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Escala tipográfica

| Elemento | Familia | Tamaño | Peso |
|---|---|---|---|
| Título de slide (header) | DM Sans | 20 px | 600 |
| Período activo (header derecho) | DM Sans | 13 px | 500 |
| Valor KPI grande | DM Mono / DM Sans | 32 px | 700 |
| Label de KPI | DM Sans | 12 px | 500 |
| Celda de tabla — número | DM Mono | 10.5 px | 400 |
| Celda de tabla — label | DM Sans | 11 px | 500 |
| Header de tabla | DM Sans | 9.5 px | 700 uppercase |
| Fila de sección (tabla) | DM Sans | 8.5 px | 700 uppercase |
| Footer | DM Sans | 10 px | 500 |

---

## Componentes base (`base.css`)

Siempre importar en cada template:
```html
<link rel="stylesheet" href="../styles/base.css">
```

Este archivo contiene todos los tokens CSS y los componentes abajo descritos. **No duplicarlos en el `<style>` local del template.**

---

### Slide header

```css
.slide-header {
  background: #0f172b;        /* navy */
  padding: 16px 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
/* .title: color #fff, 20px, weight 600 */
/* .period: color #14b8a6, 13px, weight 500 */
```

```html
<div class="slide-header">
  <span class="title">Título de la slide — insight principal</span>
  <span class="period">{{ config.month_label }}</span>
</div>
```

---

### Section cover

Slide de portada de sección. Fondo navy completo, sin header ni footer.

```html
<div class="slide section-cover">
  <div class="eyebrow">Section 0X</div>
  <div class="section-title">Nombre de sección</div>
  <div class="section-sub">{{ config.quarter_label }}</div>
  <div class="slide-num">1</div>
</div>
```

```css
/* eyebrow: 11px, #14b8a6, uppercase, letter-spacing 2px */
/* section-title: 42px, #fff, weight 700, letter-spacing -1.5px */
/* section-sub: 15px, rgba(255,255,255,0.40) */
```

---

### Slide footer

```html
<div class="slide-footer">
  <span class="footer-brand">Alegra · Confidential</span>
  <span class="footer-page">2</span>
</div>
```

---

### KPI Card (`.kpi-card`)

```css
/* Fondo blanco | borde 0.5px --color-border | border-radius 8px | padding 20px 24px */
/* Label: 10px, uppercase, letter-spacing 1.5px, teal */
/* Valor: 32–40px, 700, text-primary */
/* Badge de variación: .badge.positive / .badge.negative / .badge.neutral */
```

---

### Badges / Pills

```css
.badge { padding: 3px 10px; border-radius: 99px; font-size: 11px; font-weight: 600; }
.badge.positive { background: #dcfce7; color: #16a34a; }
.badge.negative { background: #ffedd5; color: #C2410C; }
.badge.neutral  { background: #f1f5f9; color: #64748b; }
.badge.teal     { background: #f0fdfa; color: #14b8a6; }
```

---

### Insight box (`.insight-box`)

Aparece antes del chart como primera lectura.

```css
/* Fondo: #f0fdfa | Borde izquierdo: 3px solid #14b8a6 | Padding: 12px 16px */
/* Texto: 13px, color #64748b, line-height 1.6 */
```

---

### Ask to the Board chips

```css
.ask-chip { background: #f8fafc; border: 1px solid #e2e8f0;
            border-radius: 6px; padding: 10px 14px; font-size: 12px; }
.ask-chip strong { font-size: 11px; font-weight: 700; color: #0f172b; }
```

---

### Data table (`.data-table`)

```css
/* Ancho: 100% | border-collapse: collapse */
/* Header row: fondo navy, texto blanco, 10px */
/* Filas: border-top 1px solid --color-border, 13px */
```

---

## Charts — Chart.js

**Versión:** 4.4.1 (CDN Cloudflare)
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
```

**Configuración estándar para charts nuevos:**
```js
{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },   // Siempre leyenda custom — nunca la de Chart.js
    tooltip: { enabled: false }
  },
  scales: {
    x: {
      grid: { display: false },
      border: { display: false },
      ticks: { font: { size: 9, family: 'Inter' }, color: '#999' }
    },
    y: {
      grid: { color: 'rgba(128,128,128,.07)' },
      border: { display: false },
      ticks: { font: { size: 9, family: 'Inter' }, color: '#999' }
    }
  }
}
```

**Reglas de chart:**
- Nunca usar el eje Y doble — si necesitas dos escalas, usa dos paneles separados
- Los canvas deben estar dentro de un contenedor `position: relative` con alto fijo
- Aislar el JS de cada grupo de charts en un IIFE `(function(){ ... })()` para evitar colisiones de variables
- Labels de datos inline con el plugin `afterDatasetsDraw` — no tooltips flotantes

---

## Convención de prefijos CSS

Cada sección usa su propio prefijo para evitar colisiones. **Siempre usar el prefijo de la sección al agregar clases nuevas.**

| Prefijo | Sección / Componente |
|---|---|
| `.ks-` | Key Summary (slides 4–5 de 1_inicio) |
| `.bf-` | Butterfly table (Country Performance) |
| `.aw-` | ARR Walk |
| `.hc-` | Headcount — tabla principal (slide 2) |
| `.hcs-` | Headcount Summary — tabla de staff (slide 2, rediseño) |
| `.pt-` | People & Talent (slide 3, versión anterior) |
| `.pt2-` | People & Talent — charts (slide 3, versión actual) |
| `.pp-` | Product Performance |
| `.fly-` | Flywheel chart |
| `.rp-` | Retention panel |

---

## Reglas editoriales

- **Título accionable obligatorio:** el título de cada slide debe declarar el insight, no la categoría. Ej: *"Core Net New ARR cayó 88% QoQ"*, no *"ARR Walk Core"*.
- **Fondo siempre blanco** `#ffffff`: el navy `#0f172b` solo va en el header de slide y en section covers.
- **Fuente de datos** al pie de cada slide con métricas: *"Fuente: [sistema] · [corte de fecha]"*
- **Slides de riesgo** deben terminar con chips "Ask to the Board" — una pregunta explícita al board.
- **Sin texto fuera de los 960×540** — si el contenido no cabe, reducir fuente o partir en dos slides.

---

## Cómo agregar una slide nueva

1. Abrir el template `.j2` correspondiente en `templates/`
2. Copiar el bloque de una slide existente (header + body + footer + divider)
3. Asignar el número de página correcto en `.footer-page`
4. Si necesitas CSS nuevo: agregarlo en el `<style>` del template con el prefijo de la sección
5. Si el CSS puede ser útil en otros templates: considerarlo para `styles/base.css`
6. Generar el output:
   ```bash
   uv run --with jinja2 --with pyyaml python3 scripts/generate.py --template <nombre>
   ```
7. Verificar en browser que nada se desborda (960×540 estricto)

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Templates | Jinja2 (Python) — `templates/*.j2` |
| CSS base compartido | `styles/base.css` |
| Charts | Chart.js 4.4.1 |
| Fuentes | Google Fonts (CDN) |
| Generación | `scripts/generate.py` → `output/*.html` |
| Board completo | `scripts/merge_standalone.py` → `output/board_standalone.html` |
