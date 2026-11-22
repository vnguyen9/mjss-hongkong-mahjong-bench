"""Shared banner artwork for the README and the offline leaderboard."""

from .tile_art import FACES


def _tiles():
    # Flat ivory faces, fanned like the first banner: outer tiles turned 12 degrees.
    tiles = []
    for cx, turn, face in zip((388, 450, 512), (-12, 0, 12), FACES):
        tiles.append(f'<g transform="rotate({turn} {cx} 61) translate({cx - 26} 26)">'
                     '<rect width="52" height="70.2" rx="9.9" fill="url(#ivory)" stroke="#d8c299" stroke-width="1.5"/>'
                     f'<g transform="scale(.52)">{face}</g></g>')
    return "".join(tiles)


def banner(dark=False):
    bg, ink, muted = (("#111e1b", "#edf5ee", "#a5bcb2") if dark else
                      ("#edf5ef", "#173d30", "#526c60"))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 224" role="img" aria-labelledby="banner-title">
<title id="banner-title">Hong Kong Mahjong Bench</title>
<rect width="900" height="224" rx="18" fill="{bg}"/>
<defs>
<linearGradient id="ivory" x1="0" y1="0" x2=".7" y2="1"><stop stop-color="#f8efdb"/><stop offset="1" stop-color="#e7d2ac"/></linearGradient>
</defs>
{_tiles()}
<text x="450" y="150" text-anchor="middle" fill="{ink}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="40" font-weight="700" letter-spacing="-1">Hong Kong Mahjong Bench</text>
<text x="450" y="189" text-anchor="middle" fill="{muted}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="17">An open benchmark for Hong Kong Mahjong AI.</text>
</svg>'''
