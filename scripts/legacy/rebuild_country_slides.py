#!/usr/bin/env python3
# Rebuilds the 4 Country Performance slides with butterfly layout

import re

PATH = '/Users/sebastian_alegra/Alegra IA/Template Board/slides/3_arr_walk.html'

with open(PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ── CSS ────────────────────────────────────────────────────────────────────
BF_CSS = """
    /* ── Butterfly Country Performance ── */
    .bf-cards { display: flex; border-bottom: 1px solid #eaeaea; flex-shrink: 0; }
    .bf-card { flex: 1; padding: 13px 36px; text-align: center; }
    .bf-card:first-child { border-right: 1px solid #eaeaea; }
    .bf-card-label { font-size: 11px; font-weight: 700; letter-spacing: .08em; margin-bottom: 4px; }
    .bf-card-label.c { color: #534AB7; } .bf-card-label.l { color: #1D9E75; }
    .bf-card-value { font-size: 32px; font-weight: 800; color: #111; margin: 2px 0; letter-spacing: -1.5px; }
    .bf-card-sub { font-size: 11px; color: #888; }
    .bf-table { padding: 6px 28px 0; overflow: hidden; }
    .bf-row { display: flex; align-items: center; padding: 5px 0; border-bottom: 1px solid #f0f0f0; }
    .bf-row:last-child { border-bottom: none; }
    .bf-row.bf-head { border-bottom: 2px solid #eaeaea; padding: 3px 0; }
    .bf-core, .bf-lite { flex: 1; display: flex; align-items: center; }
    .bf-core { justify-content: flex-end; padding-right: 8px; }
    .bf-lite { justify-content: flex-start; padding-left: 8px; }
    .bf-metric { width: 130px; text-align: center; font-size: 11px; font-weight: 600; color: #222; background: #f8f8f6; padding: 4px 5px; border-radius: 4px; flex-shrink: 0; line-height: 1.3; }
    .bf-val { width: 66px; font-size: 12px; font-weight: 700; color: #111; }
    .bf-core .bf-val { text-align: right; }
    .bf-lite .bf-val { text-align: left; }
    .bf-val.neg { color: #D85A30; }
    .bf-delta { width: 50px; font-size: 10px; text-align: center; font-weight: 500; color: #888; }
    .bf-pos { color: #1D9E75; } .bf-neg { color: #D85A30; }
    .bf-spark { width: 44px; height: 14px; flex-shrink: 0; }
"""

content = content.replace('  </style>', BF_CSS + '  </style>', 1)

# ── Helpers ────────────────────────────────────────────────────────────────
def spk(color, pts):
    return f'<svg class="bf-spark" viewBox="0 0 80 16" fill="none"><polyline points="{pts}" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/></svg>'

C = "#534AB7"; L = "#1D9E75"; R = "#D85A30"
RISE = "0,14 20,10 40,7 60,4 80,1"
FALL = "0,1 20,4 40,7 60,10 80,14"
FLAT = "0,8 20,6 40,9 60,7 80,8"

def p(v): return f'<div class="bf-delta bf-pos">{v}</div>'
def n(v): return f'<div class="bf-delta bf-neg">{v}</div>'
def u(v): return f'<div class="bf-delta">{v}</div>'
def vc(v, neg=False): return f'<div class="bf-val{" neg" if neg else ""}">{v}</div>'

HEAD = ('        <div class="bf-row bf-head">'
        '<div class="bf-core"><div class="bf-spark"></div>'
        '<div class="bf-delta" style="font-size:9px;font-weight:700;color:#bbb;letter-spacing:.05em;text-transform:uppercase;">YoY</div>'
        '<div class="bf-delta" style="font-size:9px;font-weight:700;color:#bbb;letter-spacing:.05em;text-transform:uppercase;">MoM</div>'
        '<div class="bf-val" style="font-size:9px;font-weight:700;color:#bbb;letter-spacing:.05em;text-transform:uppercase;text-align:right;">VALUE</div></div>'
        '<div class="bf-metric" style="background:none;color:#bbb;font-size:9px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;">METRIC</div>'
        '<div class="bf-lite"><div class="bf-val" style="font-size:9px;font-weight:700;color:#bbb;letter-spacing:.05em;text-transform:uppercase;">VALUE</div>'
        '<div class="bf-delta" style="font-size:9px;font-weight:700;color:#bbb;letter-spacing:.05em;text-transform:uppercase;">MoM</div>'
        '<div class="bf-delta" style="font-size:9px;font-weight:700;color:#bbb;letter-spacing:.05em;text-transform:uppercase;">YoY</div>'
        '<div class="bf-spark"></div></div></div>')

def row(metric, cs, cyoy, cmom, cv, lv, lmom, lyoy, ls, cneg=False, lneg=False):
    return (f'        <div class="bf-row">'
            f'<div class="bf-core">{cs}{cyoy}{cmom}{vc(cv,cneg)}</div>'
            f'<div class="bf-metric">{metric}</div>'
            f'<div class="bf-lite">{vc(lv,lneg)}{lmom}{lyoy}{ls}</div>'
            f'</div>')

def cards(c_arr, c_mom, c_mom_cls, c_yoy, c_yoy_cls,
          l_arr, l_mom, l_mom_cls, l_yoy, l_yoy_cls):
    return (f'      <div class="bf-cards">'
            f'<div class="bf-card"><div class="bf-card-label c">● CORE</div>'
            f'<div class="bf-card-value">{c_arr}</div>'
            f'<div class="bf-card-sub">ARR &nbsp;<span class="{c_mom_cls}">{c_mom}</span> MoM &nbsp;<span class="{c_yoy_cls}">{c_yoy}</span> YoY</div></div>'
            f'<div class="bf-card"><div class="bf-card-label l">● LITE</div>'
            f'<div class="bf-card-value">{l_arr}</div>'
            f'<div class="bf-card-sub">ARR &nbsp;<span class="{l_mom_cls}">{l_mom}</span> MoM &nbsp;<span class="{l_yoy_cls}">{l_yoy}</span> YoY</div></div>'
            f'</div>')

def bf_table(rows_html):
    return ('      <div class="bf-table">\n'
            + HEAD + '\n'
            + '\n'.join(rows_html)
            + '\n      </div>')

def new_cp(cards_html, table_html):
    return '<div class="cp-inner">\n' + cards_html + '\n' + table_html + '\n    </div>'

# ── Replace helper ─────────────────────────────────────────────────────────
def replace_country(html, country_comment, new_cp_inner):
    pos = html.find(country_comment)
    assert pos != -1, f"Not found: {country_comment}"
    cp_start = html.find('<div class="cp-inner">', pos)
    footer_start = html.find('<div class="slide-footer">', cp_start)
    cp_end = html.rfind('</div>', cp_start, footer_start) + len('</div>')
    return html[:cp_start] + new_cp_inner + '\n    ' + html[cp_end:]

# ══════════════════════════════════════════════════════════════════════════
# COLOMBIA
# ══════════════════════════════════════════════════════════════════════════
co_rows = [
    row("Investment",
        spk(C,RISE), n("−12.6%"), p("+19.4%"), "197,892",
        "126,423", p("+13.3%"), n("−25.3%"), spk(L,FLAT)),
    row("Net New ARR",
        spk(R,FALL), n("−106.3%"), n("−148.7%"), "−40,238",
        "−121,908", n("−995.2%"), n("−121.7%"), spk(R,FALL), True, True),
    row("Total Logos Growth",
        spk(C,RISE), p("+16.5%"), p("+0.4%"), "64",
        "−340", n("−1.3%"), n("−4.0%"), spk(R,FALL), False, True),
    row("New Logos",
        spk(C,FLAT), p("+11.5%"), n("−14.8%"), "611",
        "811", n("−8.8%"), n("−20.0%"), spk(L,FALL)),
    row("New ARR",
        spk(C,RISE), p("+24.6%"), p("+2.0%"), "261,586",
        "213,301", u("0.0%"), p("+24.3%"), spk(L,RISE)),
    row("ARPA",
        spk(C,RISE), p("+16.6%"), n("−0.8%"), "$52",
        "$22", n("−0.5%"), p("+19.6%"), spk(L,RISE)),
    row("CAC",
        spk(C,FALL), p("−21.6%"), p("−2.8%"), "$324",
        "$156", n("+7.2%"), p("−6.6%"), spk(L,FLAT)),
    row("Churn",
        spk(C,FLAT), n("+1.7%"), p("−3.2%"), "4.1%",
        "6.1%", n("+3.3%"), p("−16.7%"), spk(L,FLAT)),
    row("Payback",
        spk(C,FLAT), p("−52.6%"), n("+11.4%"), "6.7m",
        "6.6m", n("+9.5%"), p("−53.4%"), spk(L,FLAT)),
]
co_cards = cards("$8.2M","+19.4%","bf-pos","−12.6%","bf-neg",
                 "$4.1M","+13.3%","bf-pos","−25.3%","bf-neg")
content = replace_country(content, "Countries Performance — Colombia",
                          new_cp(co_cards, bf_table(co_rows)))

# ══════════════════════════════════════════════════════════════════════════
# MÉXICO
# ══════════════════════════════════════════════════════════════════════════
mx_rows = [
    row("Investment",
        spk(C,RISE), n("−18.1%"), p("+8.2%"), "142,300",
        "98,400", p("+22.5%"), n("−28.4%"), spk(L,FLAT)),
    row("Net New ARR",
        spk(R,FALL), n("−52.3%"), n("−110.2%"), "−18,400",
        "−22,600", n("−145.3%"), n("−18.7%"), spk(R,FALL), True, True),
    row("Total Logos Growth",
        spk(C,FALL), p("+8.4%"), n("−1.2%"), "−532",
        "−1,820", n("−3.4%"), n("−5.1%"), spk(R,FALL), True, True),
    row("New Logos",
        spk(C,FALL), n("−8.2%"), n("−14.0%"), "620",
        "780", n("−18.2%"), n("−22.4%"), spk(L,FALL)),
    row("New ARR",
        spk(C,RISE), p("+42.1%"), n("−8.3%"), "198,400",
        "164,200", n("−12.4%"), p("+38.6%"), spk(L,RISE)),
    row("ARPA",
        spk(C,RISE), p("+22.4%"), p("+1.2%"), "$48",
        "$21", n("−0.8%"), p("+28.1%"), spk(L,RISE)),
    row("CAC",
        spk(C,FALL), p("−18.7%"), p("−32.4%"), "$228",
        "$108", p("−28.6%"), p("−6.4%"), spk(L,FALL)),
    row("Churn",
        spk(C,FLAT), n("+31.4%"), n("+55.2%"), "5.8%",
        "7.1%", n("+18.2%"), n("+8.4%"), spk(L,FLAT)),
    row("Payback",
        spk(C,FALL), p("−48.3%"), p("−14.2%"), "6.8m",
        "5.9m", p("−34.8%"), p("−52.1%"), spk(L,FALL)),
]
mx_cards = cards("$6.8M","+8.2%","bf-pos","−18.1%","bf-neg",
                 "$3.2M","+22.5%","bf-pos","−28.4%","bf-neg")
content = replace_country(content, "Countries Performance — México",
                          new_cp(mx_cards, bf_table(mx_rows)))

# ══════════════════════════════════════════════════════════════════════════
# REPÚBLICA DOMINICANA
# ══════════════════════════════════════════════════════════════════════════
dr_rows = [
    row("Investment",
        spk(C,RISE), p("+18.6%"), p("+22.4%"), "48,200",
        "31,400", p("+18.1%"), p("+24.3%"), spk(L,RISE)),
    row("Net New ARR",
        spk(C,RISE), p("+82.1%"), p("+38.4%"), "42,800",
        "38,100", p("+28.6%"), p("+64.2%"), spk(L,RISE)),
    row("Total Logos Growth",
        spk(C,RISE), p("+24.6%"), p("+1.8%"), "508",
        "312", p("+0.8%"), p("+18.4%"), spk(L,RISE)),
    row("New Logos",
        spk(C,RISE), p("+32.1%"), p("+8.3%"), "390",
        "482", p("+12.4%"), p("+28.6%"), spk(L,RISE)),
    row("New ARR",
        spk(C,RISE), p("+96.4%"), p("+14.2%"), "86,400",
        "64,800", p("+18.6%"), p("+88.2%"), spk(L,RISE)),
    row("ARPA",
        spk(C,RISE), p("+41.2%"), p("+2.1%"), "$34",
        "$12", p("+3.4%"), p("+38.6%"), spk(L,RISE)),
    row("CAC",
        spk(C,FALL), p("−14.2%"), p("−28.4%"), "$124",
        "$65", p("−22.8%"), p("−8.6%"), spk(L,FALL)),
    row("Churn",
        spk(C,FLAT), n("+8.4%"), p("−0.3%"), "3.9%",
        "4.8%", p("−2.1%"), n("+4.2%"), spk(L,FLAT)),
    row("Payback",
        spk(C,FALL), p("−52.4%"), p("−18.6%"), "4.2m",
        "3.8m", p("−28.4%"), p("−61.2%"), spk(L,FALL)),
]
dr_cards = cards("$1.8M","+22.4%","bf-pos","+18.6%","bf-pos",
                 "$0.9M","+18.1%","bf-pos","+24.3%","bf-pos")
content = replace_country(content, "Countries Performance — República Dominicana",
                          new_cp(dr_cards, bf_table(dr_rows)))

# ══════════════════════════════════════════════════════════════════════════
# COSTA RICA
# ══════════════════════════════════════════════════════════════════════════
cr_rows = [
    row("Investment",
        spk(C,RISE), p("+22.8%"), p("+10.4%"), "38,400",
        "22,100", p("+14.2%"), p("+19.6%"), spk(L,RISE)),
    row("Net New ARR",
        spk(C,RISE), p("+48.4%"), p("+18.6%"), "28,400",
        "11,200", p("+8.4%"), p("+32.6%"), spk(L,RISE)),
    row("Total Logos Growth",
        spk(C,RISE), p("+18.4%"), p("+0.8%"), "227",
        "−88", n("−0.6%"), p("+12.2%"), spk(L,FLAT), False, True),
    row("New Logos",
        spk(C,RISE), p("+14.8%"), p("+5.1%"), "227",
        "318", p("+4.2%"), p("+8.6%"), spk(L,RISE)),
    row("New ARR",
        spk(C,RISE), p("+52.4%"), p("+6.8%"), "62,400",
        "38,200", p("+4.2%"), p("+46.8%"), spk(L,RISE)),
    row("ARPA",
        spk(C,RISE), p("+36.4%"), p("+1.8%"), "$34",
        "$11", u("0.0%"), p("+28.4%"), spk(L,RISE)),
    row("CAC",
        spk(C,FALL), p("−12.8%"), p("−22.4%"), "$110",
        "$58", p("−18.6%"), p("−8.2%"), spk(L,FALL)),
    row("Churn",
        spk(C,FLAT), n("+6.8%"), u("0.0%"), "4.2%",
        "4.9%", n("+4.2%"), n("+2.4%"), spk(L,FLAT)),
    row("Payback",
        spk(C,FALL), p("−44.2%"), p("−12.4%"), "4.8m",
        "4.2m", p("−18.6%"), p("−58.4%"), spk(L,FALL)),
]
cr_cards = cards("$1.4M","+10.4%","bf-pos","+22.8%","bf-pos",
                 "$0.7M","+14.2%","bf-pos","+19.6%","bf-pos")
content = replace_country(content, "Countries Performance — Costa Rica",
                          new_cp(cr_cards, bf_table(cr_rows)))

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done — 4 countries rebuilt with butterfly layout.")
