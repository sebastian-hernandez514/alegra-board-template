#!/usr/bin/env python3
import re

path = "/Users/sebastian_alegra/Alegra IA/Template Board/slides/3_arr_walk.html"
with open(path) as f:
    html = f.read()

def bars(color, pattern):
    """Return 5-bar SVG sparkline. pattern: rise, fall, flat"""
    if pattern == 'rise':
        rects = [(2,11,5),(18,8,8),(34,6,10),(50,4,12),(66,2,14)]
    elif pattern == 'fall':
        rects = [(2,2,14),(18,4,12),(34,6,10),(50,8,8),(66,11,5)]
    else:  # flat
        rects = [(2,7,9),(18,5,11),(34,6,10),(50,7,9),(66,6,10)]
    inner = ''.join(f'<rect x="{x}" y="{y}" width="12" height="{h}" fill="{color}" rx="1"/>' for x,y,h in rects)
    return f'<svg class="bf-spark" viewBox="0 0 80 16">{inner}</svg>'

# Map: (points_snippet, color) -> bar svg
replacements = {
    ('0,14 20,10 40,7 60,4 80,1', '#534AB7'): bars('#534AB7', 'rise'),
    ('0,1 20,4 40,7 60,10 80,14', '#534AB7'): bars('#534AB7', 'fall'),
    ('0,8 20,6 40,9 60,7 80,8',   '#534AB7'): bars('#534AB7', 'flat'),
    ('0,14 20,10 40,7 60,4 80,1', '#1D9E75'): bars('#1D9E75', 'rise'),
    ('0,1 20,4 40,7 60,10 80,14', '#1D9E75'): bars('#1D9E75', 'fall'),
    ('0,8 20,6 40,9 60,7 80,8',   '#1D9E75'): bars('#1D9E75', 'flat'),
    ('0,1 20,4 40,7 60,10 80,14', '#D85A30'): bars('#D85A30', 'fall'),
}

for (pts, color), bar_svg in replacements.items():
    old = f'<svg class="bf-spark" viewBox="0 0 80 16" fill="none"><polyline points="{pts}" stroke="{color}" stroke-width="1.5" stroke-linejoin="round"/></svg>'
    html = html.replace(old, bar_svg)

with open(path, 'w') as f:
    f.write(html)

# Verify no polylines remain in bf-spark svgs
remaining = re.findall(r'class="bf-spark"[^>]*>.*?polyline', html)
print(f"Done. Remaining polylines in bf-spark: {len(remaining)}")
