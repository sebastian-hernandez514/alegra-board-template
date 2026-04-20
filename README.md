# Alegra Board Presentation — Template

Template HTML del board ejecutivo mensual/trimestral de Alegra. Construido con HTML/CSS/Chart.js. Diseñado para storytelling con datos de SaaS B2B multimercado.

---

## Estado del proyecto

| # | Sección | Estado | Slides |
|---|---------|--------|--------|
| 1 | Inicio de presentación | ✅ Completo | 5 slides |
| 2 | Discussion Topic | ✅ Completo | 6 slides (3 temas × 2) |
| 3 | ARR Walk | ✅ Completo | 8 slides |
| 4 | Financial Performance | 🔶 Parcial | 3 slides (cover ✅ · Product Performance ✅ · slide 3 placeholder) |
| 5 | Go to Market | ✅ Completo | 6 slides |
| 6 | R&D | ⏳ Pendiente | — |
| 7 | Headcount Summary | ✅ Completo | 3 slides |
| 8 | Appendix | ⏳ Pendiente | — |

**Deuda técnica activa:**
- ARR Walk slides 2–4 tienen banner "Pending Redesign" — requieren rediseño de waterfall a barras de cascada visual
- Go to Market slide 6 es placeholder (Accountant Flywheel cont.)
- Financial Performance slide 3 es placeholder (contenido pendiente de definición)

---

## Estructura del proyecto

```
Template Board/
├── README.md                    ← Este archivo — estado y guía de uso
├── slides/                      ← Archivos HTML por sección (uno por sección)
│   ├── 1_inicio.html            ← Cover, CEO H&L, TOC, Monthly Performance, YTD Performance
│   ├── 2_discussion_topic.html  ← 3 temas × 2 slides
│   ├── 3_arr_walk.html          ← ARR Walk Core/Lite/Alanube + Country Performance (4 países)
│   ├── 4_financial_performance.html ← Product Performance (parcial)
│   ├── 5_go_to_market.html      ← New Logos, Acquisition, Funnel, Flywheel
│   ├── 7_headcount.html         ← Headcount by Team + People & Talent
│   └── [6_rd.html · 8_appendix.html — pendientes]
├── styles/
│   └── base.css                 ← Tokens CSS y componentes compartidos por todas las secciones
├── docs/
│   ├── DESIGN_SYSTEM.md         ← Tokens de color, tipografía, componentes y convenciones CSS
│   ├── BOARD_BLUEPRINT.md       ← Blueprint slide por slide: qué pregunta responde, qué muestra
│   └── CHANGELOG.md             ← Historial de versiones y decisiones por sesión
├── assets/
│   ├── reference/               ← PDFs originales de referencia (no versionar contenido)
│   └── country_performance_reference.png
└── scripts/                     ← Scripts Python de mantenimiento del template
    ├── rebuild_country_slides.py ← Reconstruye los 4 Country Performance con butterfly layout
    └── fix_sparklines_bars.py   ← Convirtió sparklines de polyline a barras SVG (rect)
```

---

## Cómo usar

### Ver el template
Abrir cualquier archivo de `slides/` directamente en el browser. No requiere servidor.

### Navegar entre slides
Cada archivo HTML contiene múltiples slides apiladas verticalmente. Hacer scroll para navegar.

### Actualizar datos (fase actual: placeholders)
Los valores están hardcodeados como datos de ejemplo. Los textos con `{{Month}}`, `{{Year}}`, `{{PrevMonth}}`, `{{PrevYear}}` son los únicos placeholders activos por ahora.

### Conectar a datos reales (fase futura)
La fuente de verdad de métricas y queries está en `docs/BOARD_BLUEPRINT.md` (sección de cada slide).

---

## Stack técnico

- **HTML/CSS** puro — sin frameworks
- **Chart.js 4.4.1** (CDN cloudflare) — gráficas interactivas
- **SVG inline** — gráficas customizadas (Flywheel, sparklines butterfly)
- **Google Fonts** — Inter (base) + DM Sans + DM Mono (slides GTM y Headcount)
- **Redshift** (futuro) — fuente de datos real via Python/boto3 + `redshift_guard.py`

---

## Arquitectura objetivo — Board automatizado

Ver `docs/ARCHITECTURE.md` para el diseño completo.

```
RS → metrics.yaml  ┐
Google Sheets       ├→ generate.py → slides/*.html → PDF
editorial.yaml      ┘
```

**Flujo por rol:**
- **Data team:** corre `generate.py` al cierre del período
- **CEO / área:** llena su tab en Google Sheets (H&L, Discussion, narrativas)
- **Board:** recibe el PDF generado automáticamente

**Hoja de ruta:**
1. ✅ Template HTML completo con todos los slides
2. ⏳ `docs/DATA_SPEC.md` — contrato de qué query alimenta cada variable
3. ⏳ Convertir `slides/*.html` → `templates/*.j2` (Jinja2)
4. ⏳ `scripts/fetch_metrics.py` — Redshift → `data/metrics.yaml`
5. ⏳ `scripts/fetch_editorial.py` — Google Sheets → `data/editorial.yaml`
6. ⏳ `scripts/generate.py` — orquestador completo
7. ⏳ `scripts/export_pdf.py` — PDF listo para distribución

---

## Contexto del negocio

Alegra es una plataforma SaaS de gestión empresarial para SMBs en Latinoamérica. Opera con dos productos principales:
- **Core** — Suite completa (facturación, inventario, POS, CRM). Color: `#534AB7` (purple)
- **Lite** — Producto freemium simplificado. Color: `#1D9E75` (green)
- **Alanube** — Vertical de proveedores electrónicos (Colombia)

Mercados principales: Colombia (CO), México (MX), República Dominicana (DR), Costa Rica (CR).
