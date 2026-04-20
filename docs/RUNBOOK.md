# RUNBOOK — Cómo generar el Board cada mes
*Guía operacional para correr el pipeline de principio a fin.*
*Última actualización: Apr 2026*

---

## Visión rápida del flujo

```
1. Actualizar CSVs (P&L, Payback)
2. Editar data/config.yaml (período)
3. Editar data/editorial/*.yaml (CEO H&L, ARR Asks, Discussion Topics)
4. Correr fetch_metrics.py → genera data/metrics.yaml
5. Correr generate.py → genera output/*.html
6. Abrir en browser y revisar
```

---

## Paso 0 — Pre-requisitos (solo la primera vez)

### Autenticación AWS SSO
```bash
~/aws-cli-v2/aws-cli/aws sso login --profile alegra
```
Abre el browser, el usuario aprueba y listo. La sesión dura varias horas.
Si un comando falla con error de credenciales/token expirado → volver a correr esto.

### Herramientas necesarias
- `uv` en `~/.local/bin/uv`
- AWS CLI v2 en `~/aws-cli-v2/aws-cli/aws`
- Todo lo demás se instala automáticamente con `uv run --with ...`

---

## Paso 1 — Actualizar CSVs

> Solo necesario cuando hay datos nuevos. Los CSVs están en `csv/`.

| CSV | Cuándo actualizar | Qué contiene |
|-----|-------------------|--------------|
| `csv/P&L Histórico- ACtual.csv` | Cada mes, al cierre | P&L real mensual (Operating Income, CoR, CAC, etc.) |
| `csv/P&L Histórico - Budget.csv` | Cuando cambia el plan | P&L budget anual |
| `csv/Metricas_budget.csv` | Al inicio del año / si cambia el plan | Budget de ARR, New MRR, New Logos, Churn por mes |
| `csv/Payback.csv` | Cada mes si hay dato nuevo | Payback por país y segmento |

**Si solo actualizaste CSVs** (sin necesidad de re-consultar Redshift), usar el flag `--csv-only` en el paso 4.

---

## Paso 2 — Actualizar `data/config.yaml`

Editar el período activo antes de cualquier otra cosa:

```yaml
# data/config.yaml
month_label:   "March 2026"      # Mes en inglés, largo
quarter_label: "1Q26"            # Quarter actual
prev_year:     "2025"            # Año anterior (para comparaciones YoY)
year:          2026              # Año actual
```

> **Nota:** `quarter_label` siempre refleja el quarter del mes activo (ej: enero, febrero y marzo → `1Q26`).

---

## Paso 3 — Llenar los YAMLs editoriales

Los archivos en `data/editorial/` contienen el contenido que humanos definen antes del board. No se generan automáticamente.

### `data/editorial/ceo.yaml` — CEO rellena esto

```yaml
ceo_title: "CEO Highlights & Lowlights"

highlights:
  - "Texto del highlight 1"
  - "Texto del highlight 2"
  - "..."   # hasta ~5 bullets

lowlights:
  - "Texto del lowlight 1"
  - "Texto del lowlight 2"
  - "..."   # 2-3 bullets típicamente

financial_update: >
  Párrafo de contexto financiero para el slide de CEO H&L.
  Puede tener varias líneas.
```

### `data/editorial/arr_walk.yaml` — Product/Finance rellena esto

```yaml
products:
  - id: core
    action_title: "Action title del slide ARR Walk Core (insight, no categoría)"
    asks:
      - title: "Nombre corto del ask"
        text: "Pregunta o decisión que se lleva al board."

  - id: lite
    action_title: "Action title del slide ARR Walk Lite"
    asks:
      - title: "Nombre corto"
        text: "Pregunta al board."

alanube_title: "Alanube ARR Walk — Documentos electrónicos"
alanube_insight: "Insight clave de Alanube para el período."
```

> Máximo 3 `asks` por producto. El campo `action_title` reemplaza el header del slide — debe declarar el insight, no la categoría.

### `data/editorial/discussion_topics.yaml` — Responsable por tema

Ver la estructura actual del archivo como referencia. Soporta dos layouts:
- `two_col` — dos columnas de texto (contexto + propuesta)
- `table` — tabla de datos comparativa

---

## Paso 4 — Correr `fetch_metrics.py`

Este script consulta Redshift y los CSVs, y escribe `data/metrics.yaml`.

### Caso A — Mes nuevo (consulta RS completa)
```bash
cd "/Users/sebastian_alegra/Alegra IA/Template Board"
uv run --with boto3 --with pyyaml python3 scripts/fetch_metrics.py --month 2026-03
```

### Caso B — Solo actualizaste CSVs (sin tocar RS)
```bash
uv run --with boto3 --with pyyaml python3 scripts/fetch_metrics.py --month 2026-03 --csv-only
```

### Mes normal vs Cierre de Quarter

El script detecta automáticamente el tipo de período según el número de mes:

| Mes | Tipo | Comportamiento |
|-----|------|----------------|
| ene, feb, abr, may, jul, ago, oct, nov | **Mes normal** | Comparación MoM |
| **mar, jun, sep, dic** | **Cierre de Q** | Comparación QoQ |

**Qué cambia en cierre de Q:**

| Métrica | Mes normal | Cierre de Q |
|---------|------------|-------------|
| `new_logos` | Logos del mes | Suma de los 3 meses del Q |
| `new_mrr` | MRR del mes | Suma de los 3 meses del Q |
| `new_logos_vs_budget` | Real mes vs budget mes | Suma Q real vs suma Q budget |
| `new_mrr_vs_budget` | Real mes vs budget mes | Suma Q real vs suma Q budget |
| `logo_churn_core/global` | Tasa del mes | Promedio de las 3 tasas mensuales del Q |
| `arr_total` | EoP del mes (siempre puntual) | EoP del mes (siempre puntual) |

> El flag `is_quarter_end` queda guardado en `metrics.yaml` y los templates lo leen para cambiar etiquetas (MoM → QoQ) y valores automáticamente.

### Fórmula de Churn (validada con Retention)
```
Churn Rate = (logos CHURN - logos REACTIVATED) / BoP
BoP = logos activos del mes anterior
      = COUNT DISTINCT WHERE event_logo NOT IN ('CHURN', 'AWAITING PAYMENT')
```

---

## Paso 5 — Correr `generate.py`

Convierte `data/metrics.yaml` + `data/editorial/*.yaml` + `templates/*.j2` → `output/*.html`.

### Generar todos los slides
```bash
uv run --with jinja2 --with pyyaml python3 scripts/generate.py
```

### Generar solo una sección (más rápido para iterar)
```bash
uv run --with jinja2 --with pyyaml python3 scripts/generate.py --template 1_inicio
uv run --with jinja2 --with pyyaml python3 scripts/generate.py --template 3_arr_walk
```

> **Regla de oro:** `generate.py` solo lee `metrics.yaml`. Si el YAML no cambió, el HTML no cambia. Se puede correr infinitas veces sin costo de RS.

---

## Paso 6 — Revisar el output

Abrir los archivos de `output/` directamente en el browser:
```
output/
├── 1_inicio.html
├── 2_discussion_topic.html
├── 3_arr_walk.html
├── 4_financial_performance.html
├── 5_go_to_market.html
└── 7_headcount.html
```

Cada archivo tiene múltiples slides apiladas verticalmente — hacer scroll para navegar.

> `slides/*.html` son los HTMLs estáticos originales de diseño (referencia). El output real del pipeline está en `output/`.

---

## Checklist mensual completo

```
PRE-PIPELINE
[ ] Sesión SSO activa (aws sso login --profile alegra)
[ ] CSV P&L actualizado con el mes cerrado
[ ] CSV Payback actualizado si hay dato nuevo
[ ] data/config.yaml actualizado (month_label, quarter_label, year)

EDITORIAL (humanos)
[ ] data/editorial/ceo.yaml — CEO llenó highlights, lowlights y financial_update
[ ] data/editorial/arr_walk.yaml — action titles y asks por Core, Lite y Alanube
[ ] data/editorial/discussion_topics.yaml — hasta 3 temas con asks al board

PIPELINE
[ ] fetch_metrics.py --month YYYY-MM corrió sin errores
[ ] data/metrics.yaml tiene fecha de hoy (verificar timestamps)
[ ] generate.py corrió sin errores
[ ] output/*.html abre correctamente en browser

REVISIÓN
[ ] Slide 4 (Monthly Performance) — números concuerdan con reporte de cierre
[ ] Slide 5 (YTD Performance) — acumulados correctos
[ ] Slide 6 (ARR Global) — chart con datos del trimestre correcto
[ ] CEO H&L — texto del YAML se ve bien formateado
[ ] Discussion Topics — layouts renderizan correctamente
```

---

## Fuentes de datos por sección

| Sección | Fuente principal | Fuente editorial |
|---------|-----------------|-----------------|
| S1 Cover + config | `data/config.yaml` | — |
| S1 CEO H&L | — | `editorial/ceo.yaml` |
| S1 TOC | Template estático | — |
| S1 Monthly Performance | Redshift + CSVs | — |
| S1 YTD Performance | Redshift | — |
| S1 ARR Global | Redshift | — |
| S2 Discussion Topics | — | `editorial/discussion_topics.yaml` |
| S3 ARR Walk Core/Lite | Redshift | `editorial/arr_walk.yaml` (asks) |
| S3 Country Performance | Redshift + `csv/Payback.csv` | — |
| S4 Financial Performance | CSVs (P&L) | — |
| S5 Go to Market | Redshift | — |
| S7 Headcount | Pendiente (People & Talent) | — |

---

## Troubleshooting

### Error de credenciales AWS
```
botocore.exceptions.TokenRetrievalError
```
→ Correr: `~/aws-cli-v2/aws-cli/aws sso login --profile alegra`

### `metrics.yaml` no se generó / está vacío
→ Verificar que el mes pasado como `--month` existe en Redshift (`fact_customers_mrr`)
→ Verificar que los CSVs tienen el mes activo en sus filas

### Un template no renderiza
→ Correr solo ese template para ver el error:
```bash
uv run --with jinja2 --with pyyaml python3 scripts/generate.py --template 1_inicio
```

### Los números del slide no cuadran
→ Revisar `data/metrics.yaml` directamente — es la única fuente que lee `generate.py`
→ Si el YAML tiene el número incorrecto, el problema está en `fetch_metrics.py`
→ Nunca editar `metrics.yaml` a mano
