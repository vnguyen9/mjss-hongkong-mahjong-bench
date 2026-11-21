"""Shared banner artwork for the README and the offline leaderboard."""

from .tile_art import FACES


def _tiles():
    # Body values follow global.css: .mahjong-tile, .tile-ivory and --slab-10.
    layers = ("#e5d1aa", "#dfc9a0", "#d8c096", "#d0b78b", "#c7ad80",
              "#bda375", "#b3986a", "#a88d60", "#9d8256", "#91764c")
    tiles = []
    for x, face in zip((354, 420, 486), FACES):
        body = "".join(f'<rect y="{i}" width="60" height="81" rx="11.4" fill="{colour}"/>'
                       for i, colour in reversed(list(enumerate(layers, 1))))
        tiles.append(f'<g transform="translate({x} 24)">'
                     '<rect y="10" width="60" height="81" rx="11.4" fill="#000" opacity=".32" filter="url(#tile-shadow)"/>'
                     f'{body}<rect width="60" height="81" rx="11.4" fill="url(#ivory)" stroke="#d8c299"/>'
                     '<rect x=".5" y=".5" width="59" height="80" rx="10.9" fill="none" stroke="#fff" stroke-opacity=".5"/>'
                     f'<g transform="translate(1 1) scale(.58)">{face}</g></g>')
    return "".join(tiles)


def banner(dark=False):
    bg, ink, muted = (("#111e1b", "#edf5ee", "#a5bcb2") if dark else
                      ("#edf5ef", "#173d30", "#526c60"))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 250" role="img" aria-labelledby="banner-title">
<title id="banner-title">Hong Kong Mahjong Bench</title>
<rect width="900" height="250" rx="18" fill="{bg}"/>
<defs>
<linearGradient id="ivory" x1="0" y1="0" x2=".7" y2="1"><stop stop-color="#f8efdb"/><stop offset="1" stop-color="#e7d2ac"/></linearGradient>
<filter id="tile-shadow" x="-50%" y="-30%" width="200%" height="190%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>
{_tiles()}
<text x="450" y="165" text-anchor="middle" fill="{ink}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="40" font-weight="700" letter-spacing="-1">Hong Kong Mahjong Bench</text>
<text x="450" y="204" text-anchor="middle" fill="{muted}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="17">Every player faces the same deals.</text>
</svg>'''
