#!/usr/bin/env python3
"""
fetch_metrics.py — Fetch ARR Walk data from Redshift → data/metrics.yaml

Usage:
    uv run --with boto3 python3 scripts/fetch_metrics.py
    uv run --with boto3 python3 scripts/fetch_metrics.py --refresh
    uv run --with boto3 python3 scripts/fetch_metrics.py --month 2026-02

Outputs:
    data/metrics.yaml   (consumed by generate.py → Jinja2 templates)

Sources:
    - bi_strategic.arr_walk_monthly_summary   (segment-level ARR Walk)
    - dwh_facts.fact_customers_mrr            (logos consolidated + country-level)

Data NOT covered here (needs fetch_sheets.py):
    - Budget / Plan  (arr_vs_budget, new_mrr_vs_budget, etc.)
    - Gross Margin / EBITDA  (financial P&L)
    - Payback period
    Placeholders are written as "N/A" so templates render without crashing.
"""

import sys, json, argparse, time, math, csv, calendar
from datetime import datetime
from collections import defaultdict
from pathlib import Path

import yaml  # pip install pyyaml (or uv run --with pyyaml)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from redshift_guard import run_query

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
CACHE_FILE  = ROOT / "data" / ".cache_metrics.json"
OUTPUT_FILE = ROOT / "data" / "metrics.yaml"
BUDGET_FILE  = ROOT / "csv" / "Metricas_budget.csv"
PNL_ACTUAL   = ROOT / "csv" / "P&L Histórico- ACtual.csv"
PNL_BUDGET   = ROOT / "csv" / "P&L Histórico - Budget.csv"
PAYBACK_FILE = ROOT / "csv" / "Payback.csv"
FX_FILE      = ROOT / "csv" / "paises_fx.csv"

# ── FX Conversion ───────────────────────────────────────────────────────────────
# Los 5 países en paises_fx.csv — el resto usa amount_mrr tal cual (ya en USD)
_FX_PAISES = {"argentina", "colombia", "mexico", "peru", "spain"}

# Decimales a usar por país al redondear la tasa FX
# CO/AR → entero; MX/PE → 1 decimal; ES → 3 decimales
_FX_DECIMALS = {
    "colombia":  0,
    "argentina": 0,
    "mexico":    1,
    "peru":      1,
    "spain":     3,
}

# Mapeo de app_version (Redshift) → nombre en paises_fx.csv
_APP_TO_FX_PAIS = {
    "colombia":  "colombia",
    "mexico":    "mexico",
    "argentina": "argentina",
    "peru":      "peru",
    "spain":     "spain",
    "españa":    "spain",
    "espana":    "spain",
}

def load_fx():
    """Carga paises_fx.csv → {(pais, 'YYYY-MM'): fx_rate}"""
    fx = {}
    try:
        with open(FX_FILE, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                pais  = (row.get('pais')  or '').strip().lower()
                fecha = (row.get('fecha') or '').strip()[:7]   # "YYYY-MM"
                val   = (row.get('valor') or '').strip()
                if pais in _FX_PAISES and fecha and val:
                    try:
                        decimals = _FX_DECIMALS.get(pais, 0)
                        fx[(pais, fecha)] = round(float(val.replace(',', '.')), decimals)
                    except ValueError:
                        pass
    except FileNotFoundError:
        print("  ⚠️  paises_fx.csv no encontrado — usando amount_mrr sin conversión FX")
    return fx

def _apply_fx_to_row(row, fx):
    """Convierte mrr_local_* a USD y escribe el resultado en mrr_usd_*.
    - Países en paises_fx.csv (CO/MX/AR/PE/ES): mrr_local / tasa CSV
    - Resto: usa amount_usd_mrr directamente (ya viene en el row como mrr_usd_*)
    """
    app  = (row.get('app_version') or '').strip().lower()
    pais = _APP_TO_FX_PAIS.get(app)
    if not pais:
        return  # No es país FX → mrr_usd_* ya tiene amount_usd_mrr correcto
    m    = str(row.get('date_month') or '')[:7]
    rate = fx.get((pais, m))
    if not rate:
        return  # Sin tasa para ese mes → fallback a amount_usd_mrr
    pairs = [('mrr_local_eop',      'mrr_usd_eop'),
             ('mrr_local_new',      'mrr_usd_new'),
             ('mrr_local_recov',    'mrr_usd_recov'),
             ('mrr_local_react',    'mrr_usd_react'),
             ('mrr_local_churn',    'mrr_usd_churn'),
             ('mrr_local_upsell',   'mrr_usd_upsell'),
             ('mrr_local_downsell', 'mrr_usd_downsell')]
    for local_col, usd_col in pairs:
        row[usd_col] = float(row.get(local_col) or 0) / rate

CACHE_VERSION = "v10-board-metrics-expansion-delta"

# ── SQL ────────────────────────────────────────────────────────────────────────
# Fuente única: dwh_facts.fact_customers_mrr
# Reemplaza arr_walk_monthly_summary + _SQL_NEW_LOGOS_COUNTRY + _SQL_CHURN_COUNTRY
_SQL_FACT_SUMMARY = """
WITH lagged AS (
  SELECT date_month, segment_type_def, app_version, id_company, event_logo,
         amount_mrr,
         amount_usd_mrr,
         LAG(amount_mrr)     OVER (PARTITION BY id_company ORDER BY date_month) AS prev_mrr_local,
         LAG(amount_usd_mrr) OVER (PARTITION BY id_company ORDER BY date_month) AS prev_mrr_usd
  FROM dwh_facts.fact_customers_mrr
  WHERE date_month <= '{cutoff}-01'
    AND segment_type_def IN ('Core', 'Lite')
)
SELECT date_month,
       segment_type_def                                                                                          AS segment,
       app_version,
       COUNT(DISTINCT CASE WHEN event_logo NOT IN ('CHURN','AWAITING PAYMENT') THEN id_company END)             AS logos_eop,
       COUNT(DISTINCT CASE WHEN event_logo = 'NEW'         THEN id_company END)                                 AS logos_new,
       COUNT(DISTINCT CASE WHEN event_logo = 'RECOVERED'   THEN id_company END)                                 AS logos_recov,
       COUNT(DISTINCT CASE WHEN event_logo = 'REACTIVATED' THEN id_company END)                                 AS logos_react,
       COUNT(DISTINCT CASE WHEN event_logo = 'CHURN'       THEN id_company END)                                 AS logos_churn,
       SUM(CASE WHEN event_logo NOT IN ('CHURN','AWAITING PAYMENT') THEN amount_mrr          ELSE 0 END)        AS mrr_local_eop,
       SUM(CASE WHEN event_logo = 'NEW'         THEN amount_mrr          ELSE 0 END)                            AS mrr_local_new,
       SUM(CASE WHEN event_logo = 'RECOVERED'   THEN amount_mrr          ELSE 0 END)                            AS mrr_local_recov,
       SUM(CASE WHEN event_logo = 'REACTIVATED' THEN amount_mrr          ELSE 0 END)                            AS mrr_local_react,
       SUM(CASE WHEN event_logo = 'CHURN'       THEN COALESCE(prev_mrr_local, 0) ELSE 0 END)                   AS mrr_local_churn,
       SUM(CASE WHEN event_logo IN ('EXPANSION UPSELL','EXPANSION CROSS SELLING')
                THEN amount_mrr - COALESCE(prev_mrr_local, 0) ELSE 0 END)                                      AS mrr_local_upsell,
       SUM(CASE WHEN event_logo IN ('CONTRACTION DOWNSELL','CONTRACTION CROSS SELLING')
                THEN amount_mrr - COALESCE(prev_mrr_local, 0) ELSE 0 END)                                      AS mrr_local_downsell,
       SUM(CASE WHEN event_logo NOT IN ('CHURN','AWAITING PAYMENT') THEN amount_usd_mrr      ELSE 0 END)        AS mrr_usd_eop,
       SUM(CASE WHEN event_logo = 'NEW'         THEN amount_usd_mrr      ELSE 0 END)                            AS mrr_usd_new,
       SUM(CASE WHEN event_logo = 'RECOVERED'   THEN amount_usd_mrr      ELSE 0 END)                            AS mrr_usd_recov,
       SUM(CASE WHEN event_logo = 'REACTIVATED' THEN amount_usd_mrr      ELSE 0 END)                            AS mrr_usd_react,
       SUM(CASE WHEN event_logo = 'CHURN'       THEN COALESCE(prev_mrr_usd, 0)   ELSE 0 END)                   AS mrr_usd_churn,
       SUM(CASE WHEN event_logo IN ('EXPANSION UPSELL','EXPANSION CROSS SELLING')
                THEN amount_usd_mrr - COALESCE(prev_mrr_usd, 0) ELSE 0 END)                                    AS mrr_usd_upsell,
       SUM(CASE WHEN event_logo IN ('CONTRACTION DOWNSELL','CONTRACTION CROSS SELLING')
                THEN amount_usd_mrr - COALESCE(prev_mrr_usd, 0) ELSE 0 END)                                    AS mrr_usd_downsell
FROM lagged
GROUP BY date_month, segment_type_def, app_version
ORDER BY date_month, segment_type_def, app_version
"""

# Logos consolidados (COUNT DISTINCT cross-segmento — evita doble conteo)
_SQL_LOGOS_ALL = """
SELECT date_month,
       COUNT(DISTINCT CASE WHEN event_logo NOT IN ('CHURN','AWAITING PAYMENT') THEN id_company END) AS logos_eop,
       COUNT(DISTINCT CASE WHEN event_logo = 'NEW'         THEN id_company END)                     AS logos_new,
       COUNT(DISTINCT CASE WHEN event_logo = 'RECOVERED'   THEN id_company END)                     AS logos_recov,
       COUNT(DISTINCT CASE WHEN event_logo = 'REACTIVATED' THEN id_company END)                     AS logos_react
FROM dwh_facts.fact_customers_mrr
WHERE date_month <= '{cutoff}-01'
GROUP BY date_month
ORDER BY date_month
"""


_SQL_INVESTMENT = """
SELECT cohortmonth, app_version, segment_type,
       SUM(general_expenses_usd + paid_media_expenses_usd + publicidad_no_web_expenses_usd
           + software_and_tools_expenses_usd + team_expenses_usd + freelance_expenses_usd
           + payroll_expenses_usd + travel_expenses_usd) AS total_investment_usd,
       SUM(paid_media_expenses_usd + publicidad_no_web_expenses_usd) AS paid_media_usd,
       SUM(payroll_expenses_usd + team_expenses_usd + freelance_expenses_usd) AS people_usd,
       SUM(general_expenses_usd + software_and_tools_expenses_usd + travel_expenses_usd) AS other_usd
FROM db_finance.fact_cac_version_segments
WHERE cohortmonth <= '{cutoff}-01'
  AND cohortmonth >= DATEADD(month, -12, '{cutoff}-01')
  AND segment_type IN ('Core', 'Lite')
  AND app_version IN ('colombia', 'mexico', 'republicaDominicana', 'costaRica')
GROUP BY cohortmonth, app_version, segment_type
ORDER BY cohortmonth
"""


# ── Fetch helpers ──────────────────────────────────────────────────────────────
def _run(sql, label):
    print(f"  ⏳ Consultando {label}…")
    res = run_query(sql=sql, database="data_table_bi",
                    cluster_identifier="redshift-cluster-2", db_user="datauser45")
    return res["statement_id"]

def _pages(sid):
    import boto3
    c = boto3.Session(profile_name="alegra", region_name="us-east-1").client("redshift-data")
    while True:
        s = c.describe_statement(Id=sid)["Status"]
        if s == "FINISHED": break
        if s in ("FAILED", "ABORTED"): raise RuntimeError(f"Query {sid} falló")
        time.sleep(2)
    rows, cols, kw = [], None, {"Id": sid}
    while True:
        r = c.get_statement_result(**kw)
        if not cols: cols = [x["label"] for x in r["ColumnMetadata"]]
        for rec in r["Records"]:
            rows.append({c: next(iter(f.values()), None) for c, f in zip(cols, rec)})
        nt = r.get("NextToken")
        if not nt: break
        kw["NextToken"] = nt
    return rows

def load_data(cutoff, refresh=False):
    if not refresh and CACHE_FILE.exists():
        cached = json.loads(CACHE_FILE.read_text())
        if cached.get("version") == CACHE_VERSION and cached.get("cutoff") == cutoff:
            print(f"  📦 Cache del {cached['fetched_at'][:16]}")
            return cached["summary"], cached["logos_all"], cached["country"], cached.get("investment", {})
        print("  🔄 Cache desactualizada, consultando Redshift…")

    sids = {
        "fact_summary": _run(_SQL_FACT_SUMMARY.format(cutoff=cutoff), "fact_customers_mrr (summary)"),
        "logos_all":    _run(_SQL_LOGOS_ALL.format(cutoff=cutoff),    "logos consolidados"),
        "investment":   _run(_SQL_INVESTMENT.format(cutoff=cutoff),   "investment por país"),
    }
    fact_summary_rows = _pages(sids["fact_summary"])
    logos_rows        = _pages(sids["logos_all"])
    investment_rows   = _pages(sids["investment"])

    # ── Aplicar conversión FX (amount_mrr → USD)
    # Países en paises_fx.csv: mrr_usd_* = mrr_local_* / tasa CSV
    # Resto: mrr_usd_* ya viene de amount_usd_mrr (fallback correcto)
    fx = load_fx()
    for row in fact_summary_rows:
        _apply_fx_to_row(row, fx)
    print(f"  💱 FX aplicado — {sorted(_FX_PAISES)} vía CSV · resto usa amount_usd_mrr")

    # ── Aggregate summary by (month, segment) — collapse app_version
    _NUM = ["logos_eop","logos_new","logos_recov","logos_react","logos_churn",
            "mrr_eop","mrr_new","mrr_recov","mrr_react","mrr_churn","mrr_upsell","mrr_downsell"]
    _COL_MAP = {
        "mrr_usd_eop": "mrr_eop", "mrr_usd_new": "mrr_new",
        "mrr_usd_recov": "mrr_recov", "mrr_usd_react": "mrr_react",
        "mrr_usd_churn": "mrr_churn", "mrr_usd_upsell": "mrr_upsell",
        "mrr_usd_downsell": "mrr_downsell",
    }
    grouped = {}
    for r in fact_summary_rows:
        m   = str(r["date_month"])[:7]
        seg = r.get("segment") or "Other"
        key = (m, seg)
        if key not in grouped:
            grouped[key] = {"m": m, "seg": seg, **{k: 0.0 for k in _NUM}}
        for rs_col, py_col in _COL_MAP.items():
            grouped[key][py_col] += float(r.get(rs_col) or 0)
        for col in ["logos_eop","logos_new","logos_recov","logos_react","logos_churn"]:
            grouped[key][col] += float(r.get(col) or 0)

    summary = list(grouped.values())

    # ── Logos consolidated (COUNT DISTINCT cross-segmento — sin doble conteo)
    logos_all = {}
    for r in logos_rows:
        m = str(r["date_month"])[:7]
        logos_all[m] = {
            "logos_eop":   float(r.get("logos_eop")   or 0),
            "logos_new":   float(r.get("logos_new")   or 0),
            "logos_recov": float(r.get("logos_recov") or 0),
            "logos_react": float(r.get("logos_react") or 0),
        }

    # ── Country (month → app_version → segment → metrics) — directo desde fact
    _COUNTRIES = {"colombia", "mexico", "costaRica", "republicaDominicana"}
    country = {}
    for r in fact_summary_rows:
        m   = str(r["date_month"])[:7]
        app = r.get("app_version") or ""
        seg = r.get("segment") or "Other"
        if app not in _COUNTRIES:
            continue
        eop = float(r.get("logos_eop") or 0)
        country.setdefault(m, {}).setdefault(app, {})[seg] = {
            "logos_eop":      eop,
            "logos_eop_fact": eop,   # misma fuente — ya no hay distinción
            "logos_new":      float(r.get("logos_new")      or 0),
            "logos_recov":    float(r.get("logos_recov")    or 0),
            "logos_react":    float(r.get("logos_react")    or 0),
            "logos_churn":    float(r.get("logos_churn")    or 0),
            "mrr_eop":        float(r.get("mrr_usd_eop")    or 0),
            "mrr_new":        float(r.get("mrr_usd_new")    or 0),
            "mrr_recov":      float(r.get("mrr_usd_recov")  or 0),
            "mrr_churn":      float(r.get("mrr_usd_churn")  or 0),
            "mrr_upsell":     float(r.get("mrr_usd_upsell") or 0),
            "mrr_downsell":   float(r.get("mrr_usd_downsell") or 0),
        }

    # ── Investment: {country_key: {segment: {month: {total, paid, people, other}}}}
    investment = {}
    for r in investment_rows:
        app = (r.get("app_version") or "").strip()
        seg = (r.get("segment_type") or "").strip()
        m   = str(r.get("cohortmonth") or "")[:7]  # "2026-02"
        investment.setdefault(app, {}).setdefault(seg, {})[m] = {
            "total":  float(r.get("total_investment_usd") or 0),
            "paid":   float(r.get("paid_media_usd") or 0),
            "people": float(r.get("people_usd") or 0),
            "other":  float(r.get("other_usd") or 0),
        }

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({
        "version":    CACHE_VERSION,
        "cutoff":     cutoff,
        "fetched_at": datetime.now().isoformat(),
        "summary":    summary,
        "logos_all":  logos_all,
        "country":    country,
        "investment": investment,
    }))
    n_country = sum(len(segs) for ms in country.values() for segs in ms.values())
    print(f"  ✅ {len(fact_summary_rows)} filas fact · {len(summary)} summary · {len(logos_all)} meses logos · {n_country} registros país · {len(investment)} países investment")
    return summary, logos_all, country, investment

# ── Metric computation (adapted from dashboard.py) ────────────────────────────
_MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def _month_label(m):   # "2026-02" → "Feb-26"
    return f"{_MONTH_NAMES[int(m[5:])-1]}-{m[2:4]}"

def _prev_m(m):
    y, mo = int(m[:4]), int(m[5:])
    mo -= 1
    if mo == 0: mo, y = 12, y - 1
    return f"{y:04d}-{mo:02d}"

def _prev_q(q_months):
    """Given a list of months for a quarter, return the 3 preceding months."""
    first = q_months[0]
    prev = []
    m = first
    for _ in range(3):
        m = _prev_m(m)
        prev.insert(0, m)
    return prev

def _calc(ms, bym):
    """Compute ARR Walk metrics for a list of months (quarter, month, or YTD)."""
    ms = [m for m in ms if m in bym]
    if not ms: return None
    le  = lambda m: bym.get(m, {}).get("logos_eop",   0)
    me  = lambda m: bym.get(m, {}).get("mrr_eop",     0)

    bop_l   = le(_prev_m(ms[0]));  eop_l = le(ms[-1])
    new_l   = sum(bym[m].get("logos_new",   0) for m in ms)
    recov_l = sum(bym[m].get("logos_recov", 0) for m in ms)
    react_l = sum(bym[m].get("logos_react", 0) for m in ms)
    disc_l  = bop_l + new_l + recov_l - eop_l + react_l
    nc_l    = disc_l - react_l

    bop_m = me(_prev_m(ms[0]));  eop_m = me(ms[-1])
    new_m   = sum(bym[m].get("mrr_new",      0) for m in ms)
    recov_m = sum(bym[m].get("mrr_recov",    0) for m in ms)
    react_m = sum(bym[m].get("mrr_react",    0) for m in ms)
    churn_m = sum(bym[m].get("mrr_churn",    0) for m in ms)
    up_m    = sum(bym[m].get("mrr_upsell",   0) for m in ms)
    down_m  = sum(bym[m].get("mrr_downsell", 0) for m in ms)
    fx_m    = eop_m - (bop_m + new_m + recov_m - churn_m + react_m + up_m + down_m)
    nc_m    = react_m - churn_m   # negativo cuando churn > reactivados (dinero que se va)
    n       = len(ms)

    avg_l        = (bop_l + eop_l) / 2 or 1
    new_pct      = (new_l + recov_l) / avg_l / n
    disc_pct     = disc_l / avg_l / n
    nc_pct       = nc_l   / avg_l / n

    # Churn rate correcto: promedio de tasas mensuales (CHURN - REACTIVATED) / BoP
    _monthly_churn_rates = []
    for mi in ms:
        _bop_mi = le(_prev_m(mi))
        _churn_mi = bym.get(mi, {}).get("logos_churn", 0)
        _react_mi = bym.get(mi, {}).get("logos_react", 0)
        if _bop_mi > 0:
            _monthly_churn_rates.append(max(_churn_mi - _react_mi, 0) / _bop_mi)
    l_churn_pct = sum(_monthly_churn_rates) / len(_monthly_churn_rates) if _monthly_churn_rates else 0

    last   = ms[-1]
    yoy_key = f"{int(last[:4])-1:04d}{last[4:]}"
    l_py = le(yoy_key)
    a_py = me(yoy_key) * 12

    return {
        "l_bop": bop_l, "l_new": new_l, "l_recov": recov_l,
        "l_react": react_l, "l_disc": disc_l, "l_net_churn": nc_l, "l_eop": eop_l,
        "l_eop_py": l_py,
        "l_churn_pct": l_churn_pct,
        "l_new_pct": new_pct, "l_disc_pct": disc_pct, "l_nc_pct": nc_pct,
        "a_bop": bop_m*12, "a_new": new_m*12, "a_recov": recov_m*12,
        "a_react": react_m*12, "a_churn": churn_m*12, "a_net_churn": nc_m*12,
        "a_upsell": up_m*12, "a_down": down_m*12, "a_fx": fx_m*12,
        "a_net_exp": (up_m+down_m+fx_m)*12, "a_eop": eop_m*12,
        "a_net_new": (eop_m - bop_m)*12,
        "a_cc_eop": (eop_m - fx_m)*12,
        "a_eop_py": a_py,
    }

QUARTERS = [
    ("1Q24", ["2024-01","2024-02","2024-03"]),
    ("2Q24", ["2024-04","2024-05","2024-06"]),
    ("3Q24", ["2024-07","2024-08","2024-09"]),
    ("4Q24", ["2024-10","2024-11","2024-12"]),
    ("1Q25", ["2025-01","2025-02","2025-03"]),
    ("2Q25", ["2025-04","2025-05","2025-06"]),
    ("3Q25", ["2025-07","2025-08","2025-09"]),
    ("4Q25", ["2025-10","2025-11","2025-12"]),
    ("1Q26", ["2026-01","2026-02","2026-03"]),
]

def _seg_metrics(bym, all_months, latest_mm):
    q, mo, ytd = {}, {}, {}
    for lbl, ms in QUARTERS:
        r = _calc(ms, bym)
        if r: q[lbl] = r
    for m in all_months:
        r = _calc([m], bym)
        if r: mo[_month_label(m)] = r
    for yr in ["2024", "2025", "2026"]:
        ms = [m for m in all_months if m.startswith(yr) and m[5:] <= latest_mm]
        r  = _calc(ms, bym)
        if r: ytd[yr] = r
    return {"quarters": q, "months": mo, "ytd": ytd}

def build_seg_metrics(summary, logos_all):
    _NUM = ["logos_eop","logos_new","logos_recov","logos_react","logos_churn",
            "mrr_eop","mrr_new","mrr_recov","mrr_react","mrr_churn","mrr_upsell","mrr_downsell"]
    segs_raw = defaultdict(dict)
    for r in summary:
        segs_raw[r["seg"]][r["m"]] = r

    all_months = sorted({m for sd in segs_raw.values() for m in sd})
    segs_raw["all"] = {}
    for m in all_months:
        row = {"m": m, "seg": "all"}
        for k in _NUM:
            row[k] = sum(segs_raw[seg].get(m, {}).get(k, 0.0)
                         for seg in segs_raw if seg != "all")
        if m in logos_all:
            for lk in ["logos_eop","logos_new","logos_recov","logos_react"]:
                row[lk] = logos_all[m][lk]
        segs_raw["all"][m] = row

    latest_mm = max(all_months)[5:] if all_months else "12"

    result = {}
    for seg in ["all", "Core", "Lite"]:
        if segs_raw.get(seg):
            result[seg] = _seg_metrics(segs_raw[seg], all_months, latest_mm)
    return result, segs_raw, all_months, latest_mm

# ── Number formatters ──────────────────────────────────────────────────────────
def _fm(v):
    """USD amount → "$X.XM" for ≥1M, "$XK" for <1M"""
    if v is None: return "N/A"
    if abs(v) >= 1e6:
        return f"${v/1e6:.1f}M"
    return f"${v/1e3:.0f}K"

def _fl(v):
    """Logos → "X.Xk" """
    if v is None: return "N/A"
    return f"{v/1e3:.1f}k"

def _fp(v):
    """Ratio → "+X.X%"  (or "(X.X%)" for negative) """
    if v is None: return "N/A"
    pct = v * 100
    return f"{pct:+.1f}%"

def _pct_delta(curr, prev):
    """Compute % change and return (label, is_positive)."""
    if not prev: return "N/A", True
    delta = (curr - prev) / abs(prev)
    return _fp(delta), delta >= 0

def _arr_pct_delta(curr_dict, prev_dict, key):
    c = curr_dict.get(key, 0)
    p = prev_dict.get(key, 0)
    return _pct_delta(c, p)

# ── SVG Sparkline ──────────────────────────────────────────────────────────────
def _sparkline(values, color="#534AB7", width=44, height=14, stroke=1.5):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return f'<svg class="bf-spark" viewBox="0 0 {width} {height}"></svg>'
    lo, hi = min(vals), max(vals)
    rng = hi - lo or 1
    n   = len(vals)
    pts = []
    for i, v in enumerate(vals):
        x = i / (n - 1) * (width - 2) + 1
        y = height - 2 - (v - lo) / rng * (height - 4)
        pts.append(f"{x:.1f},{y:.1f}")
    return (f'<svg class="bf-spark" viewBox="0 0 {width} {height}">'
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round"/></svg>')

# ── Build metrics.yaml structure ───────────────────────────────────────────────
def build_yaml(seg_metrics, segs_raw, all_months, latest_mm, country_raw, cutoff, investment=None):
    # Latest month label (e.g. "Feb-26") and last quarter label
    latest_m = cutoff  # "2026-02"
    latest_m_lbl = _month_label(latest_m)  # "Feb-26"

    # Determine which quarter cutoff falls in
    def _quarter_of(m):
        for lbl, ms in QUARTERS:
            if m in ms: return lbl
        return QUARTERS[-1][0]
    latest_q_lbl = _quarter_of(latest_m)

    # ── Prior month & prior year month
    prev_m  = _prev_m(latest_m)
    prev_m_lbl = _month_label(prev_m)
    prev_yr = f"{int(latest_m[:4])-1}{latest_m[4:]}"

    def _mo(seg, m=latest_m_lbl):
        return seg_metrics.get(seg, {}).get("months", {}).get(m, {})

    def _mo_prev(seg):
        return seg_metrics.get(seg, {}).get("months", {}).get(prev_m_lbl, {})

    def _mo_py(seg):
        py_lbl = _month_label(prev_yr)
        return seg_metrics.get(seg, {}).get("months", {}).get(py_lbl, {})

    def _q(seg, q=latest_q_lbl):
        return seg_metrics.get(seg, {}).get("quarters", {}).get(q, {})

    def _q_prev(seg):
        # Previous quarter label
        idx = next((i for i, (l, _) in enumerate(QUARTERS) if l == latest_q_lbl), -1)
        if idx <= 0: return {}
        prev_q_lbl = QUARTERS[idx-1][0]
        return seg_metrics.get(seg, {}).get("quarters", {}).get(prev_q_lbl, {})

    # ── Global KPIs (slide 1 — Key Summary)
    all_m    = _mo("all")
    all_m_pv = _mo_prev("all")
    all_m_py = _mo_py("all")

    def _delta_m(key):  return _pct_delta(all_m.get(key,0), all_m_pv.get(key,0))
    def _delta_y(key):  return _pct_delta(all_m.get(key,0), all_m_py.get(key,0))

    arr_mom_str, arr_mom_pos      = _delta_m("a_eop")
    arr_yoy_str, arr_yoy_pos      = _delta_y("a_eop")
    new_mrr_mom_str, new_mrr_mom_pos = _delta_m("a_new")
    new_mrr_yoy_str, new_mrr_yoy_pos = _delta_y("a_new")
    new_logos_mom_str, new_logos_mom_pos = _delta_m("l_new")
    new_logos_yoy_str, new_logos_yoy_pos = _delta_y("l_new")

    # ── Quarter-end detection y QoQ deltas ───────────────────────────────────
    is_quarter_end = int(latest_m[5:]) in (3, 6, 9, 12)
    all_q     = _q("all")
    all_q_pv  = _q_prev("all")
    arr_qoq_str,       arr_qoq_pos       = _pct_delta(all_q.get("a_eop",0), all_q_pv.get("a_eop",0))
    new_mrr_qoq_str,   new_mrr_qoq_pos   = _pct_delta(all_q.get("a_new",0), all_q_pv.get("a_new",0))
    new_logos_qoq_str, new_logos_qoq_pos = _pct_delta(all_q.get("l_new",0), all_q_pv.get("l_new",0))
    # Label del quarter previo, e.g. "Q4 2025"
    idx_q = next((i for i,(l,_) in enumerate(QUARTERS) if l==latest_q_lbl), -1)
    prev_q_label = QUARTERS[idx_q-1][0] if idx_q > 0 else "—"

    # ── ARR Walk products (Core + Lite)  ─────────────────────────────────────
    _PRODUCT_CFG = [
        {"seg": "Core", "id": "core", "name": "Core", "color": "#534AB7"},
        {"seg": "Lite", "id": "lite", "name": "Lite", "color": "#1D9E75"},
    ]

    # Build quarterly chart arrays for each product
    available_qs = [lbl for lbl, ms in QUARTERS
                    if _calc(ms, segs_raw.get("Core", {}))]

    products = []
    for cfg in _PRODUCT_CFG:
        seg      = cfg["seg"]
        q_data   = seg_metrics.get(seg, {}).get("quarters", {})
        q_prev_d = _q_prev(seg)
        q_cur_d  = _q(seg)
        q_py_key = _month_label(prev_yr)
        q_py_d   = seg_metrics.get(seg, {}).get("months", {}).get(q_py_key, {})

        if not q_cur_d:
            continue  # segment not present

        # Chart arrays — all available quarters
        chart_qs = [lbl for lbl, _ in QUARTERS if lbl in q_data]
        arr_new_rec    = [q_data[q].get("a_new",   0)/1e6 + q_data[q].get("a_recov", 0)/1e6 for q in chart_qs]
        arr_expansion  = [max(q_data[q].get("a_upsell",  0)/1e6, 0) for q in chart_qs]
        arr_churn      = [max(q_data[q].get("a_churn",   0)/1e6, 0) for q in chart_qs]
        arr_contraction= [max(q_data[q].get("a_down",    0)/1e6, 0) for q in chart_qs]
        arr_net_new    = [q_data[q].get("a_net_new", 0)/1e6 for q in chart_qs]
        logos_new_ch   = [q_data[q].get("l_new",   0) + q_data[q].get("l_recov", 0) for q in chart_qs]
        logos_exp_ch   = [0] * len(chart_qs)
        logos_churn_ch = [q_data[q].get("l_disc",  0) for q in chart_qs]
        logos_down_ch  = [0] * len(chart_qs)
        y_max          = max((max(arr_new_rec + arr_expansion) if arr_new_rec else 0),
                             (max(arr_churn + arr_contraction) if arr_churn else 0)) * 1.25 or 1

        # q_cards (BoP/EoP per quarter for last 5 quarters)
        q_cards = []
        bym_seg = segs_raw.get(seg, {})
        for q_lbl, ms in QUARTERS[-5:]:
            if not any(m in bym_seg for m in ms): continue
            bop_m_key = _prev_m(ms[0])
            bop_mrr   = bym_seg.get(bop_m_key, {}).get("mrr_eop", 0)
            bop_logos = bym_seg.get(bop_m_key, {}).get("logos_eop", 0)
            eop_m_key = ms[-1]
            eop_mrr   = bym_seg.get(eop_m_key, {}).get("mrr_eop", 0)
            eop_logos = bym_seg.get(eop_m_key, {}).get("logos_eop", 0)
            q_cards.append({
                "label":    q_lbl,
                "bopArr":   _fm(bop_mrr * 12),
                "bopLogos": round(bop_logos / 1e3, 2),
                "eopArr":   _fm(eop_mrr * 12),
                "eopLogos": round(eop_logos / 1e3, 2),
            })

        # Key headline metrics
        logos_yoy_str, logos_yoy_pos = _pct_delta(q_cur_d.get("l_eop",0), q_cur_d.get("l_eop_py",0))
        logos_qoq_str, logos_qoq_pos = _pct_delta(q_cur_d.get("l_eop",0), q_prev_d.get("l_eop",0))
        arr_yoy_s,  arr_yoy_p   = _pct_delta(q_cur_d.get("a_eop",0), q_cur_d.get("a_eop_py",0))
        arr_qoq_s,  arr_qoq_p   = _pct_delta(q_cur_d.get("a_eop",0), q_prev_d.get("a_eop",0))
        churn_qoq_s, churn_qoq_p = _pct_delta(q_cur_d.get("a_churn",0), q_prev_d.get("a_churn",0))
        churn_yoy_s, churn_yoy_p = _pct_delta(q_cur_d.get("a_churn",0), q_cur_d.get("a_eop_py",0))
        nn_qoq_s,   nn_qoq_p    = _pct_delta(q_cur_d.get("a_net_new",0), q_prev_d.get("a_net_new",0))

        prev_q_nn = q_prev_d.get("a_net_new", 0)
        prev_q_lbl_str = QUARTERS[max(0, next((i for i,(l,_) in enumerate(QUARTERS) if l==latest_q_lbl), 0)-1)][0]

        products.append({
            "id":           cfg["id"],
            "name":         cfg["name"],
            "color":        cfg["color"],
            "action_title": f"ARR Walk {cfg['name']} — {latest_q_lbl}",
            # KPI cards
            "arr_eop":      _fm(q_cur_d.get("a_eop", 0)),
            "arr_yoy":      arr_yoy_s,
            "arr_qoq":      arr_qoq_s,
            "logos_eop":    _fl(q_cur_d.get("l_eop", 0)),
            "logos_yoy":    logos_yoy_str,
            "logos_qoq":    logos_qoq_str,
            "churn_arr":    _fm(q_cur_d.get("a_churn", 0)),
            "churn_qoq":    churn_qoq_s,
            "churn_yoy":    churn_yoy_s,
            "net_new_arr":  _fm(q_cur_d.get("a_net_new", 0)),
            "net_new_vs":   f"vs {_fm(prev_q_nn)} en {prev_q_lbl_str}",
            "net_new_qoq":  nn_qoq_s,
            # Chart data
            "quarters":        chart_qs,
            "arr_new_rec":     arr_new_rec,
            "arr_expansion":   arr_expansion,
            "arr_churn":       arr_churn,
            "arr_contraction": arr_contraction,
            "arr_net_new":     arr_net_new,
            "logos_new":       logos_new_ch,
            "logos_expansion": logos_exp_ch,
            "logos_churn":     logos_churn_ch,
            "logos_contraction": logos_down_ch,
            "q_cards":         q_cards,
            "y_max":           round(y_max, 2),
            # Asks — editorial content; merged by generate.py from editorial/arr_walk.yaml
            "asks": [],
        })

    # ── Country butterfly ─────────────────────────────────────────────────────
    COUNTRY_CFG = [
        {"key": "colombia",            "team": "CO", "name": "Colombia",         "flag": "🇨🇴"},
        {"key": "mexico",              "team": "MX", "name": "México",           "flag": "🇲🇽"},
        {"key": "republicaDominicana", "team": "DR", "name": "Rep. Dominicana",  "flag": "🇩🇴"},
        {"key": "costaRica",           "team": "CR", "name": "Costa Rica",       "flag": "🇨🇷"},
    ]

    # Build per-country time series from country_raw: month → team → seg → metrics
    def _country_ts(team, seg, key, months=12):
        """Return list of values for the last `months` months (chronological)."""
        recent = sorted(country_raw.keys())[-months:]
        return [country_raw.get(m, {}).get(team, {}).get(seg, {}).get(key, 0) for m in recent]

    def _country_m(team, seg, m=latest_m):
        return country_raw.get(m, {}).get(team, {}).get(seg, {})

    def _country_pm(team, seg):
        return country_raw.get(prev_m, {}).get(team, {}).get(seg, {})

    def _country_pym(team, seg):
        return country_raw.get(prev_yr, {}).get(team, {}).get(seg, {})

    CORE_COLOR = "#534AB7"
    LITE_COLOR = "#1D9E75"

    # ── Payback por país desde CSV — serie de tiempo completa ──────────────────
    # payback_by_country: {country_key: {seg: {month: val}}}
    payback_by_country = {}
    if PAYBACK_FILE.exists():
        with open(PAYBACK_FILE, newline="", encoding="utf-8") as _f:
            for _r in csv.DictReader(_f):
                if _r.get("Type", "").strip() == "Todos":
                    continue
                _ck  = _r.get("Type", "").strip()     # e.g. "colombia"
                _seg = _r.get("Segment", "").strip()  # "Core" / "Lite"
                _val = float(_r.get("valor", 0) or 0)
                # fecha "M/1/YYYY" → "YYYY-MM"
                _fd  = _r.get("fecha", "").strip()
                # Soporta tanto "YYYY-MM" como "M/D/YYYY"
                try:
                    if "-" in _fd:
                        _mk = _fd[:7]  # "2026-03"
                    else:
                        _mk = datetime.strptime(_fd, "%m/%d/%Y").strftime("%Y-%m")
                except ValueError:
                    continue
                payback_by_country.setdefault(_ck, {}).setdefault(_seg, {})[_mk] = _val

    # Q months para lógica de cierre de Q en países
    _cur_q_ms  = next((ms for _, ms in QUARTERS if latest_m in ms), [latest_m])
    _prev_q_ms = next((QUARTERS[i-1][1] for i, (_, ms) in enumerate(QUARTERS)
                       if latest_m in ms and i > 0), [latest_m])
    # Mismo Q del año anterior (YoY para Q)
    _cur_q_ms_py = [f"{int(m[:4])-1}{m[4:]}" for m in _cur_q_ms]

    countries = []
    for cfg in COUNTRY_CFG:
        tm  = cfg["team"]   # display code: CO/MX/DR/CR
        key = cfg["key"]    # lookup key in country_raw: colombia/mexico/...

        # Skip countries with no data
        if not country_raw.get(latest_m, {}).get(key):
            continue

        def _val_cm(seg, k=key):  return _country_m(k, seg)
        def _val_pm(seg, k=key):  return _country_pm(k, seg)
        def _val_pym(seg, k=key): return _country_pym(k, seg)

        def _seg_kpi(seg, color):
            cur  = _val_cm(seg)
            prev = _val_pm(seg)
            py   = _val_pym(seg)
            arr_cur  = cur.get("mrr_eop", 0) * 12
            arr_prev = prev.get("mrr_eop", 0) * 12
            arr_py   = py.get("mrr_eop", 0) * 12
            mom_s, mom_p = _pct_delta(arr_cur, arr_prev)
            yoy_s, yoy_p = _pct_delta(arr_cur, arr_py)
            return {
                "arr":           _fm(arr_cur),
                "arr_mom":       mom_s,
                "arr_mom_positive": mom_p,
                "arr_yoy":       yoy_s,
                "arr_yoy_positive": yoy_p,
            }

        def _butterfly_row(metric_name, key_fn, fmt_fn, color_c, color_l, neg_is_bad=True):
            def _side(seg, color, neg_is_bad=neg_is_bad):
                cur_v  = key_fn(_val_cm(seg))
                prev_v = key_fn(_val_pm(seg))
                py_v   = key_fn(_val_pym(seg))
                mom_s, mom_p = _pct_delta(cur_v, prev_v)
                yoy_s, yoy_p = _pct_delta(cur_v, py_v)
                ts    = _country_ts(tm, seg, key_fn.__name__ if hasattr(key_fn,'__name__') else "mrr_eop", 12)
                return {
                    "val":          fmt_fn(cur_v),
                    "val_negative": (cur_v < 0) if neg_is_bad else False,
                    "mom":          mom_s,
                    "mom_positive": mom_p,
                    "yoy":          yoy_s,
                    "yoy_positive": yoy_p,
                    "sparkline_svg": _sparkline(ts, color),
                }
            return {
                "metric_name": metric_name,
                "core":        _side("Core", color_c),
                "lite":        _side("Lite", color_l),
            }

        _recent12 = sorted(country_raw.keys())[-12:]

        def _cd(seg, m):
            return country_raw.get(m, {}).get(key, {}).get(seg, {})

        def _row(name, fn, fmt):
            """Row where fn(month_dict) gives the value."""
            def _side(seg, color):
                v     = fn(_val_cm(seg))
                v_pm  = fn(_val_pm(seg))
                v_py  = fn(_val_pym(seg))
                mom_s, mom_p = _pct_delta(v, v_pm)
                yoy_s, yoy_p = _pct_delta(v, v_py)
                return {
                    "val": fmt(v), "val_negative": v < 0,
                    "mom": mom_s, "mom_positive": mom_p,
                    "yoy": yoy_s, "yoy_positive": yoy_p,
                    "sparkline_svg": _sparkline([fn(_cd(seg, m)) for m in _recent12], color),
                }
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        def _row2(name, fn, fmt):
            """Row where fn(seg, m) gives the value — for metrics needing two months."""
            def _side(seg, color):
                v     = fn(seg, latest_m)
                v_pm  = fn(seg, prev_m)
                v_py  = fn(seg, prev_yr)
                mom_s, mom_p = _pct_delta(v, v_pm)
                yoy_s, yoy_p = _pct_delta(v, v_py)
                return {
                    "val": fmt(v), "val_negative": v < 0,
                    "mom": mom_s, "mom_positive": mom_p,
                    "yoy": yoy_s, "yoy_positive": yoy_p,
                    "sparkline_svg": _sparkline([fn(seg, m) for m in _recent12], color),
                }
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        def _na_row(name):
            _ns = {"val": "N/A", "val_negative": False, "mom": "—", "mom_positive": True,
                   "yoy": "—", "yoy_positive": True, "sparkline_svg": ""}
            return {"metric_name": name, "core": dict(_ns), "lite": dict(_ns)}

        # Net New ARR: mes = EoP - BoP del mes; Q = EoP último mes Q - BoP primer mes Q
        def _net_new_arr(seg, m):
            m_prev = _prev_m(m)
            return (_cd(seg, m).get("mrr_eop", 0) - _cd(seg, m_prev).get("mrr_eop", 0)) * 12

        def _net_new_arr_q(seg, q_ms):
            eop = _cd(seg, q_ms[-1]).get("mrr_eop", 0)
            bop = _cd(seg, _prev_m(q_ms[0])).get("mrr_eop", 0)
            return (eop - bop) * 12

        # Logos Growth: mes = EoP - BoP del mes; Q = EoP último mes Q - BoP primer mes Q
        def _logos_growth(seg, m):
            return _cd(seg, m).get("logos_eop", 0) - _cd(seg, _prev_m(m)).get("logos_eop", 0)

        def _logos_growth_q(seg, q_ms):
            return _cd(seg, q_ms[-1]).get("logos_eop", 0) - _cd(seg, _prev_m(q_ms[0])).get("logos_eop", 0)

        # ARPA = ARR EoP / Logos EoP
        def _arpa(seg, m):
            l = _cd(seg, m).get("logos_eop", 0)
            return _cd(seg, m).get("mrr_eop", 0) / l if l else 0

        # Churn Rate % mensual = (CHURN - REACTIVATED) / BoP * 100
        def _churn_rate(seg, m):
            bop   = _cd(seg, _prev_m(m)).get("logos_eop_fact", 0)
            churn = _cd(seg, m).get("logos_churn", 0)
            react = _cd(seg, m).get("logos_react", 0)
            return (max(churn - react, 0) / bop * 100) if bop else 0

        # ── Helpers Q-aware (solo activos cuando is_quarter_end) ──────────────
        def _q_sum_field(seg, field, q_ms):
            return sum(_cd(seg, m).get(field, 0) for m in q_ms)

        def _q_churn_avg(seg, q_ms):
            rates = [_churn_rate(seg, m) for m in q_ms]
            valid = [r for r in rates if r > 0]
            return sum(valid) / len(valid) if valid else 0

        def _row_q(name, month_fn, q_field, fmt):
            """Row Q-aware: suma del Q cuando is_quarter_end, mes actual si no."""
            def _side(seg, color):
                if is_quarter_end:
                    v     = _q_sum_field(seg, q_field, _cur_q_ms)
                    v_pm  = _q_sum_field(seg, q_field, _prev_q_ms)
                    v_py  = _q_sum_field(seg, q_field, _cur_q_ms_py)
                else:
                    v     = month_fn(_val_cm(seg))
                    v_pm  = month_fn(_val_pm(seg))
                    v_py  = month_fn(_val_pym(seg))
                mom_s, mom_p = _pct_delta(v, v_pm)
                yoy_s, yoy_p = _pct_delta(v, v_py)
                return {
                    "val": fmt(v), "val_negative": v < 0,
                    "mom": mom_s, "mom_positive": mom_p,
                    "yoy": yoy_s, "yoy_positive": yoy_p,
                    "sparkline_svg": _sparkline([month_fn(_cd(seg, m)) for m in _recent12], color),
                }
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        def _churn_row_q(name, fmt):
            """Churn Rate Q-aware: promedio de tasas del Q."""
            def _side(seg, color):
                if is_quarter_end:
                    v    = _q_churn_avg(seg, _cur_q_ms)
                    v_pm = _q_churn_avg(seg, _prev_q_ms)
                    v_py = _q_churn_avg(seg, _cur_q_ms_py)
                else:
                    v    = _churn_rate(seg, latest_m)
                    v_pm = _churn_rate(seg, prev_m)
                    v_py = _churn_rate(seg, prev_yr)
                mom_s, mom_p = _pct_delta(v, v_pm)
                yoy_s, yoy_p = _pct_delta(v, v_py)
                return {
                    "val": fmt(v), "val_negative": v < 0,
                    "mom": mom_s, "mom_positive": mom_p,
                    "yoy": yoy_s, "yoy_positive": yoy_p,
                    "sparkline_svg": _sparkline([_churn_rate(seg, m) for m in _recent12], color),
                }
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        def _inv_row_q(name):
            """Investment Q-aware: suma del Q."""
            def _side(seg, color):
                if is_quarter_end:
                    v    = sum((_inv_v(seg, m) or 0) for m in _cur_q_ms)
                    v_pm = sum((_inv_v(seg, m) or 0) for m in _prev_q_ms)
                    v_py = sum((_inv_v(seg, m) or 0) for m in _cur_q_ms_py)
                else:
                    v    = _inv_v(seg, latest_m)
                    v_pm = _inv_v(seg, prev_m)
                    v_py = _inv_v(seg, prev_yr)
                if v is None:
                    return _na_side()
                mom_s, mom_p = _pct_delta(v, v_pm) if v_pm is not None else ("—", True)
                yoy_s, yoy_p = _pct_delta(v, v_py) if v_py is not None else ("—", True)
                ts = [_inv_v(seg, m) or 0 for m in _recent12]
                return {"val": _fm(v), "val_negative": False,
                        "mom": mom_s, "mom_positive": mom_p,
                        "yoy": yoy_s, "yoy_positive": yoy_p,
                        "sparkline_svg": _sparkline(ts, color)}
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        def _cac_row_q(name):
            """CAC Q-aware: Investment_Q / New Logos_Q."""
            def _side(seg, color):
                if is_quarter_end:
                    inv  = sum((_inv_v(seg, m) or 0) for m in _cur_q_ms)
                    nl   = _q_sum_field(seg, "logos_new", _cur_q_ms)
                    v    = inv / nl if nl > 0 else None
                    inv_p = sum((_inv_v(seg, m) or 0) for m in _prev_q_ms)
                    nl_p  = _q_sum_field(seg, "logos_new", _prev_q_ms)
                    v_pm  = inv_p / nl_p if nl_p > 0 else None
                    inv_py = sum((_inv_v(seg, m) or 0) for m in _cur_q_ms_py)
                    nl_py  = _q_sum_field(seg, "logos_new", _cur_q_ms_py)
                    v_py   = inv_py / nl_py if nl_py > 0 else None
                else:
                    v    = _cac_v(seg, latest_m)
                    v_pm = _cac_v(seg, prev_m)
                    v_py = _cac_v(seg, prev_yr)
                if v is None:
                    return _na_side()
                mom_s, mom_p = _pct_delta(v, v_pm) if v_pm is not None else ("—", True)
                yoy_s, yoy_p = _pct_delta(v, v_py) if v_py is not None else ("—", True)
                ts = [(_cac_v(seg, m) or 0) for m in _recent12]
                return {"val": f"${v:,.0f}", "val_negative": False,
                        "mom": mom_s, "mom_positive": mom_p,
                        "yoy": yoy_s, "yoy_positive": yoy_p,
                        "sparkline_svg": _sparkline(ts, color)}
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        # Payback por país desde CSV — serie de tiempo
        def _pb_v(seg, m):
            return payback_by_country.get(key, {}).get(seg, {}).get(m)

        def _payback_row(name):
            def _pb_avg(seg, q_ms):
                vals = [_pb_v(seg, m) for m in q_ms if _pb_v(seg, m) is not None]
                return sum(vals) / len(vals) if vals else None
            def _side(seg, color):
                if is_quarter_end:
                    v    = _pb_avg(seg, _cur_q_ms)
                    v_pm = _pb_avg(seg, _prev_q_ms)
                    v_py = _pb_avg(seg, _cur_q_ms_py)
                else:
                    v    = _pb_v(seg, latest_m)
                    v_pm = _pb_v(seg, prev_m)
                    v_py = _pb_v(seg, prev_yr)
                if v is None:
                    return _na_side()
                mom_s, mom_p = _pct_delta(v, v_pm) if v_pm is not None else ("—", True)
                yoy_s, yoy_p = _pct_delta(v, v_py) if v_py is not None else ("—", True)
                ts = [_pb_v(seg, m) or 0 for m in _recent12]
                return {"val": f"{v:.1f} mo", "val_negative": False,
                        "mom": mom_s, "mom_positive": mom_p,
                        "yoy": yoy_s, "yoy_positive": yoy_p,
                        "sparkline_svg": _sparkline(ts, color)}
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        # Investment y CAC — series de tiempo {seg: {month: usd}}
        inv_ts = (investment or {}).get(key, {})

        def _inv_v(seg, m):
            rec = inv_ts.get(seg, {}).get(m)
            return rec["total"] if rec else None

        def _cac_v(seg, m):
            inv = _inv_v(seg, m)
            nl  = _cd(seg, m).get("logos_new", 0)
            return inv / nl if (inv is not None and nl > 0) else None

        def _na_side():
            return {"val": "N/A", "val_negative": False, "mom": "—",
                    "mom_positive": True, "yoy": "—", "yoy_positive": True,
                    "sparkline_svg": ""}

        def _ts_side(seg, color, val_fn, fmt_fn, neg_is_bad=False):
            v    = val_fn(seg, latest_m)
            v_pm = val_fn(seg, prev_m)
            v_py = val_fn(seg, prev_yr)
            if v is None:
                return _na_side()
            mom_s, mom_p = _pct_delta(v, v_pm) if v_pm is not None else ("—", True)
            yoy_s, yoy_p = _pct_delta(v, v_py) if v_py is not None else ("—", True)
            ts = [val_fn(seg, m) or 0 for m in _recent12]
            return {"val": fmt_fn(v), "val_negative": (v < 0) if neg_is_bad else False,
                    "mom": mom_s, "mom_positive": mom_p,
                    "yoy": yoy_s, "yoy_positive": yoy_p,
                    "sparkline_svg": _sparkline(ts, color)}

        def _inv_row(name):
            return {"metric_name": name,
                    "core": _ts_side("Core", CORE_COLOR, _inv_v, _fm),
                    "lite": _ts_side("Lite", LITE_COLOR, _inv_v, _fm)}

        def _cac_row(name):
            return {"metric_name": name,
                    "core": _ts_side("Core", CORE_COLOR, _cac_v, lambda v: f"${v:,.0f}"),
                    "lite": _ts_side("Lite", LITE_COLOR, _cac_v, lambda v: f"${v:,.0f}")}

        # Net New ARR Q-aware
        def _net_new_arr_row(name):
            def _side(seg, color):
                if is_quarter_end:
                    v    = _net_new_arr_q(seg, _cur_q_ms)
                    v_pm = _net_new_arr_q(seg, _prev_q_ms)
                    v_py = _net_new_arr_q(seg, _cur_q_ms_py)
                else:
                    v    = _net_new_arr(seg, latest_m)
                    v_pm = _net_new_arr(seg, prev_m)
                    v_py = _net_new_arr(seg, prev_yr)
                mom_s, mom_p = _pct_delta(v, v_pm)
                yoy_s, yoy_p = _pct_delta(v, v_py)
                return {"val": _fm(v), "val_negative": v < 0,
                        "mom": mom_s, "mom_positive": mom_p,
                        "yoy": yoy_s, "yoy_positive": yoy_p,
                        "sparkline_svg": _sparkline([_net_new_arr(seg, m) for m in _recent12], color)}
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        # Logos Growth Q-aware
        def _logos_growth_row(name):
            fmt = lambda v: f"+{int(v):,}" if v >= 0 else f"({int(abs(v)):,})"
            def _side(seg, color):
                if is_quarter_end:
                    v    = _logos_growth_q(seg, _cur_q_ms)
                    v_pm = _logos_growth_q(seg, _prev_q_ms)
                    v_py = _logos_growth_q(seg, _cur_q_ms_py)
                else:
                    v    = _logos_growth(seg, latest_m)
                    v_pm = _logos_growth(seg, prev_m)
                    v_py = _logos_growth(seg, prev_yr)
                mom_s, mom_p = _pct_delta(v, v_pm)
                yoy_s, yoy_p = _pct_delta(v, v_py)
                return {"val": fmt(v), "val_negative": v < 0,
                        "mom": mom_s, "mom_positive": mom_p,
                        "yoy": yoy_s, "yoy_positive": yoy_p,
                        "sparkline_svg": _sparkline([_logos_growth(seg, m) for m in _recent12], color)}
            return {"metric_name": name, "core": _side("Core", CORE_COLOR), "lite": _side("Lite", LITE_COLOR)}

        butterfly_rows = [
            _inv_row_q("Investment"),
            _net_new_arr_row("Net New ARR"),
            _logos_growth_row("Logos Growth"),
            _row_q("New Logos",       lambda d: d.get("logos_new", 0), "logos_new", lambda v: f"{int(v):,}"),
            _row_q("New ARR",         lambda d: (d.get("mrr_new", 0) + d.get("mrr_recov", 0)) * 12, "mrr_new", lambda v: _fm(v * 12)),
            _row2("ARPA",             _arpa,          lambda v: f"${v:,.0f}"),
            _cac_row_q("CAC"),
            _churn_row_q("Churn Rate",                lambda v: f"{v:.1f}%"),
            _payback_row("Payback"),
        ]

        countries.append({
            "team":         tm,
            "name":         cfg["name"],
            "flag":         cfg["flag"],
            "action_title": f"{cfg['flag']} {cfg['name']} — Core vs Lite Performance",
            "core":         _seg_kpi("Core", CORE_COLOR),
            "lite":         _seg_kpi("Lite", LITE_COLOR),
            "butterfly_rows": butterfly_rows,
        })

    # ── Global Country Performance (TODOS los países — usa segs_raw global) ──
    # segs_raw["Core"/"Lite"][m] = datos globales de fact_customers_mrr sin filtro de país

    def _graw(seg, m):
        return segs_raw.get(seg, {}).get(m, {})

    def _gm(seg):   return _graw(seg, latest_m)
    def _gpm(seg):  return _graw(seg, prev_m)
    def _gpym(seg): return _graw(seg, prev_yr)

    def _g_net_new_arr(seg, m):
        return (_graw(seg, m).get("mrr_eop", 0) - _graw(seg, _prev_m(m)).get("mrr_eop", 0)) * 12

    def _g_net_new_arr_q(seg, q_ms):
        return (_graw(seg, q_ms[-1]).get("mrr_eop", 0) - _graw(seg, _prev_m(q_ms[0])).get("mrr_eop", 0)) * 12

    def _g_logos_growth(seg, m):
        return _graw(seg, m).get("logos_eop", 0) - _graw(seg, _prev_m(m)).get("logos_eop", 0)

    def _g_logos_growth_q(seg, q_ms):
        return _graw(seg, q_ms[-1]).get("logos_eop", 0) - _graw(seg, _prev_m(q_ms[0])).get("logos_eop", 0)

    def _g_arpa(seg, m):
        d = _graw(seg, m)
        l = d.get("logos_eop", 0)
        return d.get("mrr_eop", 0) / l if l else 0

    def _g_churn(seg, m):
        bop   = _graw(seg, _prev_m(m)).get("logos_eop", 0)
        churn = _graw(seg, m).get("logos_churn", 0)
        react = _graw(seg, m).get("logos_react", 0)
        return (max(churn - react, 0) / bop * 100) if bop else 0

    def _g_churn_avg_q(seg, q_ms):
        rates = [_g_churn(seg, m) for m in q_ms]
        valid = [r for r in rates if r > 0]
        return sum(valid) / len(valid) if valid else 0

    def _g_q_sum(seg, field, q_ms):
        return sum(_graw(seg, m).get(field, 0) for m in q_ms)

    def _g_inv(seg, m, field="total"):
        vals = [country_inv.get(seg, {}).get(m, {}).get(field) for country_inv in investment.values()]
        valid = [v for v in vals if v is not None]
        return sum(valid) if valid else None

    def _g_inv_paid(seg, m):   return _g_inv(seg, m, "paid")
    def _g_inv_people(seg, m): return _g_inv(seg, m, "people")
    def _g_inv_other(seg, m):  return _g_inv(seg, m, "other")

    def _g_cac(seg, m):
        inv = _g_inv(seg, m)
        nl  = _graw(seg, m).get("logos_new", 0)
        return inv / nl if (inv is not None and nl > 0) else None

    _g_na = {"val": "N/A", "val_negative": False, "mom": "—", "mom_positive": True,
             "yoy": "—", "yoy_positive": True, "sparkline_svg": ""}

    def _g_side(seg, v, v_pm, v_py, fmt_fn, neg_is_bad=True):
        if v is None:
            return dict(_g_na)
        mom_s, mom_p = _pct_delta(v, v_pm) if v_pm is not None else ("—", True)
        yoy_s, yoy_p = _pct_delta(v, v_py) if v_py is not None else ("—", True)
        return {"val": fmt_fn(v), "val_negative": (v < 0) if neg_is_bad else False,
                "mom": mom_s, "mom_positive": mom_p,
                "yoy": yoy_s, "yoy_positive": yoy_p, "sparkline_svg": ""}

    def _g_make(name, core_side, lite_side):
        return {"metric_name": name, "core": core_side, "lite": lite_side}

    def _g_inv_row_q():
        def _s(seg):
            if is_quarter_end:
                v, vp, vy = (sum((_g_inv(seg,m) or 0) for m in ms) for ms in [_cur_q_ms, _prev_q_ms, _cur_q_ms_py])
            else:
                v, vp, vy = _g_inv(seg,latest_m), _g_inv(seg,prev_m), _g_inv(seg,prev_yr)
            return _g_side(seg, v, vp, vy, _fm, neg_is_bad=False)
        return _g_make("Investment", _s("Core"), _s("Lite"))

    def _g_nna_row():
        def _s(seg):
            if is_quarter_end:
                v, vp, vy = _g_net_new_arr_q(seg,_cur_q_ms), _g_net_new_arr_q(seg,_prev_q_ms), _g_net_new_arr_q(seg,_cur_q_ms_py)
            else:
                v, vp, vy = _g_net_new_arr(seg,latest_m), _g_net_new_arr(seg,prev_m), _g_net_new_arr(seg,prev_yr)
            return _g_side(seg, v, vp, vy, _fm, neg_is_bad=True)
        return _g_make("Net New ARR", _s("Core"), _s("Lite"))

    def _g_logos_growth_row():
        fmt = lambda v: f"+{int(v):,}" if v >= 0 else f"({int(abs(v)):,})"
        def _s(seg):
            if is_quarter_end:
                v, vp, vy = _g_logos_growth_q(seg,_cur_q_ms), _g_logos_growth_q(seg,_prev_q_ms), _g_logos_growth_q(seg,_cur_q_ms_py)
            else:
                v, vp, vy = _g_logos_growth(seg,latest_m), _g_logos_growth(seg,prev_m), _g_logos_growth(seg,prev_yr)
            return _g_side(seg, v, vp, vy, fmt, neg_is_bad=True)
        return _g_make("Logos Growth", _s("Core"), _s("Lite"))

    def _g_row_q(name, m_fn, q_field, fmt_fn):
        def _s(seg):
            if is_quarter_end:
                v, vp, vy = (_g_q_sum(seg, q_field, ms) for ms in [_cur_q_ms, _prev_q_ms, _cur_q_ms_py])
            else:
                v, vp, vy = m_fn(_gm(seg)), m_fn(_gpm(seg)), m_fn(_gpym(seg))
            return _g_side(seg, v, vp, vy, fmt_fn, neg_is_bad=True)
        return _g_make(name, _s("Core"), _s("Lite"))

    def _g_arpa_row():
        def _s(seg):
            v, vp, vy = _g_arpa(seg,latest_m), _g_arpa(seg,prev_m), _g_arpa(seg,prev_yr)
            return _g_side(seg, v, vp, vy, lambda v: f"${v:,.0f}", neg_is_bad=False)
        return _g_make("ARPA", _s("Core"), _s("Lite"))

    def _g_cac_row_q():
        def _s(seg):
            if is_quarter_end:
                def _cac_q(ms):
                    inv = sum((_g_inv(seg,m) or 0) for m in ms)
                    nl  = _g_q_sum(seg, "logos_new", ms)
                    return inv / nl if nl > 0 else None
                v, vp, vy = _cac_q(_cur_q_ms), _cac_q(_prev_q_ms), _cac_q(_cur_q_ms_py)
            else:
                v, vp, vy = _g_cac(seg,latest_m), _g_cac(seg,prev_m), _g_cac(seg,prev_yr)
            return _g_side(seg, v, vp, vy, lambda v: f"${v:,.0f}", neg_is_bad=False)
        return _g_make("CAC", _s("Core"), _s("Lite"))

    def _g_churn_row_q():
        def _s(seg):
            if is_quarter_end:
                v, vp, vy = _g_churn_avg_q(seg,_cur_q_ms), _g_churn_avg_q(seg,_prev_q_ms), _g_churn_avg_q(seg,_cur_q_ms_py)
            else:
                v, vp, vy = _g_churn(seg,latest_m), _g_churn(seg,prev_m), _g_churn(seg,prev_yr)
            return _g_side(seg, v, vp, vy, lambda v: f"{v:.1f}%", neg_is_bad=False)
        return _g_make("Churn Rate", _s("Core"), _s("Lite"))

    def _g_payback_row():
        # Use Payback.csv "Todos" type for global
        _gpb = {}
        if PAYBACK_FILE.exists():
            import csv as _csv
            with open(PAYBACK_FILE, newline="", encoding="utf-8") as _f:
                for _r in _csv.DictReader(_f):
                    if _r.get("Type","").strip() != "Todos": continue
                    _seg = _r.get("Segment","").strip()
                    if _seg not in ("Core","Lite"): continue
                    _val = float(_r.get("valor", 0) or 0)
                    _fd  = _r.get("fecha","").strip()
                    try:
                        _mk = _fd[:7] if "-" in _fd else datetime.strptime(_fd, "%m/%d/%Y").strftime("%Y-%m")
                    except ValueError:
                        continue
                    _gpb.setdefault(_seg, {})[_mk] = _val
        def _g_pb(seg, m): return _gpb.get(seg, {}).get(m)
        def _g_pb_avg(seg, q_ms):
            vals = [_g_pb(seg, m) for m in q_ms if _g_pb(seg, m) is not None]
            return sum(vals)/len(vals) if vals else None
        def _s(seg):
            if is_quarter_end:
                v, vp, vy = _g_pb_avg(seg,_cur_q_ms), _g_pb_avg(seg,_prev_q_ms), _g_pb_avg(seg,_cur_q_ms_py)
            else:
                v, vp, vy = _g_pb(seg,latest_m), _g_pb(seg,prev_m), _g_pb(seg,prev_yr)
            return _g_side(seg, v, vp, vy, lambda v: f"{v:.1f} mo", neg_is_bad=False)
        return _g_make("Payback", _s("Core"), _s("Lite"))

    def _g_seg_kpi(seg):
        cur, prv, py = _gm(seg), _gpm(seg), _gpym(seg)
        ac, ap, ayp = cur.get("mrr_eop",0)*12, prv.get("mrr_eop",0)*12, py.get("mrr_eop",0)*12
        ms, mp = _pct_delta(ac, ap)
        ys, yp = _pct_delta(ac, ayp)
        return {"arr": _fm(ac), "arr_mom": ms, "arr_mom_positive": mp,
                "arr_yoy": ys, "arr_yoy_positive": yp}

    global_country = {
        "action_title": "🌎 Global — Core vs Lite Performance",
        "core": _g_seg_kpi("Core"),
        "lite": _g_seg_kpi("Lite"),
        "butterfly_rows": [
            _g_inv_row_q(),
            _g_nna_row(),
            _g_logos_growth_row(),
            _g_row_q("New Logos", lambda d: d.get("logos_new",0), "logos_new", lambda v: f"{int(v):,}"),
            _g_row_q("New ARR", lambda d: (d.get("mrr_new",0)+d.get("mrr_recov",0))*12, "mrr_new", lambda v: _fm(v*12)),
            _g_arpa_row(),
            _g_cac_row_q(),
            _g_churn_row_q(),
            _g_payback_row(),
        ],
    }

    # ── Alanube placeholder (manual data until RS source is defined) ──────────
    alanube = {
        "arr_bop":         "N/A",
        "arr_eop":         "N/A",
        "arr_delta_display": "N/A",
        "new_accounts":    "N/A",
        "issuing":         "N/A",
        "onboarding":      "N/A",
        "wf_bop_accounts": "N/A",
        "wf_new_arr":      "N/A",
        "wf_new_accounts": "N/A",
        "wf_new_note":     "Pendiente de fuente RS",
        "wf_churn_arr":    "N/A",
        "wf_churn_accounts": "N/A",
        "wf_churn_note":   "Pendiente de fuente RS",
        "wf_upside_arr":   "N/A",
        "wf_upside_note":  "Cuentas en onboarding",
        "wf_eop_accounts": "N/A",
    }

    # ── Chart period label
    first_q = next((lbl for lbl, _ in QUARTERS if lbl in
                    (seg_metrics.get("Core",{}).get("quarters",{}) or
                     seg_metrics.get("all",{}).get("quarters",{}))), "?")
    arr_chart_period_label = f"{first_q} – {latest_q_lbl}"

    # ── Assemble final structure
    out = {
        # --- Config (also needed by templates)
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "cutoff_month":  cutoff,

        # --- Slide 1 / Key Summary global KPIs
        "arr_total":           _fm(all_m.get("a_eop", 0)),
        "is_quarter_end":      is_quarter_end,
        "prev_quarter_label":  prev_q_label,

        "arr_mom":             arr_mom_str,
        "arr_mom_positive":    arr_mom_pos,
        "arr_qoq":             arr_qoq_str,
        "arr_qoq_positive":    arr_qoq_pos,
        "arr_vs_budget":       "N/A",
        "arr_vs_budget_positive": True,
        "arr_yoy":             arr_yoy_str,
        "arr_yoy_positive":    arr_yoy_pos,

        "new_mrr":                    _fm(all_q.get("a_new", 0) / 12) if is_quarter_end else _fm(all_m.get("a_new", 0) / 12),  # Q=suma 3 meses, MoM=mes actual
        "new_mrr_mom":                new_mrr_mom_str,
        "new_mrr_mom_positive":       new_mrr_mom_pos,
        "new_mrr_qoq":                new_mrr_qoq_str,
        "new_mrr_qoq_positive":       new_mrr_qoq_pos,
        "new_mrr_vs_budget":          "N/A",
        "new_mrr_vs_budget_positive": True,
        "new_mrr_yoy":                new_mrr_yoy_str,
        "new_mrr_yoy_positive":       new_mrr_yoy_pos,

        "new_logos":                    _fl(all_q.get("l_new", 0)) if is_quarter_end else _fl(all_m.get("l_new", 0)),  # Q=suma 3 meses
        "new_logos_mom":                new_logos_mom_str,
        "new_logos_mom_positive":       new_logos_mom_pos,
        "new_logos_qoq":                new_logos_qoq_str,
        "new_logos_qoq_positive":       new_logos_qoq_pos,
        "new_logos_vs_budget":          "N/A",
        "new_logos_yoy":                new_logos_yoy_str,
        "new_logos_yoy_positive":       new_logos_yoy_pos,

        # --- Financial KPIs (from Sheets — placeholders)
        "net_revenue":                  "N/A",
        "net_revenue_mom":              "N/A",
        "net_revenue_mom_positive":     True,
        "net_revenue_vs_budget":        "N/A",
        "net_revenue_vs_budget_positive": True,
        "net_revenue_yoy":              "N/A",
        "net_revenue_yoy_positive":     True,

        "gross_margin":                  "N/A",
        "gross_margin_mom":              "N/A",
        "gross_margin_vs_budget":        "N/A",
        "gross_margin_vs_budget_positive": True,
        "gross_margin_yoy":              "N/A",
        "gross_margin_yoy_positive":     True,

        "ebitda_margin":                  "N/A",
        "ebitda_margin_mom":              "N/A",
        "ebitda_margin_mom_positive":     True,
        "ebitda_margin_vs_budget":        "N/A",
        "ebitda_margin_vs_budget_positive": True,
        "ebitda_margin_yoy":              "N/A",
        "ebitda_margin_yoy_positive":     True,

        # --- Risk KPIs (Sheets for payback, RS for churn)
        "logo_churn_core":    round((_q("Core") if is_quarter_end else _mo("Core")).get("l_churn_pct", 0) * 100, 1),
        "logo_churn_global":  round((_q("all")  if is_quarter_end else all_m).get("l_churn_pct", 0) * 100, 1),
        "logo_churn_vs_budget_pp": "N/A",
        "payback_core":       "N/A",
        "payback_lite":       "N/A",
        "payback_hist":       "N/A",

        # Raw values for budget merge (removed before writing yaml)
        "_raw": {
            "arr_eop":         all_m.get("a_eop", 0),
            "new_mrr":         (all_q.get("a_new", 0) if is_quarter_end else all_m.get("a_new", 0)) / 12,
            "new_logos":       all_q.get("l_new", 0) if is_quarter_end else all_m.get("l_new", 0),
            "logo_churn_pct":  round((_q("all") if is_quarter_end else all_m).get("l_churn_pct", 0) * 100, 2),
        },

        # --- ARR Walk products (Section 03)
        "arr_chart_period_label": arr_chart_period_label,
        "arr_walk_products":      products,

        # --- Alanube (Section 03)
        "alanube": alanube,

        # --- Countries (Section 03)
        "countries": countries,
        "global_country": global_country,
    }

    # ── YTD acumulado (slide 5) ───────────────────────────────────────────────
    _cur_yr  = latest_m[:4]
    _prev_yr_int = str(int(_cur_yr) - 1)
    _ytd_cur = seg_metrics.get("all", {}).get("ytd", {}).get(_cur_yr, {})
    _ytd_py  = seg_metrics.get("all", {}).get("ytd", {}).get(_prev_yr_int, {})

    _new_mrr_ytd    = _ytd_cur.get("a_new", 0) / 12
    _new_mrr_ytd_py = _ytd_py.get("a_new",  0) / 12
    _new_l_ytd      = _ytd_cur.get("l_new", 0)
    _new_l_ytd_py   = _ytd_py.get("l_new",  0)

    out["new_mrr_ytd"]              = _fm(_new_mrr_ytd)
    out["new_mrr_ytd_yoy"], out["new_mrr_ytd_yoy_positive"] = _pct_delta(_new_mrr_ytd, _new_mrr_ytd_py)
    out["new_logos_ytd"]            = _fl(_new_l_ytd)
    out["new_logos_ytd_yoy"], out["new_logos_ytd_yoy_positive"] = _pct_delta(_new_l_ytd, _new_l_ytd_py)

    # ── Global chart arrays + QTD metrics (1_inicio) ──────────────────────────
    _all_q_data = seg_metrics.get("all", {}).get("quarters", {})
    _cqs        = [lbl for lbl, _ in QUARTERS if lbl in _all_q_data]
    _aq_cur     = _all_q_data.get(latest_q_lbl, {})
    _aq_prv_idx = max(0, next((i for i,(l,_) in enumerate(QUARTERS) if l==latest_q_lbl), 0)-1)
    _aq_prv_lbl = QUARTERS[_aq_prv_idx][0]
    _aq_prv     = _all_q_data.get(_aq_prv_lbl, {})
    _all_bym    = segs_raw.get("all", {})

    _g_new_rec  = [_all_q_data[q].get("a_new",0)/1e6 + _all_q_data[q].get("a_recov",0)/1e6 for q in _cqs]
    _g_exp      = [max(_all_q_data[q].get("a_upsell",0)/1e6, 0) for q in _cqs]
    _g_churn    = [max(_all_q_data[q].get("a_churn",0)/1e6, 0) for q in _cqs]
    _g_cont     = [max(_all_q_data[q].get("a_down",0)/1e6, 0) for q in _cqs]
    _g_nn       = [_all_q_data[q].get("a_net_new",0)/1e6 for q in _cqs]
    _g_ln       = [_all_q_data[q].get("l_new",0)+_all_q_data[q].get("l_recov",0) for q in _cqs]
    _g_lc       = [_all_q_data[q].get("l_disc",0) for q in _cqs]
    _g_ymax     = max((max(_g_new_rec+_g_exp) if _g_new_rec else 0),
                      (max(_g_churn+_g_cont)   if _g_churn   else 0)) * 1.25 or 1

    _gqc = []
    for _ql, _ms in QUARTERS[-5:]:
        if not any(m in _all_bym for m in _ms): continue
        _bop_k = _prev_m(_ms[0]); _eop_k = _ms[-1]
        _gqc.append({
            "label":    _ql,
            "bopArr":   _fm(_all_bym.get(_bop_k,{}).get("mrr_eop",0)*12),
            "bopLogos": round(_all_bym.get(_bop_k,{}).get("logos_eop",0)/1e3,2),
            "eopArr":   _fm(_all_bym.get(_eop_k,{}).get("mrr_eop",0)*12),
            "eopLogos": round(_all_bym.get(_eop_k,{}).get("logos_eop",0)/1e3,2),
        })

    out.update({
        "arr_quarters":            _cqs,
        "arr_new_rec":             _g_new_rec,
        "arr_expansion":           _g_exp,
        "arr_churn":               _g_churn,
        "arr_contraction":         _g_cont,
        "arr_net_new":             _g_nn,
        "arr_chart_y_max":         round(_g_ymax, 2),
        "logos_new":               _g_ln,
        "logos_expansion":         [0]*len(_cqs),
        "logos_churn":             _g_lc,
        "logos_contraction":       [0]*len(_cqs),
        "arr_q_cards":             _gqc,
        # QTD
        "arr_eop_qtd":             _fm(_aq_cur.get("a_eop",0)),
        "arr_qoq":                 _pct_delta(_aq_cur.get("a_eop",0), _aq_prv.get("a_eop",0))[0],
        "net_new_arr_qtd":         _fm(_aq_cur.get("a_net_new",0)),
        "net_new_arr_prev_qtd":    _fm(_aq_prv.get("a_net_new",0)),
        "net_new_arr_qoq":         _pct_delta(_aq_cur.get("a_net_new",0), _aq_prv.get("a_net_new",0))[0],
        "logos_eop_qtd":           _fl(_aq_cur.get("l_eop",0)),
        "logos_qoq":               _pct_delta(_aq_cur.get("l_eop",0), _aq_prv.get("l_eop",0))[0],
        "logos_yoy":               _pct_delta(_aq_cur.get("l_eop",0), _aq_cur.get("l_eop_py",0))[0],
        "prev_quarter_label":      _aq_prv_lbl,
        # SMB logos (global) / Accountant (N/A — needs channel_name query)
        "smb_logos_eop":           round(_aq_cur.get("l_eop",0)),
        "smb_logos_yoy":           _pct_delta(_aq_cur.get("l_eop",0), _aq_cur.get("l_eop_py",0))[0],
        "smb_logos_yoy_positive":  _pct_delta(_aq_cur.get("l_eop",0), _aq_cur.get("l_eop_py",0))[1],
        "smb_logos_net_adds":      round(all_m.get("l_new",0)+all_m.get("l_recov",0)-all_m.get("l_disc",0)),
        "accountant_logos_eop":          "N/A",
        "accountant_logos_qoq":          "N/A",
        "accountant_logos_qoq_positive": True,
        "accountant_logos_net_adds":     "N/A",
        # Churn extras
        "logo_churn_qoq":          _pct_delta(_aq_cur.get("a_churn",0), _aq_prv.get("a_churn",0))[0],
        "logo_churn_yoy":          _pct_delta(_aq_cur.get("a_churn",0), _aq_cur.get("a_eop_py",0))[0],
        "logo_churn_qtd_avg":      "N/A",
    })

    # ── ARR Walk Table (nuevo slide en 1_inicio) ──────────────────────────────
    _last5q = [lbl for lbl, _ in QUARTERS if lbl in _all_q_data][-5:]

    def _fa_abs(v):
        return _fm(v) if v != 0 else "—"

    def _fa_delta(v):
        if v == 0: return "—"
        abs_v = abs(v)
        s = f"${abs_v/1e6:.1f}M" if abs_v >= 1e6 else f"${abs_v/1e3:.0f}K"
        return f"+{s}" if v > 0 else f"({s})"

    def _fl_abs(v):
        return f"{int(round(v)):,}" if v else "—"

    def _fl_delta(v):
        if v == 0: return "—"
        return f"+{int(round(v)):,}" if v > 0 else f"({int(round(abs(v))):,})"

    def _pill_pct(cur, prv, invert=False):
        """(text, is_good) para cambio porcentual entre dos valores."""
        if not prv or cur is None: return ("—", None)
        chg = (cur - prv) / abs(prv)
        pos = chg >= 0
        sign = "+" if pos else "−"
        good = pos if not invert else not pos
        return (f"{sign}{abs(chg)*100:.0f}%", good)

    def _pill_pp(cur, prv, invert=False):
        """(text, is_good) para cambio en puntos porcentuales (valores ya en fracción)."""
        if cur is None or prv is None: return ("—", None)
        diff = cur - prv
        pos = diff >= 0
        sign = "+" if pos else "−"
        good = pos if not invert else not pos
        return (f"{sign}{abs(diff)*100:.1f}pp", good)

    # Valores del año anterior para cada quarter en _last5q
    def _py_lbl(q):
        """1Q26 → 1Q25, 4Q25 → 4Q24, etc."""
        prefix, yr = q[:-2], int(q[-2:])
        return f"{prefix}{yr-1:02d}"

    def _qraw_py(key):
        return [_all_q_data.get(_py_lbl(q), {}).get(key) or 0 for q in _last5q]

    def _aw_row(label, row_type, dot, raws, fmtfn, raws_py=None, pp=False, invert=False, nv=False):
        """Construye un dict de fila para arr_walk_table. raws = lista de 5 valores numéricos."""
        cells = [fmtfn(r) for r in raws]
        pill_fn = _pill_pp if pp else _pill_pct
        # QoQ por cada quarter: cambio vs quarter anterior (primero = —)
        qoq_cells = []
        for i, r in enumerate(raws):
            if i == 0:
                qoq_cells.append(("—", None))
            else:
                qoq_cells.append(pill_fn(r, raws[i-1], invert=invert))
        # YoY por cada quarter: cambio vs mismo quarter año anterior
        yoy_cells = []
        for i, r in enumerate(raws):
            py = raws_py[i] if raws_py else None
            if py:
                yoy_cells.append(pill_fn(r, py, invert=invert))
            else:
                yoy_cells.append(("—", None))
        qoq, qoq_good = qoq_cells[-1]
        yoy, yoy_good = yoy_cells[-1]
        return {
            "label": label, "type": row_type, "dot": dot,
            "cells": cells,
            "qoq": qoq, "qoq_good": qoq_good,
            "yoy": yoy, "yoy_good": yoy_good,
            "qoq_cells": [{"v": v, "good": g} for v, g in qoq_cells],
            "yoy_cells": [{"v": v, "good": g} for v, g in yoy_cells],
            "ytd_prev": cells[0],
            "ytd_cur": cells[-1],
            "nv": nv,
        }

    def _qraw(key):
        return [_all_q_data[q].get(key) or 0 for q in _last5q]

    _l_bop    = _qraw("l_bop")
    _l_new    = _qraw("l_new")
    _l_eop    = _qraw("l_eop")
    _l_churn  = _qraw("l_churn_pct")   # tasa mensual promedio (fracción)
    _a_bop    = _qraw("a_bop")
    _a_new    = _qraw("a_new")
    _a_recov  = _qraw("a_recov")
    _a_churn  = _qraw("a_net_churn")
    _a_upsell = _qraw("a_upsell")
    _a_down   = _qraw("a_down")
    _a_fx     = _qraw("a_fx")
    _a_net_new = _qraw("a_net_new")
    _a_eop    = _qraw("a_eop")
    _a_eop_cc = _qraw("a_cc_eop")
    _a_eop_py = _qraw_py("a_eop")

    _l_new_pct   = _qraw("l_new_pct")   # (new + recov) / avg_logos / n — ya calculado en _calc
    _a_net_exp   = [_a_upsell[i] + _a_down[i] for i in range(len(_last5q))]
    _a_net_ce_pct = [(_a_churn[i] + _a_net_exp[i]) / _a_bop[i] if _a_bop[i] else 0 for i in range(len(_last5q))]

    # ── SaaS Metrics helpers ─────────────────────────────────────────────────
    _q_months_map = {lbl: ms for lbl, ms in QUARTERS}

    # S&M Total Spend: suma investment global (todos países + segmentos) por Q
    def _sm_for_q(q):
        ms = _q_months_map.get(q, [])
        total = 0.0
        for country_inv in (investment or {}).values():
            for seg_inv in country_inv.values():
                for m in ms:
                    total += seg_inv.get(m, {}).get("total", 0)
        return total

    _a_sm = [_sm_for_q(q) for q in _last5q]

    # Payback global (Type="Todos") por Q — promedio mensual de Core y Lite
    _pb_global = {}  # {seg: {month: val}}
    if PAYBACK_FILE.exists():
        with open(PAYBACK_FILE, newline="", encoding="utf-8") as _pf:
            for _pr in csv.DictReader(_pf):
                if _pr.get("Type", "").strip() != "Todos":
                    continue
                _pseg = _pr.get("Segment", "").strip()
                _pval_s = _pr.get("valor", "").strip()
                if not _pval_s:
                    continue
                _pfd = _pr.get("fecha", "").strip()
                try:
                    _pmk = _pfd[:7] if "-" in _pfd else datetime.strptime(_pfd, "%m/%d/%Y").strftime("%Y-%m")
                except ValueError:
                    continue
                _pb_global.setdefault(_pseg, {})[_pmk] = float(_pval_s)

    def _payback_for_q(q):
        ms = _q_months_map.get(q, [])
        vals = [_pb_global.get(seg, {}).get(m) for seg in ("Core", "Lite") for m in ms
                if _pb_global.get(seg, {}).get(m)]
        return sum(vals) / len(vals) if vals else 0

    _a_payback = [_payback_for_q(q) for q in _last5q]

    # FX rates — promedio mensual por Q desde paises_fx.csv
    _fx_rates = load_fx()

    def _fx_avg_q(pais, q):
        ms = _q_months_map.get(q, [])
        rates = [_fx_rates[(pais, m)] for m in ms if (pais, m) in _fx_rates]
        return sum(rates) / len(rates) if rates else 0

    _a_cop = [_fx_avg_q("colombia", q) for q in _last5q]
    _a_mxn = [_fx_avg_q("mexico",   q) for q in _last5q]

    out["arr_walk_table"] = {
        "quarters": _last5q,
        "ytd_labels": [f"YTD'{_last5q[0][-2:]}", f"YTD'{_last5q[-1][-2:]}"],
        "sections": [
            {
                "label": "Logo EoP (000's)",
                "rows": [
                    _aw_row("Total EoP", "rb", "g",
                        _l_eop, lambda v: f"{v/1e3:.1f}" if v != 0 else "—"),
                    _aw_row("Logo Monthly New Adds %", "rt", None,
                        _l_new_pct, lambda v: f"{v*100:.1f}%" if v != 0 else "—",
                        pp=True),
                    _aw_row("Logo Monthly Churn %", "rt", None,
                        _l_churn, lambda v: f"{v*100:.1f}%" if v != 0 else "—",
                        pp=True, invert=True),
                ],
            },
            {
                "label": "ARR Walk — Spot ($M)",
                "rows": [
                    _aw_row("ARR BoP",       "rb", "g", _a_bop,    lambda v: f"${v/1e6:.1f}" if v != 0 else "—"),
                    _aw_row("Additions",      "in", "g", _a_new,    _fa_delta),
                    _aw_row("Recovered",      "in", "g", _a_recov,  _fa_delta),
                    _aw_row("Net Churn",      "in", "r", _a_churn,  _fa_delta, nv=True),
                    _aw_row("Net Expansion",  "in", "a", _a_net_exp, _fa_delta),
                    _aw_row("(+/−) FX Impact","in", "s", _a_fx,     _fa_delta),
                    _aw_row("ARR EoP",        "rb", "g", _a_eop,    lambda v: f"${v/1e6:.1f}" if v != 0 else "—", raws_py=_a_eop_py),
                    _aw_row("Net New ARR",    "rb", "a", _a_net_new, _fa_delta),
                    _aw_row("ARR EoP (CC)",   "in", "s", _a_eop_cc,  lambda v: f"${v/1e6:.1f}" if v != 0 else "—"),
                ],
            },
            {
                "label": "SaaS Metrics",
                "rows": [
                    _aw_row("Net Churn / Expansion %", "in", "g",
                        _a_net_ce_pct, lambda v: f"{v*100:.1f}%" if v != 0 else "—",
                        pp=True),
                    _aw_row("S&M Total Spend ($K)", "in", "s", _a_sm,
                        lambda v: f"${v/1e3:.0f}K" if v else "—", invert=True),
                    _aw_row("CAC Payback (meses)", "in", "g", _a_payback,
                        lambda v: f"{v:.1f}" if v else "—", invert=True),
                    _aw_row("FX — COP/USD", "rt", "s", _a_cop,
                        lambda v: f"{v:,.0f}" if v else "—", invert=True),
                    _aw_row("FX — MXN/USD", "rt", "s", _a_mxn,
                        lambda v: f"{v:.1f}" if v else "—", invert=True),
                ],
            },
        ],
    }

    # ── OVERRIDE TEMPORAL ARR Walk Global (valores del SS Apr-2026) ──────────
    # NOTA: no tocar las fórmulas arriba — solo parchear cells/qoq/yoy aquí.
    # Remover este bloque cuando RS entregue datos correctos.
    _aw_overrides = {
        "Total EoP":          {"cells": ["54.5","54.2","55.1","56.8","57.6"]},
        "Logo Monthly New Adds %": {"cells": ["5.1%","4.7%","4.9%","5.3%","5.3%"]},
        "Logo Monthly Churn %":    {"cells": ["5.2%","4.9%","4.3%","4.3%","4.8%"]},
        "ARR BoP":            {"cells": ["$19.2","$22.4","$22.9","$24.2","$26.6"]},
        "Recovered":          {"cells": ["+$400K","+$500K","+$500K","+$700K","+$500K"]},
        "Net Churn":          {"cells": ["($2.6M)","($2.6M)","($2.5M)","($2.4M)","($3.3M)"]},
        "Net Expansion":      {"cells": ["+$2.7M","+$700K","+$700K","+$1.5M","+$400K"]},
        "(+/−) FX Impact":    {"cells": ["+$800K","+$200K","+$700K","+$600K","+$400K"]},
        "ARR EoP":            {
            "cells": ["$22.4","$22.9","$24.2","$26.6","$27.3"],
            "qoq_cells": [{"v":"—","good":None},{"v":"+3%","good":True},{"v":"+6%","good":True},{"v":"+10%","good":True},{"v":"+3%","good":True}],
            "yoy_cells": [{"v":"+39%","good":True},{"v":"+41%","good":True},{"v":"+31%","good":True},{"v":"+39%","good":True},{"v":"+22%","good":True}],
            "qoq": "+3%", "qoq_good": True, "yoy": "+22%", "yoy_good": True,
            "ytd_prev": "$22.4", "ytd_cur": "$27.3",
        },
        "Net New ARR":        {"cells": ["+$3.2M","+$600K","+$1.3M","+$2.3M","+$700K"], "ytd_prev":"+$3.2M","ytd_cur":"+$700K"},
        "ARR EoP (CC)":       {
            "cells": ["$24.2","$24.6","$25.2","$27.0","$27.3"],
            "qoq_cells": [{"v":"—","good":None},{"v":"+2%","good":True},{"v":"+2%","good":True},{"v":"+7%","good":True},{"v":"+1%","good":True}],
            "ytd_prev": "$24.2", "ytd_cur": "$27.3",
        },
    }
    for _sec in out["arr_walk_table"]["sections"]:
        for _row in _sec["rows"]:
            if _row["label"] in _aw_overrides:
                _row.update(_aw_overrides[_row["label"]])
    # ── FIN OVERRIDE ─────────────────────────────────────────────────────────

    # ── Per-segment ARR Walk Table (slides 2-3 de 3_arr_walk) ────────────────
    for _prod in out["arr_walk_products"]:
        _seg_name = _prod["name"]   # "Core" o "Lite"
        _sq_data  = seg_metrics.get(_seg_name, {}).get("quarters", {})
        _s5q      = [lbl for lbl, _ in QUARTERS if lbl in _sq_data][-5:]
        if not _s5q:
            _prod["arr_walk_table"] = None
            continue

        def _sqraw(key, _sq=_sq_data, _s5=_s5q):
            return [_sq[q].get(key) or 0 for q in _s5]

        _sl_bop    = _sqraw("l_bop")
        _sl_new    = _sqraw("l_new")
        _sl_eop    = _sqraw("l_eop")
        _sl_churn  = _sqraw("l_churn_pct")
        _sa_bop    = _sqraw("a_bop")
        _sa_new    = _sqraw("a_new")
        _sa_recov  = _sqraw("a_recov")
        _sa_churn  = _sqraw("a_net_churn")
        _sa_upsell = _sqraw("a_upsell")
        _sa_down   = _sqraw("a_down")
        _sa_fx     = _sqraw("a_fx")
        _sa_net_new = _sqraw("a_net_new")
        _sa_eop    = _sqraw("a_eop")
        _sa_eop_py = [_sq_data.get(_py_lbl(q), {}).get("a_eop") or 0 for q in _s5q]

        _sl_new_pct = [_sl_new[i] / (3 * _sl_bop[i]) if _sl_bop[i] else 0 for i in range(len(_s5q))]
        _sa_net_exp = [_sa_upsell[i] + _sa_down[i] for i in range(len(_s5q))]
        _sa_net_ce  = [(_sa_churn[i] + _sa_net_exp[i]) / _sa_bop[i] if _sa_bop[i] else 0 for i in range(len(_s5q))]

        _prod["arr_walk_table"] = {
            "quarters":   _s5q,
            "ytd_labels": [f"YTD'{_s5q[0][-2:]}", f"YTD'{_s5q[-1][-2:]}"],
            "sections": [
                {
                    "label": "Logo EoP (000's)",
                    "rows": [
                        _aw_row("Total EoP", "rb", "g", _sl_eop, lambda v: f"{v/1e3:.1f}" if v != 0 else "—"),
                        _aw_row("Logo Monthly New Adds %", "rt", None, _sl_new_pct, lambda v: f"{v*100:.1f}%" if v != 0 else "—", pp=True),
                        _aw_row("Logo Monthly Churn %", "rt", None, _sl_churn, lambda v: f"{v*100:.1f}%" if v != 0 else "—", pp=True, invert=True),
                    ],
                },
                {
                    "label": "ARR Walk — Spot ($M)",
                    "rows": [
                        _aw_row("ARR BoP",         "rb", "g", _sa_bop,     lambda v: f"${v/1e6:.1f}" if v != 0 else "—"),
                        _aw_row("Additions",        "in", "g", _sa_new,    _fa_delta),
                        _aw_row("Recovered",        "in", "g", _sa_recov,  _fa_delta),
                        _aw_row("Net Churn",        "in", "r", _sa_churn,  _fa_delta, nv=True),
                        _aw_row("Net Expansion",    "in", "a", _sa_net_exp, _fa_delta),
                        _aw_row("(+/−) FX Impact",  "in", "s", _sa_fx,    _fa_delta),
                        _aw_row("ARR EoP",          "rb", "g", _sa_eop,   lambda v: f"${v/1e6:.1f}" if v != 0 else "—", raws_py=_sa_eop_py),
                        _aw_row("Net New ARR",      "rb", "a", _sa_net_new, _fa_delta),
                    ],
                },
                {
                    "label": "SaaS Metrics",
                    "rows": [
                        _aw_row("Net Churn / Expansion %", "in", "g", _sa_net_ce, lambda v: f"{v*100:.1f}%" if v != 0 else "—", pp=True),
                        _aw_row("S&M Total Spend ($K)", "in", "s", _a_sm,
                            lambda v: f"${v/1e3:.0f}K" if v else "—", invert=True),
                        _aw_row("CAC Payback (meses)", "in", "g", _a_payback,
                            lambda v: f"{v:.1f}" if v else "—", invert=True),
                        _aw_row("FX — COP/USD", "rt", "s", _a_cop,
                            lambda v: f"{v:,.0f}" if v else "—", invert=True),
                        _aw_row("FX — MXN/USD", "rt", "s", _a_mxn,
                            lambda v: f"{v:.1f}" if v else "—", invert=True),
                    ],
                },
            ],
        }

        # ── OVERRIDE TEMPORAL por segmento (valores del SS Apr-2026) ─────────
        _seg_overrides = {
            "Core": {
                "Total EoP":           {"cells": ["18.8","19.4","20.4","22.0","23.0"]},
                "Logo Monthly New Adds %": {"cells": ["4.6%","4.5%","4.6%","4.5%","4.5%"]},
                "Logo Monthly Churn %":    {"cells": ["3.4%","3.2%","3.0%","2.8%","3.6%"]},
                "ARR BoP":             {"cells": ["$10.6","$12.2","$12.8","$13.8","$15.6"]},
                "Additions":           {"cells": ["+$1.0M","+$1.0M","+$1.0M","+$1.1M","+$1.2M"]},
                "Recovered":           {"cells": ["+$100K","+$200K","+$100K","+$200K","+$100K"]},
                "Net Churn":           {"cells": ["($1.0M)","($1.0M)","($1.0M)","($1.0M)","($1.5M)"]},
                "Net Expansion":       {"cells": ["+$1.2M","+$400K","+$400K","+$900K","+$200K"]},
                "(+/−) FX Impact":     {"cells": ["+$500K","+$100K","+$400K","+$300K","+$300K"]},
                "ARR EoP":             {
                    "cells": ["$12.2","$12.8","$13.8","$15.6","$16.2"],
                    "qoq_cells": [{"v":"—","good":None},{"v":"+5%","good":True},{"v":"+8%","good":True},{"v":"+13%","good":True},{"v":"+4%","good":True}],
                    "yoy_cells": [{"v":"+36%","good":True},{"v":"+41%","good":True},{"v":"+36%","good":True},{"v":"+48%","good":True},{"v":"+33%","good":True}],
                    "qoq": "+4%", "qoq_good": True, "yoy": "+33%", "yoy_good": True,
                    "ytd_prev": "$12.2", "ytd_cur": "$16.2",
                },
                "Net New ARR":         {"cells": ["+$1.6M","+$600K","+$1.0M","+$1.8M","+$600K"], "ytd_prev":"+$1.6M","ytd_cur":"+$600K"},
                "ARR EoP (CC)":        {
                    "cells": ["$13.2","$13.8","$14.4","$15.9","$16.2"],
                    "qoq_cells": [{"v":"—","good":None},{"v":"+4%","good":True},{"v":"+4%","good":True},{"v":"+11%","good":True},{"v":"+2%","good":True}],
                    "ytd_prev": "$13.2", "ytd_cur": "$16.2",
                },
            },
            "Lite": {
                "Total EoP":           {"cells": ["35.7","34.8","34.7","34.8","34.6"]},
                "Logo Monthly New Adds %": {"cells": ["5.4%","4.8%","5.0%","5.8%","5.7%"]},
                "Logo Monthly Churn %":    {"cells": ["6.1%","5.7%","5.1%","5.1%","5.5%"]},
                "ARR BoP":             {"cells": ["$8.6","$10.1","$10.1","$10.4","$10.9"]},
                "Additions":           {"cells": ["+$700K","+$800K","+$800K","+$900K","+$1.3M"]},
                "Recovered":           {"cells": ["+$300K","+$400K","+$400K","+$500K","+$400K"]},
                "Net Churn":           {"cells": ["($1.5M)","($1.6M)","($1.5M)","($1.5M)","($1.8M)"]},
                "Net Expansion":       {"cells": ["+$1.5M","+$300K","+$300K","+$600K","+$200K"]},
                "(+/−) FX Impact":     {"cells": ["+$400K","+$100K","+$300K","+$200K","+$200K"]},
                "ARR EoP":             {
                    "cells": ["$10.1","$10.1","$10.4","$10.9","$11.1"],
                    "qoq_cells": [{"v":"—","good":None},{"v":"−0%","good":False},{"v":"+3%","good":True},{"v":"+5%","good":True},{"v":"+1%","good":True}],
                    "yoy_cells": [{"v":"+43%","good":True},{"v":"+41%","good":True},{"v":"+26%","good":True},{"v":"+27%","good":True},{"v":"+9%","good":True}],
                    "qoq": "+1%", "qoq_good": True, "yoy": "+9%", "yoy_good": True,
                    "ytd_prev": "$10.1", "ytd_cur": "$11.1",
                },
                "Net New ARR":         {"cells": ["+$1.6M","($0K)","+$300K","+$500K","+$100K"], "ytd_prev":"+$1.6M","ytd_cur":"+$100K"},
                "ARR EoP (CC)":        {
                    "cells": ["$11.0","$10.9","$10.8","$11.1","$11.1"],
                    "qoq_cells": [{"v":"—","good":None},{"v":"−1%","good":False},{"v":"−0%","good":False},{"v":"+3%","good":True},{"v":"−0%","good":False}],
                    "ytd_prev": "$11.0", "ytd_cur": "$11.1",
                },
            },
        }
        if _seg_name in _seg_overrides:
            for _sec in _prod["arr_walk_table"]["sections"]:
                for _row in _sec["rows"]:
                    if _row["label"] in _seg_overrides[_seg_name]:
                        _row.update(_seg_overrides[_seg_name][_row["label"]])
        # ── FIN OVERRIDE ─────────────────────────────────────────────────────

    # ── pp namespace (4_financial_performance) ────────────────────────────────
    _pp_months = [_month_label(m) for m in all_months[-12:]]
    _pp_prods  = []
    for _pc in [{"seg":"Core","id":"core","name":"Core","color":"#534AB7"},
                {"seg":"Lite","id":"lite","name":"Lite","color":"#1D9E75"}]:
        _bs = segs_raw.get(_pc["seg"], {})
        _mc = _bs.get(latest_m, {}); _mp = _bs.get(prev_m, {}); _my = _bs.get(prev_yr, {})
        _ac = _mc.get("mrr_eop",0)*12; _ap = _mp.get("mrr_eop",0)*12; _ay = _my.get("mrr_eop",0)*12
        _lc = _mc.get("logos_eop",0);  _lp = _mp.get("logos_eop",0);  _ly = _my.get("logos_eop",0)
        _pp_prods.append({
            "id": _pc["id"], "name": _pc["name"], "color": _pc["color"],
            "arr": _fm(_ac),
            "arr_mom": _pct_delta(_ac,_ap)[0], "arr_mom_positive": _pct_delta(_ac,_ap)[1],
            "arr_yoy": _pct_delta(_ac,_ay)[0], "arr_yoy_positive": _pct_delta(_ac,_ay)[1],
            "logos": _fl(_lc),
            "logos_mom": _pct_delta(_lc,_lp)[0], "logos_mom_positive": _pct_delta(_lc,_lp)[1],
            "logos_yoy": _pct_delta(_lc,_ly)[0], "logos_yoy_positive": _pct_delta(_lc,_ly)[1],
            "spark_arr":   [_bs.get(m,{}).get("mrr_eop",0)*12/1e6 for m in all_months[-12:]],
            "spark_data":  [_bs.get(m,{}).get("mrr_eop",0)*12/1e6 for m in all_months[-12:]],
            "spark_color": _pc["color"],
            "spark_fill":  _pc["color"] + "33",
        })
    out["pp"] = {
        "total_subs":        _fl(all_m.get("l_eop",0)),
        "total_subs_delta":  arr_mom_str,
        "total_logos":       _fl(all_m.get("l_eop",0)),
        "total_logos_delta": arr_mom_str,
        "period_label":      f"{latest_m_lbl} · ARR in USD",
        "spark_months":      _pp_months,
        "products":          _pp_prods,
    }

    # ── gtm namespace (5_go_to_market) ────────────────────────────────────────
    _nl_c     = round(_mo("Core").get("l_new",0))
    _nl_c_prv = round(_mo_prev("Core").get("l_new",0))
    _nl_c_py  = round(_mo_py("Core").get("l_new",0))
    _nl_l     = round(_mo("Lite").get("l_new",0))
    _nl_l_prv = round(_mo_prev("Lite").get("l_new",0))
    _nl_l_py  = round(_mo_py("Lite").get("l_new",0))

    # Country new logos — arrays of last 13 months for stacked bar chart
    _gtm_months13 = sorted(country_raw.keys())[-13:]
    def _cnl_ts(seg, ck):
        return [round(country_raw.get(m,{}).get(ck,{}).get(seg,{}).get("logos_new",0))
                for m in _gtm_months13]

    _na = "N/A"

    # ── Investment helpers for GTM (global = sum across countries)
    _inv_months13 = sorted({
        m for ci in investment.values() for seg in ci.values() for m in seg
    })[-13:]

    def _fmt_inv(v):
        if v is None: return _na
        if v >= 1_000_000: return f"${v/1_000_000:.1f}M"
        return f"${round(v/1_000)}K"

    def _pct_str(num, den):
        if not den: return _na
        return f"{round(num/den*100)}%"

    def _inv_series(seg, field):
        return [round(_g_inv(seg, m, field) or 0) for m in _inv_months13]

    def _pct_series(seg, num_fn, den_fn):
        result = []
        for m in _inv_months13:
            n, d = num_fn(seg, m), den_fn(seg, m)
            result.append(round(n/d*100, 1) if (n and d) else None)
        return result

    # Current, prev month, prev year values per segment
    _g_inv_m  = {s: _g_inv(s, latest_m)  for s in ("Core","Lite")}
    _g_inv_pm = {s: _g_inv(s, prev_m)    for s in ("Core","Lite")}
    _g_inv_py = {s: _g_inv(s, prev_yr)   for s in ("Core","Lite")}

    def _inv_delta(seg, cur_fn, prv_fn):
        c, p = cur_fn(seg, latest_m), prv_fn(seg, latest_m)
        if not c or not p: return _na, True
        return _pct_delta(c, p)

    _paid_pct_lite_series  = _pct_series("Lite", _g_inv_paid, _g_inv)
    _paid_pct_core_series  = _pct_series("Core", _g_inv_paid, _g_inv)
    _team_pct_core_series  = _pct_series("Core", _g_inv_people, _g_inv)

    def _pct_cur(seg, comp_fn):
        t, c = _g_inv(seg, latest_m), comp_fn(seg, latest_m)
        return _pct_str(c, t) if (t and c is not None) else _na

    # top2_concentration: % of Core new logos from top-2 countries in latest month
    _top2_vals = sorted([
        country_raw.get(latest_m, {}).get(ck, {}).get("Core", {}).get("logos_new", 0)
        for ck in ("colombia","mexico","republicaDominicana","costaRica")
    ], reverse=True)
    _top2_total = sum(_top2_vals[:2])
    _top2_all   = sum(_top2_vals) or 1
    _top2_pct   = f"{round(_top2_total/_top2_all*100)}%"

    out["gtm"] = {
        "new_logos_core":              _nl_c,
        "new_logos_core_mom":          _pct_delta(_nl_c, _nl_c_prv)[0],
        "new_logos_core_mom_positive": _pct_delta(_nl_c, _nl_c_prv)[1],
        "new_logos_core_yoy":          _pct_delta(_nl_c, _nl_c_py)[0],
        "new_logos_core_yoy_positive": _pct_delta(_nl_c, _nl_c_py)[1],
        "new_logos_lite":              _nl_l,
        "new_logos_lite_mom":          _pct_delta(_nl_l, _nl_l_prv)[0],
        "new_logos_lite_mom_positive": _pct_delta(_nl_l, _nl_l_prv)[1],
        "new_logos_lite_yoy":          _pct_delta(_nl_l, _nl_l_py)[0],
        "new_logos_lite_yoy_positive": _pct_delta(_nl_l, _nl_l_py)[1],
        "new_logos_core_co": _cnl_ts("Core","colombia"),
        "new_logos_core_mx": _cnl_ts("Core","mexico"),
        "new_logos_core_dr": _cnl_ts("Core","republicaDominicana"),
        "new_logos_core_cr": _cnl_ts("Core","costaRica"),
        "new_logos_lite_co": _cnl_ts("Lite","colombia"),
        "new_logos_lite_mx": _cnl_ts("Lite","mexico"),
        "new_logos_lite_dr": _cnl_ts("Lite","republicaDominicana"),
        "new_logos_lite_cr": _cnl_ts("Lite","costaRica"),
        "chart_months":     [_month_label(m) for m in all_months[-13:]],
        "inv_chart_months": [_month_label(m) for m in _inv_months13],
        # S&M investment — from RS (db_finance.fact_cac_version_segments)
        "sm_core_total":           _fmt_inv(_g_inv_m["Core"]),
        "sm_core_total_cur":       _fmt_inv(_g_inv_m["Core"]),
        "sm_core_total_prev":      _fmt_inv(_g_inv_pm["Core"]),
        "sm_core_total_prev_year": _fmt_inv(_g_inv_py["Core"]),
        "sm_core_people":          _pct_cur("Core", _g_inv_people),
        "sm_core_people_prev":     _pct_str(_g_inv_people("Core", prev_m) or 0, _g_inv("Core", prev_m) or 1),
        "sm_core_people_prev_year":_pct_str(_g_inv_people("Core", prev_yr) or 0, _g_inv("Core", prev_yr) or 1),
        "sm_core_paid":            _pct_cur("Core", _g_inv_paid),
        "sm_core_paid_prev":       _pct_str(_g_inv_paid("Core", prev_m) or 0, _g_inv("Core", prev_m) or 1),
        "sm_core_paid_prev_year":  _pct_str(_g_inv_paid("Core", prev_yr) or 0, _g_inv("Core", prev_yr) or 1),
        "sm_core_other":           _pct_cur("Core", _g_inv_other),
        "sm_core_other_prev":      _pct_str(_g_inv_other("Core", prev_m) or 0, _g_inv("Core", prev_m) or 1),
        "sm_core_other_prev_year": _pct_str(_g_inv_other("Core", prev_yr) or 0, _g_inv("Core", prev_yr) or 1),
        "sm_core_var":             _pct_delta(_g_inv_m["Core"], _g_inv_pm["Core"])[0] if _g_inv_m["Core"] else _na,
        "sm_core_var_positive":    _pct_delta(_g_inv_m["Core"], _g_inv_pm["Core"])[1] if _g_inv_m["Core"] else True,
        "sm_lite_total":           _fmt_inv(_g_inv_m["Lite"]),
        "sm_lite_total_cur":       _fmt_inv(_g_inv_m["Lite"]),
        "sm_lite_total_prev":      _fmt_inv(_g_inv_pm["Lite"]),
        "sm_lite_total_prev_year": _fmt_inv(_g_inv_py["Lite"]),
        "sm_lite_people":          _pct_cur("Lite", _g_inv_people),
        "sm_lite_people_prev":     _pct_str(_g_inv_people("Lite", prev_m) or 0, _g_inv("Lite", prev_m) or 1),
        "sm_lite_people_prev_year":_pct_str(_g_inv_people("Lite", prev_yr) or 0, _g_inv("Lite", prev_yr) or 1),
        "sm_lite_paid":            _pct_cur("Lite", _g_inv_paid),
        "sm_lite_paid_prev":       _pct_str(_g_inv_paid("Lite", prev_m) or 0, _g_inv("Lite", prev_m) or 1),
        "sm_lite_paid_prev_year":  _pct_str(_g_inv_paid("Lite", prev_yr) or 0, _g_inv("Lite", prev_yr) or 1),
        "sm_lite_other":           _pct_cur("Lite", _g_inv_other),
        "sm_lite_other_prev":      _pct_str(_g_inv_other("Lite", prev_m) or 0, _g_inv("Lite", prev_m) or 1),
        "sm_lite_other_prev_year": _pct_str(_g_inv_other("Lite", prev_yr) or 0, _g_inv("Lite", prev_yr) or 1),
        "sm_lite_var":             _pct_delta(_g_inv_m["Lite"], _g_inv_pm["Lite"])[0] if _g_inv_m["Lite"] else _na,
        "sm_lite_var_positive":    _pct_delta(_g_inv_m["Lite"], _g_inv_pm["Lite"])[1] if _g_inv_m["Lite"] else True,
        # Paid media / team % series
        "paid_media_pct_core_series": _paid_pct_core_series,
        "paid_media_pct_lite":        _pct_cur("Lite", _g_inv_paid),
        "paid_media_pct_lite_series": _paid_pct_lite_series,
        "team_pct_core":              _pct_cur("Core", _g_inv_people),
        "team_pct_core_series":       _team_pct_core_series,
        # Absolute investment series by component (for stacked bar charts)
        "sm_core_paid_series":   [round(_g_inv_paid("Core",   m) or 0) for m in _inv_months13],
        "sm_core_people_series": [round(_g_inv_people("Core", m) or 0) for m in _inv_months13],
        "sm_core_other_series":  [round(_g_inv_other("Core",  m) or 0) for m in _inv_months13],
        "sm_lite_paid_series":   [round(_g_inv_paid("Lite",   m) or 0) for m in _inv_months13],
        "sm_lite_people_series": [round(_g_inv_people("Lite", m) or 0) for m in _inv_months13],
        "sm_lite_other_series":  [round(_g_inv_other("Lite",  m) or 0) for m in _inv_months13],
        "top2_concentration":          _top2_pct,
        # Funnel (N/A — needs bi_funnel_master_table)
        "funnel_countries": [],
        # Flywheel (N/A — needs channel_name='Accountant' query)
        "flywheel_adds_first": 0, "flywheel_bracket_x": 0,
        "flywheel_churn_first": 0, "flywheel_gap": 0,
        "flywheel_gap_label_x": 0, "flywheel_gap_label_y": 0,
        "flywheel_label_adds_first_y": 0, "flywheel_label_churn_first_y": 0,
        "flywheel_label_first_x": 0, "flywheel_last_adds_label_y": 0,
        "flywheel_last_adds_val": 0, "flywheel_last_adds_x": 0, "flywheel_last_adds_y": 0,
        "flywheel_last_churn_label_y": 0, "flywheel_last_churn_val": 0,
        "flywheel_last_churn_x": 0, "flywheel_last_churn_y": 0,
        "flywheel_peak_adds_label_y": 0, "flywheel_peak_adds_val": 0,
        "flywheel_peak_adds_x": 0, "flywheel_peak_adds_y": 0,
        "flywheel_stock_first_val": 0, "flywheel_stock_first_x": 0,
        "flywheel_stock_growth_note": _na, "flywheel_stock_last_val": 0, "flywheel_stock_last_x": 0,
        "flywheel_stock_mid_x": 0, "flywheel_svg_adds_points": "",
        "flywheel_svg_churn_points": "", "flywheel_svg_gap_points": "",
        "flywheel_svg_stock_bars": "", "flywheel_x_label_": "",
        "flywheel_x_label_last": "", "flywheel_x_label_last_x": 0,
        "flywheel_y_bot": 0, "flywheel_y_mid": 0, "flywheel_y_top": 0,
    }

    # ── hc / pt namespaces (7_headcount — Sheets, N/A) ────────────────────────
    out["hc"] = {
        "slide": _na, "slide2_title": "Headcount",
        "headline": _na, "subline": _na,
        "total": _na, "total_sub": _na,
        "vs_forecast": _na, "vs_forecast_sub": _na,
        "new_hires": _na, "new_hires_sub": _na,
        "attrition": _na, "attrition_sub": _na,
        "turnover_rate": _na, "turnover_rate_sub": _na,
        "comparison_period": _na,
        "teams": [],
        "total_bar_pct": 0, "total_bar_label": _na,
        "total_yoy_delta": _na, "total_fcst_delta": _na,
        "spark_labels": [], "total_spark_data": [],
    }
    out["pt"] = {
        "months": [], "hc_eop": [], "hires": [],
        "attrition": [], "attrition_pct": [], "turnover_pct": [],
        "ya_max": 1, "yhead_max": 1, "yhead_min": 0,
        "ylines_max": 1, "yt_max": 1,
    }

    return out

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fetch board metrics from Redshift")
    parser.add_argument("--refresh",  action="store_true", help="Ignorar caché")
    parser.add_argument("--month",    default=None,        help="Mes de corte YYYY-MM (default: mes anterior)")
    parser.add_argument("--csv-only", action="store_true", help="Solo re-mergea CSVs (Budget, P&L, Payback) sin tocar Redshift")
    args = parser.parse_args()

    # Default cutoff = previous month
    if args.month:
        cutoff = args.month
    else:
        now = datetime.now()
        m = now.month - 1 or 12
        y = now.year if now.month > 1 else now.year - 1
        cutoff = f"{y:04d}-{m:02d}"

    print(f"📊 fetch_metrics.py · cutoff: {cutoff}")

    if args.csv_only:
        # Solo actualizar los merges de CSV sobre el metrics.yaml existente
        if not OUTPUT_FILE.exists():
            print("❌ No existe metrics.yaml — corre primero sin --csv-only para generar el YAML base.")
            sys.exit(1)
        print("📂 --csv-only: cargando metrics.yaml existente…")
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            out = yaml.safe_load(f)
        print("💰 Mergeando budget desde CSV…")
        merge_budget(out, cutoff)
        out.pop("_raw", None)
        print("📊 Mergeando P&L (Net Revenue, Gross Margin, EBITDA)…")
        merge_pnl(out, cutoff)
        print("⏱️  Mergeando Payback…")
        merge_payback(out, cutoff)
    else:
        print("📡 Cargando datos de Redshift…")
        summary, logos_all, country_raw, investment = load_data(cutoff, refresh=args.refresh)

        print("⚙️  Calculando métricas por segmento…")
        seg_metrics, segs_raw, all_months, latest_mm = build_seg_metrics(summary, logos_all)

        print("🗺️  Construyendo estructura YAML…")
        out = build_yaml(seg_metrics, segs_raw, all_months, latest_mm, country_raw, cutoff, investment)

        print("💰 Mergeando budget desde CSV…")
        merge_budget(out, cutoff)
        out.pop("_raw", None)  # solo para cálculo interno, no va al yaml

        print("📊 Mergeando P&L (Net Revenue, Gross Margin, EBITDA)…")
        merge_pnl(out, cutoff)

        print("⏱️  Mergeando Payback…")
        merge_payback(out, cutoff)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(out, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ metrics.yaml escrito → {OUTPUT_FILE}")
    print(f"   ARR total: {out['arr_total']} · MoM: {out['arr_mom']} · YoY: {out['arr_yoy']}")
    print(f"   Productos: {[p['name'] for p in out['arr_walk_products']]}")
    print(f"   Países:    {[c['team'] for c in out['countries']]}")


# ── Budget merge ───────────────────────────────────────────────────────────────
def _parse_num(s):
    """Remove $, commas and % from a CSV value and return float."""
    return float(str(s).replace("$", "").replace(",", "").replace("%", "").strip())

def merge_budget(out, cutoff):
    """Read Metricas_budget.csv, find the active month and inject vs_budget fields into out."""
    if not BUDGET_FILE.exists():
        print(f"⚠️  Budget CSV no encontrado: {BUDGET_FILE} — vs_budget queda N/A")
        return

    _MONTHS_EN = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]

    def _cutoff_to_key(c):
        y, m = c.split("-")
        return f"{_MONTHS_EN[int(m)-1]} - {y[2:]}"  # "2026-03" → "Mar - 26"

    def _q_months_for(c):
        """Devuelve los 3 meses del quarter al que pertenece c."""
        for _, ms in QUARTERS:
            if c in ms:
                return ms
        return [c]

    is_quarter_end = out.get("is_quarter_end", False)
    month_key = _cutoff_to_key(cutoff)

    # Leer TODO el CSV indexado por (Metric, month_key)
    budget_by_month = defaultdict(dict)   # {month_key: {metric: value}}
    with open(BUDGET_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        first_data_col = None
        for row in reader:
            if first_data_col is None:
                cols = [c for c in row.keys() if c not in ("Metric", "Fecha")]
                first_data_col = cols[0] if cols else None
            fk = row.get("Fecha", "").strip()
            metric = row.get("Metric", "").strip()
            val_str = (row.get(first_data_col, "") or "").strip()
            if fk and metric and val_str:
                try:
                    budget_by_month[fk][metric] = _parse_num(val_str)
                except ValueError:
                    pass

    # Budget del mes actual (para ARR EoP y Churn — siempre punto del mes)
    budget = budget_by_month.get(month_key, {})
    if not budget:
        print(f"⚠️  No se encontraron filas de budget para '{month_key}' en el CSV")
        return

    # Budget acumulado del Q para New MRR y New Logos (cuando es cierre de Q)
    if is_quarter_end:
        q_keys = [_cutoff_to_key(m) for m in _q_months_for(cutoff)]
        budget_q_new_mrr   = sum(budget_by_month.get(k, {}).get("New MRR",   0) for k in q_keys)
        budget_q_new_logos = sum(budget_by_month.get(k, {}).get("New Logos", 0) for k in q_keys)
    else:
        budget_q_new_mrr   = budget.get("New MRR",   0)
        budget_q_new_logos = budget.get("New Logos", 0)

    raw = out.get("_raw", {})

    def _pct(real, bud):
        if bud == 0:
            return "N/A", True
        delta = (real - bud) / bud * 100
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta:.1f}%", delta >= 0

    def _pp(real, bud):
        delta = real - bud
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta:.2f}"

    # ARR EoP
    if "ARR EoP" in budget:
        s, pos = _pct(raw.get("arr_eop", 0), budget["ARR EoP"])
        out["arr_vs_budget"] = s
        out["arr_vs_budget_positive"] = pos

    # New MRR (vs Q budget cuando es cierre de Q)
    if budget_q_new_mrr:
        s, pos = _pct(raw.get("new_mrr", 0), budget_q_new_mrr)
        out["new_mrr_vs_budget"] = s
        out["new_mrr_vs_budget_positive"] = pos

    # New Logos (vs Q budget cuando es cierre de Q)
    if budget_q_new_logos:
        s, pos = _pct(raw.get("new_logos", 0), budget_q_new_logos)
        out["new_logos_vs_budget"] = s

    # Churn Rate (pp delta: real - budget)
    if "Churn Rate" in budget:
        out["logo_churn_vs_budget_pp"] = _pp(raw.get("logo_churn_pct", 0), budget["Churn Rate"])

    print(f"✅ Budget mergeado para {month_key}: ARR {out['arr_vs_budget']} · "
          f"New MRR {out['new_mrr_vs_budget']} · New Logos {out['new_logos_vs_budget']} · "
          f"Churn {out['logo_churn_vs_budget_pp']}pp")


# ── P&L merge ──────────────────────────────────────────────────────────────────
def _pnl_date_str(cutoff):
    """'2026-02' → '2/28/2026' (último día del mes)."""
    y, m = int(cutoff[:4]), int(cutoff[5:])
    last = calendar.monthrange(y, m)[1]
    return f"{m}/{last}/{y}"

def _prev_cutoff(cutoff):
    """'2026-02' → '2026-01'."""
    y, m = int(cutoff[:4]), int(cutoff[5:])
    m -= 1
    if m == 0:
        m, y = 12, y - 1
    return f"{y}-{m:02d}"

def _yoy_cutoff(cutoff):
    """'2026-02' → '2025-02'."""
    return f"{int(cutoff[:4])-1}{cutoff[4:]}"

def _norm_cat(c):
    """Normaliza nombres de categoría con variaciones de mayúsculas."""
    return c.strip().lower()

# Mapeo de categorías normalizadas → clave interna
_CAT_MAP = {
    "income":                                        "income",
    "cost of revenue":                               "cor",
    "customer acquisition costs":                    "cac",
    "product (expensed)":                            "product",
    "general and administrative":                    "ga",
    "depreciation/amortization":                     "da",
    "taxes":                                         "taxes",
    "non - operating income/ expenses (net)":        "non_op",
    "non-operating income":                          "non_op",
    "interest expenses":                             "non_op",
    "financial yield":                               "fin_yield",
    "provisions":                                    "provisions",
    "interco":                                       "interco",
}

def _load_pnl_rows(filepath, date_str, amount_col):
    """Carga filas de un CSV de P&L para una fecha específica."""
    rows = []
    if not Path(filepath).exists():
        return rows
    with open(filepath, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Date", "").strip() == date_str:
                try:
                    val = float(str(row.get(amount_col, "0")).replace(",", "").strip() or 0)
                except ValueError:
                    val = 0.0
                norm = _norm_cat(row.get("Category", ""))
                rows.append({
                    "cat":  _CAT_MAP.get(norm, norm),
                    "type": row.get("Type", "").strip(),
                    "val":  val,
                })
    return rows

def _calc_pnl(rows):
    """Aplica la lógica de signos y calcula las líneas del P&L."""
    by_cat   = defaultdict(float)
    by_ctype = defaultdict(float)
    for r in rows:
        by_cat[r["cat"]]                  += r["val"]
        by_ctype[(r["cat"], r["type"])]   += r["val"]

    # ── Income ─────────────────────────────────────────────────────────────────
    op_inc  = by_ctype.get(("income", "Operating Income"), 0)
    refunds = by_ctype.get(("income", "Refunds"), 0)
    total_revenue = abs(op_inc) - abs(refunds)

    # ── CoR ────────────────────────────────────────────────────────────────────
    cor = abs(by_cat.get("cor", 0))

    # ── Gross ──────────────────────────────────────────────────────────────────
    gross_income   = total_revenue - cor
    gross_margin   = gross_income / total_revenue * 100 if total_revenue else 0

    # ── OpEx (sin CoR) ─────────────────────────────────────────────────────────
    cac     = abs(by_cat.get("cac", 0))
    product = abs(by_cat.get("product", 0))
    ga      = abs(by_cat.get("ga", 0))
    opex    = cac + product + ga

    # ── EBITDA ─────────────────────────────────────────────────────────────────
    ebitda        = gross_income - opex
    ebitda_margin = ebitda / total_revenue * 100 if total_revenue else 0

    # ── Below-EBITDA ───────────────────────────────────────────────────────────
    non_op    = by_cat.get("non_op", 0)     # viene negativo → restar = sumar
    fin_yield = by_cat.get("fin_yield", 0)  # viene negativo → restar = sumar
    da        = abs(by_cat.get("da", 0))
    taxes     = abs(by_cat.get("taxes", 0))

    net_income     = ebitda - non_op - da - fin_yield - taxes
    net_income_pct = net_income / total_revenue * 100 if total_revenue else 0

    # ── Provisions (invertir signo) ────────────────────────────────────────────
    provisions = by_cat.get("provisions", 0) * -1

    # ── Interco ────────────────────────────────────────────────────────────────
    ico_op_inc     = by_ctype.get(("interco", "Operating Income"), 0) * -1
    ico_non_op_inc = by_ctype.get(("interco", "Non-Operating Income"), 0) * -1
    ico_expenses   = by_ctype.get(("interco", "Interco Expenses"), 0)
    ico_cod        = by_ctype.get(("interco", "Cost of Debt"), 0)
    ico_taxes      = by_ctype.get(("interco", "Interco Taxes"), 0)
    total_interco  = (ico_op_inc + ico_non_op_inc) - (ico_expenses + ico_cod + ico_taxes)

    # ── Financial Outcome ──────────────────────────────────────────────────────
    fo     = net_income + provisions + total_interco
    fo_pct = fo / total_revenue * 100 if total_revenue else 0

    return {
        "total_revenue":   total_revenue,
        "gross_income":    gross_income,
        "gross_margin":    gross_margin,
        "cac":             cac,
        "product":         product,
        "ga":              ga,
        "opex":            opex,
        "ebitda":          ebitda,
        "ebitda_margin":   ebitda_margin,
        "net_income":      net_income,
        "net_income_pct":  net_income_pct,
        "provisions":      provisions,
        "total_interco":   total_interco,
        "fo":              fo,
        "fo_pct":          fo_pct,
    }

def merge_pnl(out, cutoff):
    """Lee los CSVs de P&L actual y budget, calcula métricas e inyecta en out."""
    if not PNL_ACTUAL.exists():
        print(f"⚠️  P&L Actual no encontrado: {PNL_ACTUAL}")
        return

    date_cur  = _pnl_date_str(cutoff)
    date_prev = _pnl_date_str(_prev_cutoff(cutoff))
    date_yoy  = _pnl_date_str(_yoy_cutoff(cutoff))

    rows_cur  = _load_pnl_rows(PNL_ACTUAL, date_cur,  "sum Amount USD")
    rows_prev = _load_pnl_rows(PNL_ACTUAL, date_prev, "sum Amount USD")
    rows_yoy  = _load_pnl_rows(PNL_ACTUAL, date_yoy,  "sum Amount USD")
    rows_bud  = _load_pnl_rows(PNL_BUDGET, date_cur,  "Amount") if PNL_BUDGET.exists() else []

    if not rows_cur:
        print(f"⚠️  P&L: sin filas para {date_cur}")
        return

    cur  = _calc_pnl(rows_cur)
    prev = _calc_pnl(rows_prev) if rows_prev else {}
    yoy  = _calc_pnl(rows_yoy)  if rows_yoy  else {}
    bud  = _calc_pnl(rows_bud)  if rows_bud  else {}

    def _pct_delta(a, b):
        if not b: return "N/A", True
        d = (a - b) / abs(b) * 100
        return f"{'+'if d>=0 else ''}{d:.1f}%", d >= 0

    def _pp_delta(a, b):
        if not b: return "N/A", True
        d = a - b
        return f"{'+'if d>=0 else ''}{d:.1f}pp", d >= 0

    def _fm_rev(v):
        if abs(v) >= 1e6: return f"${v/1e6:.1f}M"
        if abs(v) >= 1e3: return f"${v/1e3:.0f}K"
        return f"${v:.0f}"

    rev  = cur["total_revenue"]
    gm   = cur["gross_margin"]
    ebm  = cur["ebitda_margin"]

    # Net Revenue
    out["net_revenue"]                   = _fm_rev(rev)
    out["net_revenue_mom"], out["net_revenue_mom_positive"] = (
        _pct_delta(rev, prev.get("total_revenue", 0)) if prev else ("N/A", True))
    out["net_revenue_vs_budget"], out["net_revenue_vs_budget_positive"] = (
        _pct_delta(rev, bud.get("total_revenue", 0)) if bud else ("N/A", True))
    out["net_revenue_yoy"], out["net_revenue_yoy_positive"] = (
        _pct_delta(rev, yoy.get("total_revenue", 0)) if yoy else ("N/A", True))

    # Gross Margin %
    out["gross_margin"]                  = f"{gm:.1f}%"
    out["gross_margin_mom"], _           = (
        _pp_delta(gm, prev.get("gross_margin", 0)) if prev else ("N/A", True))
    out["gross_margin_vs_budget"], out["gross_margin_vs_budget_positive"] = (
        _pp_delta(gm, bud.get("gross_margin", 0)) if bud else ("N/A", True))
    out["gross_margin_yoy"], out["gross_margin_yoy_positive"] = (
        _pp_delta(gm, yoy.get("gross_margin", 0)) if yoy else ("N/A", True))

    # EBITDA Margin %
    out["ebitda_margin"]                 = f"{ebm:.1f}%"
    out["ebitda_margin_mom"], out["ebitda_margin_mom_positive"] = (
        _pp_delta(ebm, prev.get("ebitda_margin", 0)) if prev else ("N/A", True))
    out["ebitda_margin_vs_budget"], out["ebitda_margin_vs_budget_positive"] = (
        _pp_delta(ebm, bud.get("ebitda_margin", 0)) if bud else ("N/A", True))
    out["ebitda_margin_yoy"], out["ebitda_margin_yoy_positive"] = (
        _pp_delta(ebm, yoy.get("ebitda_margin", 0)) if yoy else ("N/A", True))

    print(f"✅ P&L mergeado para {date_cur}: "
          f"Revenue {out['net_revenue']} · GM {out['gross_margin']} · EBITDA {out['ebitda_margin']}")


# ── Payback merge ───────────────────────────────────────────────────────────────
def merge_payback(out, cutoff, payback_hist=16):
    """Lee Payback.csv e inyecta payback_core, payback_lite y payback_hist en out."""
    if not PAYBACK_FILE.exists():
        print(f"⚠️  Payback CSV no encontrado: {PAYBACK_FILE}")
        return

    # fecha en CSV: YYYY-MM
    date_str = cutoff  # ya viene como "2026-03"

    core_val = lite_val = None
    with open(PAYBACK_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("fecha", "").strip() == date_str and row.get("Type", "").strip() == "Todos":
                seg = row.get("Segment", "").strip()
                val = float(row.get("valor", 0) or 0)
                if seg == "Core":
                    core_val = val
                elif seg == "Lite":
                    lite_val = val

    if core_val is None or lite_val is None:
        print(f"⚠️  Payback: sin datos para {date_str}")
        return

    out["payback_core"] = round(core_val, 1)
    out["payback_lite"] = round(lite_val, 1)
    out["payback_hist"] = payback_hist

    print(f"✅ Payback mergeado para {date_str}: Core {out['payback_core']} mo · Lite {out['payback_lite']} mo · Hist {payback_hist} mo")


if __name__ == "__main__":
    main()
