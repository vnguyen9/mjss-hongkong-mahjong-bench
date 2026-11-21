#!/usr/bin/env python3
"""Rebuild the original banners and verified private-deck charts with the standard library."""
import math
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hkbench.site import _latest, _rows
from hkbench.visuals import banner

TABLES = [("hk-hkma-v1", "HKMA Classical"), ("hk-house-v1", "House"), ("hk-chicken-v1", "Chicken hand")]


def chart(rows, dark=False):
    bg, ink, muted, grid, bar, accent = (("#0d1117", "#e6edf3", "#a4b1bd", "#303b43", "#6b8190", "#75d9b1") if dark else
                                        ("#ffffff", "#1f2933", "#576574", "#dce4e7", "#a1b3bc", "#20785b"))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 1100" role="img" aria-labelledby="chart-title chart-desc">',
             '<title id="chart-title">Verified private-deck results</title>',
             '<desc id="chart-desc">Every bot, sorted by points a hand within each table. Whiskers show 95% intervals. Each panel has its own scale.</desc>',
             f'<rect width="640" height="1100" rx="12" fill="{bg}"/>',
             f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" fill="{ink}">']
    def text(x, y, value, size=17, **attrs):
        extra = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{escape(str(value))}</text>')
    for panel, (tid, title) in enumerate(TABLES):
        group = sorted([r for r in rows if r['table'] == tid], key=lambda r: -r['points_per_hand'])
        top = 35 + panel * 360
        text(20, top, title, 22, font_weight="700")
        text(20, top + 26, tid, 14, fill=muted)
        low = min([0] + [r['ci95'][0] for r in group])
        high = max([0] + [r['ci95'][1] for r in group])
        rough = (high - low or 1) / 5
        power = 10 ** math.floor(math.log10(rough))
        fraction = rough / power
        step = (1 if fraction < 1.5 else 2 if fraction < 3 else 5 if fraction < 7 else 10) * power
        lo, hi = math.floor(low / step) * step, math.ceil(high / step) * step
        text(620, top + 26, 'Mean', 16, text_anchor="end", fill=muted)
        def x(v): return 210 + (v - lo) / (hi - lo or 1) * 318
        bottom = top + 55 + len(group) * 30
        for i in range(round((hi - lo) / step) + 1):
            v = lo + step * i
            px = x(v)
            parts.append(f'<path d="M{px:.2f} {top+45}V{bottom}" stroke="{grid}"/>')
            text(f'{px:.2f}', bottom + 24, f'{v:g}', 18, text_anchor="middle", fill=muted)
        parts.append(f'<path d="M{x(0):.2f} {top+45}V{bottom}" stroke="{muted}"/>')
        for i, r in enumerate(group):
            y = top + 61 + i * 30
            name, mean = r['bot']['name'], r['points_per_hand']
            a, b = r['ci95']
            colour = accent if name == 'Fu-2.3M-HKMA-1' else bar
            text(20, y + 5, name, 20, fill=accent if name == 'Fu-2.3M-HKMA-1' else ink,
                 font_weight="700" if name == 'Fu-2.3M-HKMA-1' else "400")
            parts.append(f'<g><title>{escape(name)}: {mean:+.2f} [{a:+.2f}, {b:+.2f}]</title>'
                         f'<rect x="{min(x(0),x(mean)):.2f}" y="{y-8}" width="{max(1,abs(x(mean)-x(0))):.2f}" height="16" rx="3" fill="{colour}"/>'
                         f'<path d="M{x(a):.2f} {y}H{x(b):.2f}M{x(a):.2f} {y-5}v10M{x(b):.2f} {y-5}v10" stroke="{ink}" stroke-width="1.5"/>'
                         '</g>')
            text(620, y + 5, f'{mean:+.2f}', 20, text_anchor="end", font_weight="600")
        text(369, bottom + 47, 'Points a hand · 95% interval', 18, text_anchor="middle", fill=muted)
    parts.append('</g></svg>')
    return '\n'.join(parts) + '\n'


def main():
    out = ROOT / 'docs' / 'assets'
    out.mkdir(parents=True, exist_ok=True)
    rows = [r for r in _latest(_rows(ROOT / 'results')) if r['seed_tag'] == 'private' and r['verification'] == 'verified']
    for theme in ('light', 'dark'):
        (out / f'banner-{theme}.svg').write_text(banner(theme == 'dark') + '\n', encoding='utf-8')
        (out / f'results-{theme}.svg').write_text(chart(rows, theme == 'dark'), encoding='utf-8')
    print(f'Rendered {len(rows)} verified private-deck rows across {len(TABLES)} tables.')


if __name__ == '__main__':
    main()
