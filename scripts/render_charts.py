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

#: id, title, what the table is ranked by. Chicken hand pays every win the same, so it is ranked by win rate.
TABLES = [("hk-hkma-v1", "HKMA Classical", "points_per_hand"), ("hk-house-v1", "House", "points_per_hand"),
          ("hk-chicken-v2", "Chicken hand", "win_rate")]


def chart(rows, dark=False):
    bg, ink, muted, grid, bar, accent = (("#0d1117", "#e6edf3", "#a4b1bd", "#303b43", "#6b8190", "#75d9b1") if dark else
                                        ("#ffffff", "#1f2933", "#576574", "#dce4e7", "#a1b3bc", "#20785b"))
    groups = [sorted([r for r in rows if r['table'] == tid], key=lambda r: -r['value']) for tid, _, _ in TABLES]
    # Each panel is as tall as its rows: title, rows and axis labels, then a gap before the next panel.
    height = sum(165 + len(g) * 30 for g in groups) - 10
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 {height}" role="img" aria-labelledby="chart-title chart-desc">',
             '<title id="chart-title">Verified private-deck results</title>',
             '<desc id="chart-desc">Every bot, sorted within each table by points a hand, or by win rate on Chicken hand. Whiskers show 95% confidence intervals. Each panel has its own scale.</desc>',
             f'<rect width="640" height="{height}" rx="12" fill="{bg}"/>',
             f'<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" fill="{ink}">']
    def text(x, y, value, size=17, **attrs):
        extra = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{escape(str(value))}</text>')
    top = 35
    for group, (tid, title, metric) in zip(groups, TABLES):
        by_wins = metric == 'win_rate'
        text(20, top, title, 22, font_weight="700")
        text(20, top + 26, tid, 14, fill=muted)
        low = min([0] + [r['ci95'][0] for r in group])
        high = max([0] + [r['ci95'][1] for r in group])
        rough = (high - low or 1) / 5
        power = 10 ** math.floor(math.log10(rough))
        fraction = rough / power
        step = (1 if fraction < 1.5 else 2 if fraction < 3 else 5 if fraction < 7 else 10) * power
        if metric == 'win_rate':
            step = 0.2  # the axis is short, so label every 20%
        lo, hi = math.floor(low / step) * step, math.ceil(high / step) * step
        text(620, top + 26, 'Win rate' if by_wins else 'Mean', 16, text_anchor="end", fill=muted)
        if by_wins:
            text(545, top + 26, 'Deal-in', 16, text_anchor="end", fill=muted)
        show = (lambda v: f'{100 * v:.1f}%') if by_wins else (lambda v: f'{v:+.2f}')
        axis_end = 470 if by_wins else 540
        def x(v): return 290 + (v - lo) / (hi - lo or 1) * (axis_end - 290)
        bottom = top + 55 + len(group) * 30
        for i in range(round((hi - lo) / step) + 1):
            v = lo + step * i
            px = x(v)
            parts.append(f'<path d="M{px:.2f} {top+45}V{bottom}" stroke="{grid}"/>')
            text(f'{px:.2f}', bottom + 24, (f'{round(100 * v, 6):g}%' if by_wins else f'{v:g}'), 16, text_anchor="middle", fill=muted)
        parts.append(f'<path d="M{x(0):.2f} {top+45}V{bottom}" stroke="{muted}"/>')
        for i, r in enumerate(group):
            y = top + 61 + i * 30
            name, mean = r['bot']['name'], r['value']
            a, b = r['ci95']
            colour = accent if name == 'Fu-2.3M-HKMA-1' else bar
            text(20, y + 5, name, 18, fill=accent if name == 'Fu-2.3M-HKMA-1' else ink,
                 font_weight="700" if name == 'Fu-2.3M-HKMA-1' else "400")
            parts.append(f'<g><title>{escape(name)}: {show(mean)} [{show(a)}, {show(b)}]</title>'
                         f'<rect x="{min(x(0),x(mean)):.2f}" y="{y-8}" width="{max(1,abs(x(mean)-x(0))):.2f}" height="16" rx="3" fill="{colour}"/>'
                         f'<path d="M{x(a):.2f} {y}H{x(b):.2f}M{x(a):.2f} {y-5}v10M{x(b):.2f} {y-5}v10" stroke="{ink}" stroke-width="1.5"/>'
                         '</g>')
            text(620, y + 5, show(mean), 20, text_anchor="end", font_weight="600")
            if by_wins:
                text(545, y + 5, f"{100 * r['deal_in_rate']:.1f}%", 16, text_anchor="end", fill=muted)
        text((290 + axis_end) / 2, bottom + 47, 'Win rate · 95% CI' if by_wins else 'Points a hand · 95% CI', 16, text_anchor="middle", fill=muted)
        top = bottom + 110
    parts.append('</g></svg>')
    return '\n'.join(parts) + '\n'


def main():
    out = ROOT / 'docs' / 'assets'
    out.mkdir(parents=True, exist_ok=True)
    shown = {tid for tid, _, _ in TABLES}  # a retired table's rows stay in results/ and are not drawn
    rows = [r for r in _latest(_rows(ROOT / 'results')) if r['seed_tag'] == 'private' and r['verification'] == 'verified' and r['table'] in shown]
    for theme in ('light', 'dark'):
        (out / f'banner-{theme}.svg').write_text(banner(theme == 'dark') + '\n', encoding='utf-8')
        (out / f'results-{theme}.svg').write_text(chart(rows, theme == 'dark'), encoding='utf-8')
    print(f'Rendered {len(rows)} verified private-deck rows across {len(TABLES)} tables.')


if __name__ == '__main__':
    main()
