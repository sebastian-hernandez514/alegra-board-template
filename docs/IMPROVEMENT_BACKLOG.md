# Backlog de Mejoras — Alegra Board Template
*Generado a partir de revisión DataViz (10 Apr 2026)*
*Basado en principios: Knaflic, Tufte, Few, Cairo, Evergreen, Wong, Schwabish*

---

## Escala de Importancia

| Nivel | Criterio |
|-------|----------|
| 🔴 CRÍTICO | Viola un principio fundamental · Puede llevar a decisiones incorrectas |
| 🟠 ALTO | Reduce significativamente el valor de decisión del slide |
| 🟡 MEDIO | Mejora claridad o accesibilidad sin cambiar la historia |
| 🟢 BAJO | Refinamiento visual o de estilo · No cambia el mensaje |

---

## I. Títulos y Narrativa (Editorial — sin cambios de código)

| # | Mejora | Afecta | Importancia |
|---|--------|--------|-------------|
| N-1 | Reemplazar TODOS los títulos de slides por **action titles** que declaren el insight, no la categoría. Ej: "ARR Walk — Core" → "Core Net New ARR cayó 88% QoQ — churn supera adiciones por primera vez en 4 trimestres" | Todos los archivos | 🔴 CRÍTICO · **Parcial: S1 listo (4/21). Ver NARRATIVE.md** |
| N-2 | El **headline de Monthly Performance** ya casi lo logra pero prioriza el lado positivo. Mover la señal de churn al headline principal — es el riesgo más importante del período | `1_inicio.html` slide 4 | 🟠 ALTO · **✅ Resuelto junto con N-1** |
| N-3 | Exportar el mecanismo **"Ask to the Board"** (chips de pregunta al board) de Discussion Topics hacia ARR Walk y GTM — los slides de riesgo deben terminar con una pregunta o decisión explícita | `3_arr_walk.html`, `5_go_to_market.html` | 🟠 ALTO |
| N-4 | Añadir **"Big Idea"** al inicio de cada sección: una sola oración que diga qué acción se pide al board y por qué. Vive en el section cover o como primer elemento del primer slide de contenido | Todos los section covers | 🟠 ALTO |
| N-5 | **Horizontal logic test:** leer solo los títulos de todos los slides en secuencia debería contar la historia completa. Hoy no lo hace. Requiere redacción editorial por sección | Todos los archivos | 🟠 ALTO |
| N-6 | Anotar en el ARR Walk que el **ratio New/Churn se deterioró** en 1Q26 (adiciones cubren solo 79% del churn Core) — dato visible en los números pero no articulado | `3_arr_walk.html` slides 2–3 | 🟡 MEDIO |
| N-7 | Articular la **dinámica de mix ARR:** ARPA Core ($34) vs ARPA Lite ($11) = 3x. Si Lite crece más rápido, el ARR mix se deteriora aunque logos suban. No está escrito en ningún slide | `3_arr_walk.html` Country Performance | 🟡 MEDIO |

---

## II. Visualizaciones — Problemas Estructurales

| # | Mejora | Afecta | Importancia |
|---|--------|--------|-------------|
| V-1 | **Eliminar doble eje Y (y2)** del ARR Walk. El eje derecho para Net New ARR crea correlaciones visuales falsas con las barras (Few: "dual-axis charts create false correlations"). Opción A: panel separado debajo. Opción B: anotar Net New ARR directamente sobre cada par de barras como delta | `3_arr_walk.html` slides 2–3, `1_inicio.html` slide 6 | 🔴 CRÍTICO |
| V-2 | **Reducir in-bar labels** en el ARR Walk. Hoy cada barra muestra logos count (7.5px) + ARR value. A escala de presentación, los logos son ilegibles — son chartjunk. Mantener solo el valor de ARR en $M dentro de la barra. Logos van en tooltip o Q-card | `3_arr_walk.html` slides 2–3, `1_inicio.html` slide 6 | 🟠 ALTO |
| V-3 | **Rediseñar butterfly Country Performance** → small multiples. 4 países × 2 productos = 8 paneles, misma escala, dirección de lectura uniforme (izq → der en todos). El layout espejado obliga a aprender dos sistemas de lectura simultáneos (Few's 5-second rule falla) | `3_arr_walk.html` slides 5–8 | 🟠 ALTO |
| V-4 | **Q-cards al pie del ARR Walk** son parcialmente redundantes con el chart. Evaluar si pueden reemplazarse por anotaciones de BoP/EoP directamente en el chart, o convertirse en una sola fila de texto con los 5 valores | `3_arr_walk.html` slides 2–3, `1_inicio.html` slide 6 | 🟡 MEDIO |
| V-5 | **Añadir línea de referencia de Net New ARR promedio histórico** en el chart de ARR Walk — sin contexto de cuál es el "normal", el colapso de 1Q26 no tiene magnitud para el board | `3_arr_walk.html` slides 2–3 | 🟡 MEDIO |
| V-6 | **ARR Walk Alanube (slide 4)** sigue con tabla waterfall y banner "Pending Redesign". Aplicar el mismo rediseño visual de Core/Lite | `3_arr_walk.html` slide 4 | 🟡 MEDIO |
| V-7 | **Añadir anotaciones en inflection points** del chart de ARR Walk — Knaflic: "annotations transform a chart from explore to explain." Mínimo: marcar con texto el trimestre donde churn superó adiciones | `3_arr_walk.html` slides 2–3 | 🟡 MEDIO |

---

## III. Color y Accesibilidad

| # | Mejora | Afecta | Importancia |
|---|--------|--------|-------------|
| C-1 | **Sustituir rojo/verde por naranja/azul** para positivo/negativo. El esquema actual (#E24B4A rojo / #1D9E75 verde) es inaccesible para daltónicos rojo-verde (~8% de hombres). Usar `#E87722` (naranja) para negativo/riesgo y `#185FA5` (azul) para positivo/mejora. Core/Lite mantienen sus colores de producto | `base.css` + todos los archivos | 🟠 ALTO |
| C-2 | **Revisar contraste de texto en KPI cards oscuras.** Labels en `rgba(255,255,255,0.35)` sobre `#1A1917` podrían no pasar WCAG AA en proyección. Subir a mínimo `rgba(255,255,255,0.55)` | `1_inicio.html`, `3_arr_walk.html` | 🟡 MEDIO |
| C-3 | **Schwabish "start with gray":** en los charts del ARR Walk, considerar grayout de trimestres anteriores y destacar solo 1Q26 en color — el período que necesita atención. Hoy todos los trimestres compiten igual | `3_arr_walk.html` slides 2–3 | 🟡 MEDIO |

---

## IV. Clutter y Elementos Innecesarios

| # | Mejora | Afecta | Importancia |
|---|--------|--------|-------------|
| CL-1 | **Ocultar `.slide-divider`** (↓ 1/5, ↓ 2/5, etc.) en modo presentación/PDF. Son útiles en desarrollo pero son ruido en el producto final. Añadir clase `no-print` o display:none en media print | `base.css` | 🟡 MEDIO |
| CL-2 | **Eyebrow "Section 03"** en section covers aporta poco cuando ya se sabe que estás en ARR Walk. Evaluar si el número de sección es necesario o puede vivir solo en el footer | `3_arr_walk.html` + otros | 🟢 BAJO |
| CL-3 | **Borde `.aw-kpi-card::before`** (`rgba(255,255,255,0.07)`) es visualmente imperceptible. Es CSS que no hace nada. Eliminar | `1_inicio.html`, `3_arr_walk.html` | 🟢 BAJO |
| CL-4 | **Tres familias tipográficas** (Inter + DM Sans + DM Mono) coexisten en la presentación. Consolidar a DM Sans (cuerpo) + DM Mono (números) como estándar global. Inter quedaría solo como fallback | `base.css` + todos | 🟢 BAJO |
| CL-5 | **Borders de cards** en los KPI cards oscuros — el contraste de fondo ya los delimita. El borde 0.5px es non-data ink (Tufte). Evaluar eliminar | `1_inicio.html`, `3_arr_walk.html` | 🟢 BAJO |

---

## V. Contexto y Credibilidad

| # | Mejora | Afecta | Importancia |
|---|--------|--------|-------------|
| CT-1 | **Añadir fuente de datos al pie** de cada slide con datos: "Fuente: Redshift · `fact_customers_mrr` · Corte {{Month}} {{Year}}". Una línea, 9px, integrada en `.slide-footer`. Estándar WSJ (Dona Wong) | `base.css` footer + todos | 🟠 ALTO |
| CT-2 | **Líneas de referencia/target** en slides de KPI — un número sin target no tiene contexto. Ej: en Monthly Performance, el Logo Churn de 3.5% está "0.8pp sobre presupuesto" en texto, pero no hay una línea de budget en ningún chart | Slides con charts de trend | 🟠 ALTO |
| CT-3 | **Añadir período de comparación claro** en Country Performance — hoy muestra MoM y YoY en la tabla pero el hero card de ARR no tiene una línea de contexto histórico visible de un vistazo | `3_arr_walk.html` slides 5–8 | 🟡 MEDIO |
| CT-4 | **No hay incertidumbre comunicada** en ningún número forward-looking. Si hay proyecciones o forecasts en algún slide, distinguirlos visualmente (línea punteada vs sólida, Cairo: truthfulness) | Slides con datos forward | 🟡 MEDIO |

---

## VI. Secciones Pendientes de Construir

| # | Tarea | Importancia |
|---|-------|-------------|
| P-1 | **R&D (`6_rd.html`)** — archivo no existe. Estructura pendiente de definición con equipo | 🟠 ALTO |
| P-2 | **Appendix (`8_appendix.html`)** — archivo no existe. Tablas de soporte para el board | 🟡 MEDIO |
| P-3 | **Financial Performance slide 3** (`4_financial_performance.html`) — placeholder activo, contenido por definir | 🟡 MEDIO |
| P-4 | **GTM slide 6** (`5_go_to_market.html`) — placeholder activo, Accountant Flywheel continuación | 🟡 MEDIO |

---

## Resumen Ejecutivo del Backlog

| Importancia | Cantidad | Items |
|-------------|----------|-------|
| 🔴 CRÍTICO | 2 | N-1 (action titles), V-1 (doble eje Y) |
| 🟠 ALTO | 10 | N-2, N-3, N-4, N-5, V-2, V-3, C-1, CT-1, CT-2, P-1 |
| 🟡 MEDIO | 11 | N-6, N-7, V-4, V-5, V-6, V-7, C-2, C-3, CL-1, CT-3, CT-4, P-2, P-3, P-4 |
| 🟢 BAJO | 4 | CL-2, CL-3, CL-4, CL-5 |

**Quick wins (alto impacto, bajo esfuerzo técnico):**
- N-1: Reescribir títulos — solo texto, sin código
- V-1: Eliminar y2 del ARR Walk — 20 líneas de JS
- CT-1: Añadir fuente al footer — 5 líneas de CSS + 1 línea de HTML por archivo
- C-1: Cambiar paleta rojo→naranja — buscar/reemplazar en base.css y archivos

---
*Última actualización: 10 Apr 2026*
