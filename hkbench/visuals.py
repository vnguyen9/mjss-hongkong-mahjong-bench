"""Original vector artwork shared by the README and the offline leaderboard."""


def banner(dark=False):
    bg, ink, muted, jade, tile = (("#111e1b", "#edf5ee", "#a5bcb2", "#75d9b1", "#1c342c") if dark else
                                 ("#edf5ef", "#173d30", "#526c60", "#20785b", "#ffffff"))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 250" role="img" aria-labelledby="banner-title">
<title id="banner-title">Hong Kong Mahjong Bench</title>
<rect width="900" height="250" rx="18" fill="{bg}"/>
<g fill="{tile}" stroke="{jade}" stroke-width="2">
<rect x="377" y="28" width="42" height="57" rx="7" transform="rotate(-12 398 57)"/>
<rect x="429" y="23" width="42" height="57" rx="7"/>
<rect x="481" y="28" width="42" height="57" rx="7" transform="rotate(12 502 57)"/>
</g>
<g fill="{jade}"><circle cx="398" cy="56" r="7"/><circle cx="442" cy="42" r="4"/>
<circle cx="458" cy="61" r="4"/><path d="M496 46h12v20h-12z"/></g>
<text x="450" y="140" text-anchor="middle" fill="{ink}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="40" font-weight="700" letter-spacing="-1">Hong Kong Mahjong Bench</text>
<text x="450" y="183" text-anchor="middle" fill="{muted}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="17">Every player faces the same deals.</text>
<path d="M415 213h70" stroke="{jade}" stroke-width="3"/>
</svg>'''
