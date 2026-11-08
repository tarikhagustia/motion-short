"""hud kit: sci-fi simulation pieces for the `hud` style.

    import sys; sys.path[:0] = ["<skill>/scripts", "<skill>/styles/hud"]
    from svgkit import *          # base helpers: write_scene, group, depth, cover, mix, shade ...
    from kit import *             # this file

Look: near-black background, neon cyan (`C`) lines and glows, hot orange (`O`) for heat / danger /
the key number, thin mono labels, panels with cut corners, segmented meters, rotating dot globes.
The fixed screen chrome (corner brackets, SIM title, STATUS, clock) comes from the style itself:
set it with storyboard `chrome` (top level) and per-scene `chrome: {"status": "JATUH"}`.
"""
import math
import random

from svgkit import _id, f, mix, shade, group, depth

C = "#5fe3ff"      # cyan
C2 = "#9cefff"     # light cyan
O = "#ffae4a"      # orange
O2 = "#ff7a2f"     # deep orange
BG = "#04080c"
INK = "#e9f8ff"

# rough continent outlines (lon, lat) for the dot globe; recognisable at dot resolution
CONTINENTS = [
    [(-168, 66), (-140, 70), (-95, 72), (-80, 64), (-60, 55), (-55, 47), (-70, 43), (-76, 35), (-81, 25), (-97, 26), (-97, 18), (-87, 15), (-80, 8),
     (-92, 15), (-106, 23), (-117, 32), (-124, 40), (-124, 48), (-135, 58), (-152, 60), (-166, 60)],                      # North America
    [(-80, 9), (-75, 11), (-62, 10), (-50, 2), (-35, -6), (-39, -14), (-48, -26), (-58, -35), (-65, -42), (-70, -54), (-74, -45), (-71, -30),
     (-70, -18), (-77, -10), (-81, -4), (-78, 2)],                                                                            # South America
    [(-10, 36), (10, 37), (32, 31), (43, 12), (51, 11), (40, -3), (40, -15), (33, -26), (20, -35), (14, -25), (12, -6), (9, 4), (-8, 4), (-17, 14), (-17, 21)],  # Africa
    [(-10, 36), (-9, 43), (-2, 48), (5, 52), (8, 58), (20, 70), (30, 71), (40, 66), (40, 46), (28, 41), (20, 38), (12, 44), (3, 43)],   # Europe
    [(40, 66), (70, 73), (110, 77), (140, 72), (180, 68), (170, 60), (155, 58), (140, 52), (135, 43), (122, 40), (122, 30), (110, 20),
     (106, 10), (100, 14), (98, 8), (92, 21), (80, 14), (77, 8), (72, 20), (62, 25), (56, 27), (48, 30), (35, 32), (36, 37), (40, 46)],  # Asia
    [(35, 30), (44, 13), (52, 16), (58, 22), (56, 26), (48, 29)],                                                             # Arabia
    [(114, -22), (122, -18), (130, -12), (137, -12), (142, -11), (146, -18), (153, -26), (150, -37), (141, -38), (131, -31), (116, -34), (114, -27)],  # Australia
    [(95, 5), (98, 4), (104, -2), (106, -6), (100, -3), (96, 2)],                                                             # Sumatra
    [(105, -6), (114, -7), (116, -8.5), (106, -7.5)],                                                                         # Java
    [(109, 1), (112, 3), (117, 7), (119, 1), (116, -4), (110, -3)],                                                           # Borneo
    [(119, 1), (125, 1), (122, -5), (120, -5)],                                                                               # Sulawesi
    [(131, -1), (141, -3), (150, -10), (141, -9), (134, -4)],                                                                 # New Guinea
    [(-52, 60), (-20, 70), (-25, 82), (-60, 82), (-72, 77)],                                                                  # Greenland
    [(130, 31), (135, 34), (141, 41), (142, 45), (138, 37), (132, 33)],                                                       # Japan
    [(-6, 50), (2, 52), (-3, 58), (-6, 56)],                                                                                  # UK
    [(44, -25), (50, -15), (49, -12), (44, -17)],                                                                             # Madagascar
]


def _inside(x, y, poly):
    n, ins = len(poly), False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            ins = not ins
        j = i
    return ins


def land_points(step=3.2):
    pts = []
    lat = -60.0
    while lat <= 82:
        dlon = step / max(math.cos(math.radians(lat)), .2)
        lon = -180.0
        while lon < 180:
            if any(_inside(lon, lat, p) for p in CONTINENTS):
                pts.append((lat, lon))
            lon += dlon
        lat += step
    return pts


# ---------------------------------------------------------------- backgrounds
def space_bg(seed=0, stars_n=90, grid=True, tint=None):
    """Near-black screen with a faint cyan grid, a soft central bloom and twinkling stars."""
    tint = tint or "#0b2533"
    r = random.Random(seed)
    gid, pid = _id("sb"), _id("gr")
    s = (f'<defs><radialGradient id="{gid}" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="{tint}"/>'
         f'<stop offset="1" stop-color="{BG}"/></radialGradient>'
         f'<pattern id="{pid}" width="60" height="60" patternUnits="userSpaceOnUse"><path d="M60,0 L0,0 0,60" fill="none" stroke="{C}" stroke-width="1" opacity=".09"/></pattern></defs>'
         f'<rect width="1080" height="1920" fill="url(#{gid})"/>')
    if grid:
        s += f'<rect width="1080" height="1920" fill="url(#{pid})"/>'
    s += "".join(f'<circle cx="{r.uniform(0,1080):.0f}" cy="{r.uniform(0,1920):.0f}" r="{r.uniform(.8,2.2):.1f}" fill="{C2}" '
                 f'data-anim="twinkle" data-phase="{r.uniform(0,6):.2f}"/>' for _ in range(stars_n))
    return s


def glow(x, y, r, color=C, opacity=.5, pulse=True):
    gid = _id("gl")
    a = ' data-anim="pulse" data-period="3"' if pulse else ""
    return (f'<defs><radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient></defs><circle cx="{x}" cy="{y}" r="{r}" fill="url(#{gid})"{a}/>')


# ---------------------------------------------------------------- globe & bodies
def dot_globe(cx, cy, r, rate=10, tilt=18, lon0=-110, color=C, markers=(), step=3.2, ocean_dots=False, at=None):
    """Rotating holographic Earth made of dots. markers: [(lat, lon, "LABEL")] -> pinned ring + label box.
    lon0 = longitude facing the viewer at t=0 (Jakarta ~ 107 -> use lon0=-107)."""
    pts = land_points(step)
    dots = "".join(f'<circle r="2.6" fill="{color}" data-lat="{la:.1f}" data-lon="{lo:.1f}"/>' for la, lo in pts)
    if ocean_dots:
        r0 = random.Random(3)
        dots += "".join(f'<circle r="1.2" fill="{color}" data-lat="{r0.uniform(-70,80):.1f}" data-lon="{r0.uniform(-180,180):.1f}"/>' for _ in range(260))
    mk = ""
    for la, lo, text in markers:
        mk += (f'<g data-lat="{la}" data-lon="{lo}"><circle r="14" fill="none" stroke="{O}" stroke-width="3"/>'
               f'<circle r="5" fill="{O}"/><circle r="14" fill="none" stroke="{O}" stroke-width="2" data-anim="ripple" data-period="1.6"/>'
               f'<path d="M14,-14 L60,-60 L80,-60" fill="none" stroke="{C2}" stroke-width="2"/>'
               f'<rect x="80" y="-82" width="{len(text)*24+36}" height="44" fill="rgba(4,14,20,.88)" stroke="{C}" stroke-width="2"/>'
               f'<text x="98" y="-50" font-family="Chakra Petch" font-weight="700" font-size="28" fill="{INK}" letter-spacing="2">{text}</text></g>')
    body = (glow(cx, cy, r * 1.5, color, .22, False)
            + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#061a24" fill-opacity=".85" stroke="{color}" stroke-width="3" opacity=".9"/>'
            + f'<circle cx="{cx}" cy="{cy}" r="{r+16}" fill="none" stroke="{color}" stroke-width="1.5" opacity=".35" stroke-dasharray="4 10"/>'
            + "".join(f'<ellipse cx="{cx}" cy="{cy+r*math.sin(math.radians(a))*0.95:.0f}" rx="{r*math.cos(math.radians(a)):.0f}" ry="{r*.12*math.cos(math.radians(a)):.0f}" '
                      f'fill="none" stroke="{color}" stroke-width="1" opacity=".18"/>' for a in (-60, -30, 0, 30, 60))
            + f'<g data-anim="globe" data-cx="{cx}" data-cy="{cy}" data-r="{r}" data-rate="{rate}" data-tilt="{tilt}" data-lon0="{lon0}">{dots}{mk}</g>')
    return f'<g data-anim="fade" data-at="{at}" data-dur=".6">{body}</g>' if at is not None else body


def orbit_ring(cx, cy, rx, ry, color=C, spin_period=14, dash="6 14", width=2, opacity=.6, tilt=0):
    return (f'<g transform="rotate({tilt} {cx} {cy})"><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-dasharray="{dash}" opacity="{opacity}"/></g>')


def spin_ring(cx, cy, r, color=C, period=18, dash="40 18 6 18", width=3, opacity=.7, reverse=False):
    p = -period if reverse else period
    return (f'<g data-anim="spin" data-period="{p}" style="transform-origin:{cx}px {cy}px;transform-box:view-box">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}" opacity="{opacity}"/></g>')


def hot_sphere(cx, cy, r, core="#fff1c8", mid=O, rim=O2, seed=0, boil=True):
    """Glowing hot body (star, planet core): radial gradient + turbulent surface + outer bloom."""
    gid, fid = _id("hs"), _id("hf")
    g = (f'<defs><radialGradient id="{gid}" cx="45%" cy="42%" r="60%"><stop offset="0" stop-color="{core}"/>'
         f'<stop offset=".55" stop-color="{mid}"/><stop offset="1" stop-color="{rim}"/></radialGradient>'
         f'<filter id="{fid}"><feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3" seed="{seed}"/>'
         f'<feColorMatrix type="matrix" values="0 0 0 0 1  0 0 0 0 .9  0 0 0 0 .7  0 0 0 1.3 -0.55"/>'
         f'<feComposite in2="SourceGraphic" operator="in"/></filter></defs>'
         + glow(cx, cy, r * 2.0, mid, .35)
         + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/>')
    tex = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" filter="url(#{fid})" opacity=".45"/>'
    if boil:
        tex = f'<g data-anim="spin" data-period="60" style="transform-origin:{cx}px {cy}px;transform-box:view-box">{tex}</g>'
    return g + tex + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff3d6" stroke-width="3" opacity=".7"/>'


def holo_planet(cx, cy, r, color=C, rate=8, lon0=-107, at=None):
    """Small holographic Earth (dot globe without markers) for orbit diagrams."""
    return dot_globe(cx, cy, r, rate=rate, lon0=lon0, color=color, step=6, at=at)


def light_pulse(path_d, at=0.0, dur=2.0, color="#fff6d8", loop=False, size=10):
    """A bright dot travelling along a path (light, signal, gravity wave front) with a fading trail."""
    pid = _id("lp")
    loop_a = ' data-loop="1"' if loop else ""
    return (f'<path id="{pid}" d="{path_d}" fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="3 9" opacity=".45"/>'
            f'<g data-anim="path" data-path="#{pid}" data-at="{at}" data-dur="{dur}"{loop_a}>'
            f'<circle cx="0" cy="0" r="{size*2.4:.0f}" fill="{color}" opacity=".25"/><circle cx="0" cy="0" r="{size}" fill="{color}"/></g>')


# ---------------------------------------------------------------- panels & widgets
def panel(x, y, w, h, color=C, fill="rgba(4,14,22,.82)", cut=18, title=None, at=None):
    """Cut-corner panel with a thin glowing border and optional mono title strip."""
    d = f"M{x+cut},{y} L{x+w},{y} L{x+w},{y+h-cut} L{x+w-cut},{y+h} L{x},{y+h} L{x},{y+cut} Z"
    g = f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="2.4"/>'
    g += f'<path d="M{x+w-60},{y+h+8} L{x+w},{y+h+8}" stroke="{color}" stroke-width="3" opacity=".7"/>'
    if title:
        g += f'<text x="{x+26}" y="{y+40}" font-family="Share Tech Mono" font-size="24" letter-spacing="4" fill="{C2}" opacity=".8">{title}</text>'
    return f'<g data-anim="fade" data-at="{at}" data-dur=".35">{g}</g>' if at is not None else g


def readout(x, y, label, value, unit="", color=INK, size=56, at=None, count_to=None, count_dur=1.5, frm=0, anchor="start"):
    """Mono label over a big value. count_to makes the value count up (Indonesian thousands dots)."""
    lab = f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Share Tech Mono" font-size="22" letter-spacing="4" fill="{C2}" opacity=".75">{label}</text>'
    if count_to is not None:
        a = f' data-at="{at or 0}" data-dur="{count_dur}" data-from="{frm}" data-to="{count_to}" data-suffix=""'
        val = f'<text x="{x}" y="{y+size+6}" text-anchor="{anchor}" font-family="Chakra Petch" font-weight="700" font-size="{size}" fill="{color}" data-anim="count"{a}>{value}</text>'
    else:
        val = f'<text x="{x}" y="{y+size+6}" text-anchor="{anchor}" font-family="Chakra Petch" font-weight="700" font-size="{size}" fill="{color}">{value}</text>'
    if unit:
        val += f'<text x="{x}" y="{y+size+6}" dx="{len(str(value))*size*.55+10:.0f}" font-family="Chakra Petch" font-weight="600" font-size="{size*.45:.0f}" fill="{color}" opacity=".8">{unit}</text>'
    g = lab + val
    return f'<g data-anim="fade" data-at="{at}" data-dur=".3">{g}</g>' if at is not None and count_to is None else g


def meter(x, y, w, h=26, n=28, at=0.0, dur=2.0, level=1.0, warn_from=0.65, label="", label_r=""):
    """Segmented bar that fills from left to `level` (0-1) starting at `at`; segments past warn_from turn orange."""
    seg_w = w / n
    out = ""
    if label:
        out += f'<text x="{x}" y="{y-12}" font-family="Share Tech Mono" font-size="22" letter-spacing="4" fill="{C2}" opacity=".75">{label}</text>'
    if label_r:
        out += f'<text x="{x+w}" y="{y+h-3}" dx="18" font-family="Chakra Petch" font-weight="700" font-size="26" fill="{O}" opacity=".6">{label_r}</text>'
    for i in range(n):
        k = i / n
        col = O if k >= warn_from else C
        out += f'<rect x="{x+i*seg_w+2:.1f}" y="{y}" width="{seg_w-4:.1f}" height="{h}" fill="{col}" opacity=".14"/>'
        if k < level:
            out += (f'<rect x="{x+i*seg_w+2:.1f}" y="{y}" width="{seg_w-4:.1f}" height="{h}" fill="{col}" '
                    f'data-anim="fade" data-at="{at + dur * k / max(level, .01):.2f}" data-dur=".08"/>')
    return out


def leader_label(px, py, lx, ly, text, color=C, at=0.0, warn=False, value=None):
    """Callout box at (lx, ly) with a leader line to the point (px, py)."""
    col = O if warn else color
    w = max(len(text) * 26 + 40, (len(value) * 36 + 40) if value else 0)
    h = 64 if not value else 120
    g = (f'<circle cx="{px}" cy="{py}" r="7" fill="{BG}" stroke="{INK}" stroke-width="3"/>'
         f'<path d="M{px},{py} L{lx+w/2:.0f},{ly+h}" fill="none" stroke="{INK}" stroke-width="2" data-anim="draw" data-at="{at}" data-dur=".4"/>'
         f'<rect x="{lx}" y="{ly}" width="{w}" height="{h}" fill="rgba(4,14,22,.88)" stroke="{col}" stroke-width="2.4"/>'
         f'<text x="{lx+20}" y="{ly+44}" font-family="Chakra Petch" font-weight="700" font-size="34" fill="{INK}" letter-spacing="2">{text}</text>')
    if value:
        g += f'<text x="{lx+20}" y="{ly+100}" font-family="Chakra Petch" font-weight="700" font-size="50" fill="{O}">{value}</text>'
    return f'<g data-anim="fade" data-at="{at}" data-dur=".3">{g}</g>'


def checklist(x, y, items, title="PARAMETER", w=520, at=0.0):
    """Panel with checkbox rows: items = [(text, checked_at_or_None)]."""
    h = 90 + len(items) * 62
    g = panel(x, y, w, h, title=title)
    for i, (text, chk) in enumerate(items):
        yy = y + 80 + i * 62
        g += f'<rect x="{x+28}" y="{yy}" width="34" height="34" fill="none" stroke="{INK}" stroke-width="3"/>'
        if chk is not None:
            g += f'<path d="M{x+34},{yy+18} l9,10 l16,-20" fill="none" stroke="{C}" stroke-width="5" data-anim="draw" data-at="{chk}" data-dur=".25"/>'
        g += f'<text x="{x+82}" y="{yy+29}" font-family="Chakra Petch" font-weight="700" font-size="34" fill="{INK}" letter-spacing="3">{text}</text>'
    return f'<g data-anim="fade" data-at="{at}" data-dur=".3">{g}</g>'


def wave_graph(x, y, w, h, cycles=2.0, at=0.0, dur=2.5, color=C, label="GRAFIK", ylabels=("ATAS", "TENGAH", "BAWAH"), fn=None):
    """Panel with a line graph that draws itself and a dot riding the head. fn(t in 0..1) -> -1..1 (default sine)."""
    fn = fn or (lambda t: math.cos(2 * math.pi * cycles * t))
    pts = [(x + 90 + (w - 120) * i / 120, y + h / 2 - fn(i / 120) * (h / 2 - 50)) for i in range(121)]
    d = "M" + " L".join(f"{f(a)},{f(b)}" for a, b in pts)
    pid = _id("wg")
    g = panel(x, y, w, h, title=label)
    for i, yl in enumerate(ylabels):
        yy = y + 50 + i * (h - 100) / max(len(ylabels) - 1, 1)
        g += (f'<text x="{x+22}" y="{yy+6:.0f}" font-family="Share Tech Mono" font-size="18" fill="{C2}" opacity=".6">{yl}</text>'
              f'<line x1="{x+90}" y1="{yy:.0f}" x2="{x+w-30}" y2="{yy:.0f}" stroke="{C}" stroke-width="1" opacity=".18"/>')
    g += f'<path id="{pid}" d="{d}" fill="none" stroke="{color}" stroke-width="4" data-anim="draw" data-at="{at}" data-dur="{dur}"/>'
    g += (f'<g data-anim="path" data-path="#{pid}" data-at="{at}" data-dur="{dur}"><circle r="16" fill="{color}" opacity=".25"/>'
          f'<circle r="8" fill="#fff"/></g>')
    return g


def radar(cx, cy, r, color=C, period=3.0):
    """Radar sweep with range rings."""
    gid = _id("rd")
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r*k/4:.0f}" fill="none" stroke="{color}" stroke-width="1.5" opacity=".3"/>' for k in range(1, 5))
    sweep = (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{color}" stop-opacity="0"/>'
             f'<stop offset="1" stop-color="{color}" stop-opacity=".5"/></linearGradient></defs>'
             f'<g data-anim="spin" data-period="{period}" style="transform-origin:{cx}px {cy}px;transform-box:view-box">'
             f'<path d="M{cx},{cy} L{cx+r},{cy} A{r},{r} 0 0 0 {f(cx+r*math.cos(-.8))},{f(cy+r*math.sin(-.8))} Z" fill="url(#{gid})"/></g>')
    return rings + sweep


def hazard_strip(x, y, w, h=34, color=O, at=None):
    pid = _id("hz")
    g = (f'<defs><pattern id="{pid}" width="40" height="{h}" patternUnits="userSpaceOnUse" patternTransform="skewX(-30)">'
         f'<rect width="20" height="{h}" fill="{color}"/></pattern></defs>'
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})" opacity=".85"/>')
    return f'<g data-anim="blinkon" data-period="1">{g}</g>' if at is None else f'<g data-anim="fade blinkon" data-at="{at}" data-period="1">{g}</g>'


def mono(x, y, text, size=24, color=None, anchor="start", at=None, opacity=.8, spacing=4):
    color = color or C2
    a = f' data-anim="fade" data-at="{at}" data-dur=".2"' if at is not None else ""
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Share Tech Mono" font-size="{size}" letter-spacing="{spacing}" '
            f'fill="{color}" opacity="{opacity}"{a}>{text}</text>')


def big(x, y, text, size=90, color=INK, anchor="middle", at=None, glow_c=C):
    a = f' data-anim="pop" data-at="{at}"' if at is not None else ""
    return (f'<g{a}><text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Chakra Petch" font-weight="700" font-size="{size}" fill="{color}" '
            f'style="filter:drop-shadow(0 0 14px {glow_c})">{text}</text></g>')


def thermo(x, y, h=520, level=.2, at=0.0, dur=2.0, cold=C, hot=O, falling=True):
    """Vertical thermometer bar; level animates from 1 -> level (falling) or 0 -> level."""
    gid = _id("th")
    g = (f'<defs><linearGradient id="{gid}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{cold}"/><stop offset="1" stop-color="{hot}"/></linearGradient></defs>'
         f'<rect x="{x-26}" y="{y-h}" width="52" height="{h}" rx="26" fill="rgba(4,14,22,.85)" stroke="{INK}" stroke-width="3"/>')
    if falling:
        g += (f'<rect x="{x-16}" y="{y-h+10}" width="32" height="{h-20}" rx="16" fill="url(#{gid})"/>'
              f'<rect x="{x-17}" y="{y-h+8}" width="34" height="{(h-20)*(1-level):.0f}" rx="16" fill="#061018" data-anim="grow" data-origin="top" data-at="{at}" data-dur="{dur}"/>')
    else:
        g += f'<rect x="{x-16}" y="{y-10-(h-20)*level:.0f}" width="32" height="{(h-20)*level:.0f}" rx="16" fill="url(#{gid})" data-anim="grow" data-origin="bottom" data-at="{at}" data-dur="{dur}"/>'
    return g


# ---------------------------------------------------------------- devices & surveillance
# (phones, towers, servers, people, cards, documents; first used for "presiden-disadap")
def phone_screen(cx, cy, h=560):
    """Screen rect (x, y, w, h) of phone(cx, cy, h), for drawing content on it."""
    w = h * .5
    return cx - w / 2 + w * .07, cy - h / 2 + h * .09, w * .86, h * .82


def phone(cx, cy, h=560, color=C, screen="", at=None, glow_c=None, screen_fill="#0a2230"):
    """Smartphone outline centred at (cx, cy). `screen` is SVG in scene coordinates (see phone_screen)."""
    w = h * .5
    x, y, r = cx - w / 2, cy - h / 2, w * .13
    sx, sy, sw, sh = phone_screen(cx, cy, h)
    g = glow(cx, cy, h * .7, glow_c or color, .16, False)
    g += (f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(r)}" fill="#05111a" stroke="{color}" stroke-width="4"/>'
          f'<rect x="{f(sx)}" y="{f(sy)}" width="{f(sw)}" height="{f(sh)}" rx="{f(r*.4)}" fill="{screen_fill}" stroke="{color}" stroke-width="1.5" stroke-opacity=".45"/>'
          f'<rect x="{f(cx-w*.14)}" y="{f(y+h*.035)}" width="{f(w*.28)}" height="{f(h*.022)}" rx="{f(h*.011)}" fill="{color}" opacity=".55"/>'
          f'<path d="M{f(x+w+3)},{f(y+h*.2)} v{f(h*.1)} M{f(x+w+3)},{f(y+h*.34)} v{f(h*.06)} M{f(x-3)},{f(y+h*.24)} v{f(h*.14)}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>'
          f'<rect x="{f(cx-w*.18)}" y="{f(y+h*.955)}" width="{f(w*.36)}" height="{f(h*.01)}" rx="3" fill="{color}" opacity=".6"/>')
    g += screen
    return f'<g data-anim="fade" data-at="{at}" data-dur=".4">{g}</g>' if at is not None else g


def signal_rings(cx, cy, r=80, color=C, period=1.8, n=3, opacity=.8, width=3):
    """Expanding rings (a phone transmitting, a tap leaking). Loops."""
    return "".join(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="none" stroke="{color}" stroke-width="{width}" '
                   f'data-anim="ripple" data-period="{period}" data-phase="{period*k/n:.2f}" data-opacity="{opacity}"/>' for k in range(n))


def cell_tower(cx, base_y, h=440, color=C, beacon=O, rings=True):
    """Lattice cell tower with panel antennas, a blinking beacon and transmit rings."""
    top = base_y - h
    hw0, hw1 = h * .17, h * .035
    g = f'<path d="M{f(cx-hw0)},{base_y} L{f(cx-hw1)},{f(top)} M{f(cx+hw0)},{base_y} L{f(cx+hw1)},{f(top)}" stroke="{color}" stroke-width="5" fill="none"/>'
    n = 6
    for i in range(n):
        y0, y1 = base_y - h * i / n, base_y - h * (i + 1) / n
        w0, w1 = hw0 + (hw1 - hw0) * i / n, hw0 + (hw1 - hw0) * (i + 1) / n
        g += (f'<path d="M{f(cx-w0)},{f(y0)} L{f(cx+w1)},{f(y1)} M{f(cx+w0)},{f(y0)} L{f(cx-w1)},{f(y1)} M{f(cx-w1)},{f(y1)} L{f(cx+w1)},{f(y1)}" '
              f'stroke="{color}" stroke-width="2" opacity=".55"/>')
    for dx in (-1, 1):
        g += f'<rect x="{f(cx+dx*hw1*2.2-9)}" y="{f(top+h*.03)}" width="18" height="{f(h*.13)}" rx="4" fill="#06202c" stroke="{color}" stroke-width="3"/>'
    g += f'<path d="M{cx},{f(top)} v{f(-h*.12)}" stroke="{color}" stroke-width="4"/>'
    g += glow(cx, top - h * .12, 40, beacon, .5)
    g += f'<circle cx="{cx}" cy="{f(top-h*.12)}" r="9" fill="{beacon}" data-anim="blinkon" data-period="1.2"/>'
    if rings:
        g += signal_rings(cx, top + h * .06, h * .22, color, 2.2, 3, .55, 2.5)
    g += f'<path d="M{f(cx-hw0-40)},{base_y} H{f(cx+hw0+40)}" stroke="{color}" stroke-width="3" opacity=".6"/>'
    return g


def server_rack(x, y, w=260, h=420, color=C, label="", seed=0, units=8):
    """Server rack: stacked units with twinkling LEDs and a label strip on top."""
    rnd = random.Random(seed)
    g = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#05121b" stroke="{color}" stroke-width="3.5"/>'
    uh = (h - 40) / units
    for i in range(units):
        uy = y + 20 + i * uh
        g += f'<rect x="{x+18}" y="{f(uy)}" width="{w-36}" height="{f(uh-10)}" rx="4" fill="#0a2230" stroke="{color}" stroke-width="1.5" stroke-opacity=".5"/>'
        g += "".join(f'<rect x="{f(x+36+k*14)}" y="{f(uy+uh/2-8)}" width="6" height="6" fill="{color}" opacity=".35"/>' for k in range(int((w - 140) / 14)))
        for k in range(3):
            col = O if rnd.random() < .25 else C
            g += (f'<circle cx="{f(x+w-40-k*20)}" cy="{f(uy+uh/2-5)}" r="4.5" fill="{col}" '
                  f'data-anim="twinkle" data-phase="{rnd.uniform(0, 6):.2f}"/>')
    if label:
        g += (f'<rect x="{x}" y="{y-58}" width="{w}" height="46" fill="rgba(4,14,22,.9)" stroke="{color}" stroke-width="2"/>'
              f'<text x="{f(x+w/2)}" y="{y-24}" text-anchor="middle" font-family="Chakra Petch" font-weight="700" font-size="30" letter-spacing="4" fill="{INK}">{label}</text>')
    return g


def person(cx, base_y, h=520, color=C, holding_phone=True, fill="#071722"):
    """Faceless silhouette (head + shoulders + torso), optionally looking at a glowing phone. Breathes."""
    hr = h * .12
    hy = base_y - h + hr
    sh = base_y - h * .66
    body = (f'<path d="M{f(cx-h*.27)},{base_y} L{f(cx-h*.25)},{f(sh+h*.1)} Q{f(cx-h*.24)},{f(sh)} {f(cx-h*.12)},{f(sh-h*.02)} '
            f'L{f(cx+h*.12)},{f(sh-h*.02)} Q{f(cx+h*.24)},{f(sh)} {f(cx+h*.25)},{f(sh+h*.1)} L{f(cx+h*.27)},{base_y} Z" '
            f'fill="{fill}" stroke="{color}" stroke-width="3.5"/>'
            f'<path d="M{f(cx-h*.05)},{f(sh-h*.02)} L{f(cx-h*.045)},{f(hy+hr*.8)} M{f(cx+h*.05)},{f(sh-h*.02)} L{f(cx+h*.045)},{f(hy+hr*.8)}" stroke="{color}" stroke-width="3"/>'
            f'<circle cx="{cx}" cy="{f(hy)}" r="{f(hr)}" fill="{fill}" stroke="{color}" stroke-width="3.5"/>')
    if holding_phone:
        px, py = cx + h * .02, sh + h * .2
        body += (f'<path d="M{f(cx-h*.2)},{f(sh+h*.32)} Q{f(cx-h*.08)},{f(py+h*.12)} {f(px-h*.02)},{f(py+h*.06)}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>'
                 + glow(px, py, h * .22, C2, .35, False)
                 + f'<rect x="{f(px-h*.045)}" y="{f(py-h*.075)}" width="{f(h*.09)}" height="{f(h*.15)}" rx="6" fill="#bff4ff" stroke="{color}" stroke-width="2" transform="rotate(-14 {f(px)} {f(py)})"/>'
                 + f'<path d="M{f(px)},{f(py)} L{f(cx-hr*.6)},{f(hy+hr*.2)} L{f(cx+hr*.6)},{f(hy+hr*.2)} Z" fill="{C2}" opacity=".08"/>')
    return f'<g data-anim="pulse" data-period="4.5" data-amp=".5">{body}</g>'


def id_card(x, y, w=200, h=270, label="", color=C, at=None, lit_color=O):
    """Faceless ID card: silhouette, redacted name bar, barcode. Lights up (border -> lit_color) at `at`."""
    cx = x + w / 2

    def card(col, op):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="rgba(4,14,22,.9)" stroke="{col}" stroke-width="3" opacity="{op}"/>'
                f'<rect x="{x+20}" y="{y+20}" width="{w-40}" height="{f(h*.5)}" fill="#0a2230" stroke="{col}" stroke-width="1.5" opacity="{op}"/>'
                f'<circle cx="{f(cx)}" cy="{f(y+20+h*.2)}" r="{f(w*.13)}" fill="{col}" opacity="{op*.55:.2f}"/>'
                f'<path d="M{f(cx-w*.27)},{f(y+20+h*.5)} Q{f(cx)},{f(y+h*.3)} {f(cx+w*.27)},{f(y+20+h*.5)} Z" fill="{col}" opacity="{op*.55:.2f}"/>'
                f'<rect x="{x+20}" y="{f(y+h*.62+12)}" width="{w-40}" height="20" fill="{col}" opacity="{op*.9:.2f}"/>'
                + "".join(f'<rect x="{f(x+22+k*9)}" y="{f(y+h*.8)}" width="{3 if k % 3 else 5}" height="{f(h*.11)}" fill="{col}" opacity="{op*.6:.2f}"/>'
                          for k in range(int((w - 40) / 9))))
    g = card(color, .45)
    if label:
        g += f'<text x="{f(cx)}" y="{y+h+40}" text-anchor="middle" font-family="Share Tech Mono" font-size="24" letter-spacing="3" fill="{C2}" opacity=".8">{label}</text>'
    if at is not None:
        g += f'<g data-anim="fade" data-at="{at}" data-dur=".15">{glow(cx, y + h / 2, w * .9, lit_color, .25, False)}{card(lit_color, 1)}</g>'
    return g


def doc_card(x, y, w=480, h=620, title="SURAT", lines=7, color=C, at=None):
    """Official document: header, text lines, signature line (drawn in the HUD palette)."""
    g = (f'<path d="M{x},{y} H{x+w-50} L{x+w},{y+50} V{y+h} H{x} Z" fill="#081a24" stroke="{color}" stroke-width="3"/>'
         f'<path d="M{x+w-50},{y} V{y+50} H{x+w}" fill="none" stroke="{color}" stroke-width="2" opacity=".7"/>'
         f'<text x="{x+40}" y="{y+70}" font-family="Chakra Petch" font-weight="700" font-size="32" letter-spacing="3" fill="{INK}">{title}</text>'
         f'<rect x="{x+40}" y="{y+92}" width="{w-80}" height="3" fill="{color}" opacity=".6"/>')
    for i in range(lines):
        ll = w - 80 - (60 if i % 3 == 2 else 0) - (140 if i == lines - 1 else 0)
        g += f'<rect x="{x+40}" y="{y+130+i*46}" width="{ll}" height="12" rx="6" fill="{C2}" opacity=".28"/>'
    g += (f'<path d="M{x+w-230},{y+h-70} q30,-40 60,0 t60,-10 t50,5" fill="none" stroke="{C2}" stroke-width="3" opacity=".6"/>'
          f'<rect x="{x+w-240}" y="{y+h-55}" width="200" height="2" fill="{C2}" opacity=".5"/>')
    return f'<g data-anim="fade" data-at="{at}" data-dur=".4">{g}</g>' if at is not None else g


def stamp(cx, cy, text, color=O, at=0.0, angle=-12, size=54):
    """Rubber stamp that slams on at `at` (pop) with a slight tilt."""
    w = len(text) * size * .62 + 60
    g = (f'<g transform="rotate({angle} {cx} {cy})"><rect x="{f(cx-w/2)}" y="{f(cy-size*.9)}" width="{f(w)}" height="{f(size*1.6)}" rx="8" '
         f'fill="rgba(20,8,0,.6)" stroke="{color}" stroke-width="7"/>'
         f'<text x="{cx}" y="{f(cy+size*.32)}" text-anchor="middle" font-family="Chakra Petch" font-weight="700" font-size="{size}" letter-spacing="4" fill="{color}">{text}</text></g>')
    return f'<g data-anim="pop" data-at="{at}">{g}</g>'


def file_list(x, y, w, names, at_delete=None, step=.12, color=C, title="ARSIP"):
    """Panel with file rows (icon + name + size). From at_delete the rows vanish one by one with an orange flash."""
    h = 90 + len(names) * 58
    g = panel(x, y, w, h, title=title)
    for i, name in enumerate(names):
        yy = y + 74 + i * 58
        row = (f'<rect x="{x+26}" y="{yy}" width="30" height="38" rx="3" fill="none" stroke="{color}" stroke-width="2.5"/>'
               f'<path d="M{x+32},{yy+14} h18 M{x+32},{yy+22} h18 M{x+32},{yy+30} h12" stroke="{color}" stroke-width="2" opacity=".7"/>'
               f'<text x="{x+76}" y="{yy+29}" font-family="Share Tech Mono" font-size="28" letter-spacing="2" fill="{INK}">{name}</text>'
               f'<text x="{x+w-30}" y="{yy+29}" text-anchor="end" font-family="Share Tech Mono" font-size="22" fill="{C2}" opacity=".6">{(i*37 % 90) + 12} MB</text>')
        if at_delete is None:
            g += row
        else:
            t = at_delete + i * step
            g += (f'<g data-anim="fade-out" data-at="{t:.2f}" data-dur=".18">{row}</g>'
                  f'<g data-anim="fade" data-at="{t:.2f}" data-dur=".08"><g data-anim="fade-out" data-at="{t+.2:.2f}" data-dur=".4">'
                  f'<rect x="{x+20}" y="{yy-4}" width="{w-40}" height="46" fill="{O}" opacity=".35"/></g></g>')
    return g
