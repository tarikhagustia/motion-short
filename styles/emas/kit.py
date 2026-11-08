"""emas kit: ornamental gold-on-batik pieces for the `emas` style.

    import sys; sys.path[:0] = ["<skill>/scripts", "<skill>/styles/emas"]
    from svgkit import *          # base helpers: write_scene, group, depth, cover, mix, shade ...
    from kit import *             # this file

Look: every shape is flat colour (crimson, indigo, rust brown, cream) with a thin gold outline
(`GOLD`) and gold detail lines; backgrounds are batik fabric (fine diagonal parang lines, kawung dots).
All pieces already move (bob, sway, drift, twinkle, pulse) so scenes stay alive.
"""
import math
import random

from svgkit import _id, f, mix, shade, group, depth

P = {
    "gold": "#d9b45e", "gold_hi": "#f6dc8a", "gold_dk": "#9c7330",
    "crimson": "#8e2433", "crimson_dk": "#5e1322", "red": "#b13a3a",
    "indigo": "#27346b", "indigo_dk": "#18204a", "indigo_hi": "#3b4c8f",
    "rust": "#8a5530", "rust_dk": "#5e3519", "brown": "#6b4126",
    "cream": "#efe0bf", "paper": "#e6d3a8", "ink": "#2a160c", "teal": "#2f5d64",
}
GOLD = P["gold"]


def _gstroke(w=3, c=GOLD):
    return f'stroke="{c}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"'


# ---------------------------------------------------------------- backgrounds
def batik_bg(base="#7a4a2a", line=None, motif="parang", seed=0, y0=0, y1=1920, opacity=0.35):
    """Fabric background: base colour + fine diagonal parang lines or kawung dots, soft light falloff."""
    pid, gid = _id("pat"), _id("bg")
    line = line or shade(base, -0.35)
    if motif == "kawung":
        pat = (f'<pattern id="{pid}" width="44" height="44" patternUnits="userSpaceOnUse">'
               f'<ellipse cx="22" cy="10" rx="6" ry="9" fill="none" stroke="{line}" stroke-width="1.6"/>'
               f'<ellipse cx="22" cy="34" rx="6" ry="9" fill="none" stroke="{line}" stroke-width="1.6"/>'
               f'<ellipse cx="10" cy="22" rx="9" ry="6" fill="none" stroke="{line}" stroke-width="1.6"/>'
               f'<ellipse cx="34" cy="22" rx="9" ry="6" fill="none" stroke="{line}" stroke-width="1.6"/>'
               f'<circle cx="22" cy="22" r="2" fill="{line}"/></pattern>')
    elif motif == "dots":
        pat = (f'<pattern id="{pid}" width="22" height="22" patternUnits="userSpaceOnUse">'
               f'<circle cx="11" cy="11" r="1.6" fill="{line}"/></pattern>')
    else:  # parang: fine diagonal lines with a small zigzag every few lines
        pat = (f'<pattern id="{pid}" width="18" height="18" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)">'
               f'<line x1="0" y1="0" x2="0" y2="18" stroke="{line}" stroke-width="2.2"/>'
               f'<line x1="9" y1="0" x2="9" y2="18" stroke="{line}" stroke-width="0.9" opacity=".6"/></pattern>')
    h = y1 - y0
    return (f'<defs>{pat}<radialGradient id="{gid}" cx="50%" cy="42%" r="75%">'
            f'<stop offset="0" stop-color="{shade(base, .12)}"/><stop offset="1" stop-color="{shade(base, -.28)}"/></radialGradient></defs>'
            f'<rect x="0" y="{y0}" width="1080" height="{h}" fill="url(#{gid})"/>'
            f'<rect x="0" y="{y0}" width="1080" height="{h}" fill="url(#{pid})" opacity="{opacity}"/>')


def night_cloth(base=None, seed=0):
    """Deep indigo cloth with scattered gold dots (night, sea, sky)."""
    base = base or P["indigo"]
    r = random.Random(seed)
    dots = "".join(f'<circle cx="{r.uniform(0,1080):.0f}" cy="{r.uniform(0,1920):.0f}" r="{r.uniform(1.2,2.8):.1f}" fill="{P["gold_hi"]}" '
                   f'data-anim="twinkle" data-phase="{r.uniform(0,6):.2f}"/>' for _ in range(70))
    return batik_bg(base, shade(base, -.4), "kawung", seed, opacity=.3) + dots


# ---------------------------------------------------------------- ornaments
def ornate_frame(inset=46, top=None, bottom=None, color=GOLD, fill=None, tumpal=True):
    """Gold double-rule frame with tumpal (triangle) bands top and bottom and corner rosettes."""
    t = top if top is not None else inset
    b = bottom if bottom is not None else 1920 - inset
    x0, x1 = inset, 1080 - inset
    s = ""
    if fill:
        s += f'<rect x="{x0}" y="{t}" width="{x1-x0}" height="{b-t}" fill="{fill}"/>'
    s += f'<rect x="{x0}" y="{t}" width="{x1-x0}" height="{b-t}" fill="none" {_gstroke(4, color)}/>'
    s += f'<rect x="{x0+14}" y="{t+14}" width="{x1-x0-28}" height="{b-t-28}" fill="none" {_gstroke(1.6, color)}/>'
    if tumpal:
        for yy, d in ((t + 14, 1), (b - 14, -1)):
            n = 18
            w = (x1 - x0 - 28) / n
            pts = " ".join(f"M{f(x0+14+i*w)},{yy} L{f(x0+14+i*w+w/2)},{f(yy+d*34)} L{f(x0+14+(i+1)*w)},{yy}" for i in range(n))
            s += f'<path d="{pts}" fill="none" {_gstroke(1.8, color)}/>'
    for cx, cy in ((x0, t), (x1, t), (x0, b), (x1, b)):
        s += rosette(cx, cy, 16, color)
    return s


def rosette(x, y, r=18, color=GOLD, spin=False):
    petals = "".join(f'<ellipse cx="{f(x)}" cy="{f(y-r*.55)}" rx="{f(r*.28)}" ry="{f(r*.55)}" fill="{color}" '
                     f'transform="rotate({k*45} {f(x)} {f(y)})"/>' for k in range(8))
    core = f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r*.25)}" fill="{P["crimson_dk"]}" stroke="{color}" stroke-width="2"/>'
    g = f'<g>{petals}{core}</g>'
    return f'<g data-anim="spin" data-period="30">{g}</g>' if spin else g


def gold_sun(x, y, r=110, rays=16, spin=True):
    """Spiky ornamental sun: gold disc with engraved ring and pointed rays, slow spin + glow pulse."""
    gid = _id("sg")
    pts = []
    for i in range(rays * 2):
        a = math.pi * i / rays
        rr = r * (1.55 if i % 2 == 0 else 1.08)
        pts.append(f"{f(x+math.cos(a)*rr)},{f(y+math.sin(a)*rr)}")
    ray = f'<polygon points="{" ".join(pts)}" fill="{P["gold"]}" stroke="{P["gold_dk"]}" stroke-width="2"/>'
    if spin:
        ray = f'<g data-anim="spin" data-period="40">{ray}</g>'
    return (f'<defs><radialGradient id="{gid}"><stop offset="0" stop-color="#fff2b8" stop-opacity=".9"/>'
            f'<stop offset="1" stop-color="#f6c95a" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{x}" cy="{y}" r="{r*2.6:.0f}" fill="url(#{gid})" opacity=".55" data-anim="pulse" data-period="5"/>'
            + ray +
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="#f2cf6e" stroke="{P["gold_dk"]}" stroke-width="3"/>'
            f'<circle cx="{x}" cy="{y}" r="{r*.78:.0f}" fill="none" stroke="#c99a3c" stroke-width="2.5" stroke-dasharray="5 7"/>'
            f'<circle cx="{x}" cy="{y}" r="{r*.5:.0f}" fill="#f8dc8a"/>')


def sparkles(n=10, area=(80, 200, 1000, 1300), seed=0, color=None):
    """Four-point gold glints that twinkle."""
    r = random.Random(seed)
    color = color or P["gold_hi"]
    out = ""
    for _ in range(n):
        x, y = r.uniform(area[0], area[2]), r.uniform(area[1], area[3])
        s = r.uniform(6, 16)
        d = f"M{f(x)},{f(y-s)} Q{f(x)},{f(y)} {f(x+s)},{f(y)} Q{f(x)},{f(y)} {f(x)},{f(y+s)} Q{f(x)},{f(y)} {f(x-s)},{f(y)} Q{f(x)},{f(y)} {f(x)},{f(y-s)}Z"
        out += f'<path d="{d}" fill="{color}" data-anim="twinkle" data-phase="{r.uniform(0,6):.2f}"/>'
    return out


def glow(x, y, r=200, color="#ffd77a", opacity=0.6, pulse=True):
    gid = _id("gl")
    a = ' data-anim="pulse" data-period="3.5"' if pulse else ""
    return (f'<defs><radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#{gid})"{a}/>')


def ornate_waves(y, rows=3, color=None, line=None, seed=0, speed=10, spacing=70, x0=-120, x1=1200):
    """Rows of curling ornamental waves (indigo with gold/cream curls), drifting slowly."""
    color = color or P["indigo"]
    line = line or "#9fb0e0"
    r = random.Random(seed)
    out = f'<rect x="0" y="{y}" width="1080" height="{1920-y}" fill="{color}"/>'
    for k in range(rows * 3):
        yy = y + 40 + k * spacing * .55
        off = (k % 2) * spacing / 2
        curls = ""
        x = x0 + off
        while x < x1:
            curls += (f'<path d="M{f(x)},{f(yy)} q{spacing*.25:.0f},-26 {spacing*.5:.0f},0 q-{spacing*.14:.0f},-14 -{spacing*.2:.0f},2" '
                      f'fill="none" stroke="{line}" stroke-width="2.2" stroke-linecap="round" opacity="{.45 + .3 * r.random():.2f}"/>')
            x += spacing
        sp = speed * (1 if k % 2 else -1) * (0.6 + .4 * r.random())
        curls = f'<g data-anim="drift" data-speed="{sp:.1f}">{curls}</g>'
        out += curls
    return out


def river(path_d, width=260, color=None, bank=GOLD, seed=0):
    """A winding river: indigo band with gold banks and drifting swirl marks along the path."""
    color = color or P["indigo"]
    pid = _id("rv")
    r = random.Random(seed)
    swirls = ""
    for i in range(14):
        k = i / 14
        swirls += (f'<g data-anim="path" data-path="#{pid}" data-dur="{r.uniform(9,14):.1f}" data-loop="1" data-at="{-k*12:.1f}">'
                   f'<path d="M0,0 q10,-12 20,0 q-6,-6 -10,0" fill="none" stroke="#a9b7e6" stroke-width="2.4" stroke-linecap="round" '
                   f'transform="translate({r.uniform(-60,60):.0f},{r.uniform(-20,20):.0f})"/></g>')
    return (f'<path d="{path_d}" fill="none" stroke="{bank}" stroke-width="{width+14}" stroke-linecap="round"/>'
            f'<path id="{pid}" d="{path_d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
            f'<path d="{path_d}" fill="none" stroke="{shade(color,.1)}" stroke-width="{width*.55:.0f}" stroke-linecap="round" opacity=".5"/>'
            + swirls)


# ---------------------------------------------------------------- objects
def rumah_panggung(x, y, s=1.0, roof=None, wall=None, flip=False):
    """Stilt house (Malay/Sumatran): red roof with gold edge, wood wall, stilts, ladder. (x, y) = ground centre."""
    roof = roof or P["red"]
    wall = wall or "#a8683a"
    sx = -s if flip else s
    g = (f'<g transform="translate({x},{y}) scale({sx:.3f},{s:.3f})">'
         + "".join(f'<rect x="{xx}" y="-70" width="7" height="70" fill="{P["rust_dk"]}"/>' for xx in (-62, -22, 18, 56))
         + f'<rect x="-78" y="-78" width="156" height="10" fill="{P["rust_dk"]}" {_gstroke(1.4)}/>'
         f'<rect x="-66" y="-150" width="132" height="74" fill="{wall}" {_gstroke(2)}/>'
         + "".join(f'<line x1="-66" y1="{yy}" x2="66" y2="{yy}" stroke="{shade(wall,-.25)}" stroke-width="2"/>' for yy in (-132, -114, -96))
         + f'<rect x="-14" y="-136" width="28" height="52" fill="{P["indigo_dk"]}" {_gstroke(1.6)}/>'
         f'<path d="M-96,-146 L0,-214 L96,-146 Z" fill="{roof}" {_gstroke(3)}/>'
         f'<path d="M-96,-146 q-14,-4 -20,-16 M96,-146 q14,-4 20,-16" fill="none" {_gstroke(3)}/>'
         f'<path d="M-60,-160 L0,-202 L60,-160" fill="none" stroke="{shade(roof,-.3)}" stroke-width="2"/>'
         f'<path d="M30,-70 L52,0 M44,-70 L66,0" stroke="{P["rust_dk"]}" stroke-width="5"/>'
         + "".join(f'<line x1="{34+k*5}" y1="{-58+k*14}" x2="{48+k*5}" y2="{-58+k*14}" stroke="{P["rust_dk"]}" stroke-width="4"/>' for k in range(4))
         + '</g>')
    return g


def batik_palm(x, y, h=300, colors=None, seed=0):
    """Stylised batik palm: thin trunk, fronds made of rows of filled leaf ovals (red/blue alternating), swaying."""
    r = random.Random(seed)
    colors = colors or [P["crimson"], P["indigo_hi"]]
    trunk = f'<path d="M{x},{y} q{r.uniform(-20,20):.0f},{-h*.5:.0f} {r.uniform(-12,12):.0f},{-h:.0f}" fill="none" stroke="{P["gold_dk"]}" stroke-width="5"/>'
    top_x, top_y = x, y - h
    fronds = ""
    for i, ang in enumerate((-150, -115, -70, -30, 10, 200)):
        a = math.radians(ang)
        L = h * r.uniform(.42, .55)
        col = colors[i % len(colors)]
        leaves = ""
        for k in range(6):
            t = (k + 1) / 7
            cx, cy = top_x + math.cos(a) * L * t, top_y + math.sin(a) * L * t + 30 * t * t
            leaves += (f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(16-k*1.2)}" ry="{f(10-k*.6)}" fill="{col}" '
                       f'stroke="{GOLD}" stroke-width="1.4" transform="rotate({ang+90} {f(cx)} {f(cy)})"/>'
                       f'<circle cx="{f(cx)}" cy="{f(cy)}" r="1.6" fill="{P["gold_hi"]}"/>')
        fronds += leaves
    crown = f'<g data-anim="sway" data-pivot="{top_x} {top_y}" data-period="{r.uniform(4,6):.1f}" data-amp="1.2">{fronds}</g>'
    return f'<g data-anim="sway" data-pivot="{x} {y}" data-period="{r.uniform(5,7):.1f}" data-amp=".5">{trunk}{crown}</g>'


def jong(x, y, s=1.0, sails=2, hull=None, sail=None, bob=True, flip=False):
    """Nusantara ship (jong / jung): curved hull with gold ornament, rectangular battened sails. (x, y) = waterline centre."""
    hull = hull or P["rust_dk"]
    sail = sail or "#c9a06a"
    sx = -s if flip else s
    sail_svg = ""
    for i in range(sails):
        ox = -40 + i * 90 - (sails - 1) * 20
        hgt = 230 - i * 30
        sail_svg += (f'<line x1="{ox}" y1="-30" x2="{ox}" y2="{-hgt-30}" stroke="{P["ink"]}" stroke-width="5"/>'
                     f'<path d="M{ox-62},{-hgt-10} L{ox+58},{-hgt-26} L{ox+66},-56 L{ox-58},-48 Z" fill="{sail}" {_gstroke(2.4)}/>'
                     + "".join(f'<line x1="{ox-60+k*1.2:.0f}" y1="{-hgt-10+k*(hgt-40)/5:.0f}" x2="{ox+62+k*.4:.0f}" y2="{-hgt-26+k*(hgt-30)/5:.0f}" '
                               f'stroke="{P["rust_dk"]}" stroke-width="2"/>' for k in range(1, 5)))
    flag = f'<path d="M{-40-(sails-1)*20},{-260} l34,8 l-34,10 z" fill="{P["crimson"]}" data-anim="sway" data-period="1.4" data-amp="2"/>'
    hull_svg = (f'<path d="M-170,-40 Q-150,30 -60,34 L80,34 Q170,30 190,-50 L150,-40 L-150,-36 Z" fill="{hull}" {_gstroke(3)}/>'
                f'<path d="M-150,-20 Q-40,6 170,-26" fill="none" {_gstroke(2.2)}/>'
                f'<path d="M190,-50 q24,-30 6,-60 q-6,22 -24,30" fill="{hull}" {_gstroke(2.4)}/>'
                f'<path d="M-170,-40 q-26,-16 -18,-44 q12,20 30,26" fill="{hull}" {_gstroke(2.4)}/>'
                + "".join(f'<circle cx="{xx}" cy="6" r="4" fill="{P["gold_hi"]}"/>' for xx in range(-110, 140, 40)))
    g = f'<g transform="translate({x},{y}) scale({sx:.3f},{s:.3f})">{sail_svg}{flag}{hull_svg}</g>'
    return f'<g data-anim="bob" data-period="3.6" data-amp="1.2">{g}</g>' if bob else g


def stupa_temple(x, y, s=1.0, roof=None, roof2=None):
    """Tiered temple / vihara: stone base, red and indigo stacked roofs with gold trims, small stupa finial."""
    roof = roof or P["crimson"]
    roof2 = roof2 or P["indigo"]
    g = f'<g transform="translate({x},{y}) scale({s:.3f})">'
    g += f'<rect x="-210" y="-60" width="420" height="60" fill="{P["paper"]}" {_gstroke(2.4)}/>'
    g += "".join(f'<line x1="-210" y1="{-60+k*15}" x2="210" y2="{-60+k*15}" stroke="{P["gold_dk"]}" stroke-width="1.4"/>' for k in range(1, 4))
    g += f'<rect x="-160" y="-190" width="320" height="130" fill="{P["crimson_dk"]}" {_gstroke(2.4)}/>'
    g += "".join(f'<rect x="{xx}" y="-176" width="24" height="104" fill="{P["red"]}" {_gstroke(1.2)}/>' for xx in range(-140, 140, 44))
    for k, (w, yy, col) in enumerate(((440, -190, roof2), (360, -262, roof), (270, -326, roof2), (180, -380, roof))):
        g += (f'<path d="M{-w/2:.0f},{yy} L{-w/2+50:.0f},{yy-62} L{w/2-50:.0f},{yy-62} L{w/2:.0f},{yy} Z" fill="{col}" {_gstroke(2.6)}/>'
              + "".join(f'<line x1="{-w/2+20+j*(w-40)/8:.0f}" y1="{yy-6}" x2="{-w/2+60+j*(w-120)/8:.0f}" y2="{yy-56}" stroke="{shade(col,.15)}" stroke-width="2"/>' for j in range(9)))
    g += f'<path d="M-20,-442 Q0,-500 20,-442 Z" fill="{P["gold"]}"/><line x1="0" y1="-500" x2="0" y2="-540" stroke="{P["gold"]}" stroke-width="4"/>'
    g += f'<circle cx="0" cy="-548" r="9" fill="{P["gold_hi"]}" data-anim="pulse" data-period="2"/>'
    return g + "</g>"


def traveler(x, y, h=200, robe=None, hat=True, facing=1, walk=False):
    """Simple robed figure (monk / traveler / sailor), flat colours with gold rim. (x, y) = feet."""
    robe = robe or P["crimson"]
    s = h / 200
    body = (f'<path d="M-30,0 L-22,-120 Q0,-140 22,-120 L30,0 Z" fill="{robe}" {_gstroke(2)}/>'
            f'<path d="M-22,-120 L18,-30" stroke="{P["gold_hi"]}" stroke-width="3"/>'
            f'<circle cx="0" cy="-148" r="20" fill="#c58c5c" {_gstroke(1.6)}/>')
    if hat:
        body += f'<path d="M-40,-152 L0,-188 L40,-152 Z" fill="{P["paper"]}" {_gstroke(2)}/>'
    g = f'<g transform="translate({x},{y}) scale({s*facing:.3f},{s:.3f})">{body}</g>'
    return f'<g data-anim="walk" data-period=".7">{g}</g>' if walk else g


def figure_rows(x0, x1, y0, rows=5, cols=14, color=None, gap=46, seed=0):
    """Many small seated figures in rows (students, crowd, congregation), staggered pop-in."""
    color = color or P["crimson"]
    r = random.Random(seed)
    out = ""
    for j in range(rows):
        yy = y0 + j * gap
        n = cols + (j % 2)
        w = (x1 - x0) / n
        row = ""
        for i in range(n):
            xx = x0 + w * (i + .5)
            c = color if r.random() > .2 else shade(color, -.2)
            row += (f'<g data-anim="pop"><path d="M{f(xx-13)},{yy} Q{f(xx)},{yy-34} {f(xx+13)},{yy} Z" fill="{c}" stroke="{GOLD}" stroke-width="1"/>'
                    f'<circle cx="{f(xx)}" cy="{yy-36}" r="8" fill="#b9825a"/></g>')
        out += f'<g data-stagger=".03" data-at="{j*.15:.2f}">{row}</g>'
    return out


def prasasti(x, y, w=170, h=230, seed=0, color=None):
    """Inscribed stone (batu prasasti): rounded slab with rows of glyph marks in gold."""
    color = color or "#5b6a8c"
    r = random.Random(seed)
    glyphs = ""
    for row in range(int(h / 34) - 1):
        xx = x - w / 2 + 22
        while xx < x + w / 2 - 26:
            gw = r.uniform(10, 18)
            glyphs += (f'<path d="M{f(xx)},{f(y-h/2+40+row*32)} q{gw/2:.0f},-{r.uniform(6,14):.0f} {gw:.0f},0 m-{gw*.6:.0f},6 l0,8" '
                       f'fill="none" stroke="{P["gold_hi"]}" stroke-width="2.2" stroke-linecap="round"/>')
            xx += gw + 8
    return (f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="{w*.22:.0f}" fill="{color}" {_gstroke(3)}/>'
            f'<rect x="{x-w/2+10}" y="{y-h/2+10}" width="{w-20}" height="{h-20}" rx="{w*.18:.0f}" fill="none" stroke="{shade(color,-.25)}" stroke-width="2"/>'
            + glyphs)


def medallion(x, y, r=110, fill=None, inner=""):
    """Gold oval portrait frame; put a silhouette or symbol in `inner` (drawn centred at x, y)."""
    fill = fill or P["indigo"]
    return (f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r*1.22:.0f}" fill="{fill}" stroke="{P["gold"]}" stroke-width="10"/>'
            f'<ellipse cx="{x}" cy="{y}" rx="{r-16}" ry="{r*1.22-16:.0f}" fill="none" stroke="{P["gold_hi"]}" stroke-width="2.4" stroke-dasharray="3 6"/>'
            + inner)


def lamp(x, y, s=1.0):
    """Oil lamp with flickering flame and warm glow."""
    return (glow(x, y - 70 * s, 160 * s, "#ffcf6b", .55)
            + f'<g transform="translate({x},{y}) scale({s})">'
            f'<path d="M-40,0 Q0,24 40,0 L30,-30 Q0,-20 -30,-30 Z" fill="{P["gold_dk"]}" {_gstroke(2)}/>'
            f'<path d="M-22,-30 Q0,-80 22,-30" fill="#f6e3b0" opacity=".8" stroke="{GOLD}" stroke-width="2"/>'
            f'<path d="M0,-52 q10,-14 0,-34 q-10,20 0,34" fill="#ffb347" data-anim="flicker pulse" data-period=".9"/></g>')


def label_gold(x, y, text, size=46, color=None, anchor="middle", at=None, italic=False, weight=700):
    """Serif map label in cream/gold with dark outline (place names on maps)."""
    color = color or P["cream"]
    a = f' data-anim="fade" data-at="{at}"' if at is not None else ""
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Playfair Display" font-weight="{weight}" font-size="{size}"{st} '
            f'fill="{color}" stroke="{P["ink"]}" stroke-width="5" paint-order="stroke"{a}>{text}</text>')


def compass(x, y, r=80, spin_in=None):
    """Ornate compass rose in gold."""
    pts = []
    for i in range(16):
        a = math.pi * i / 8 - math.pi / 2
        rr = r if i % 4 == 0 else (r * .55 if i % 2 == 0 else r * .3)
        pts.append(f"{f(x+math.cos(a)*rr)},{f(y+math.sin(a)*rr)}")
    g = (f'<circle cx="{x}" cy="{y}" r="{r*.72:.0f}" fill="none" {_gstroke(2)}/>'
         f'<polygon points="{" ".join(pts)}" fill="{P["gold"]}" stroke="{P["gold_dk"]}" stroke-width="1.5"/>'
         f'<text x="{x}" y="{y-r-10}" text-anchor="middle" font-family="Playfair Display" font-weight="700" font-size="30" fill="{P["gold_hi"]}">U</text>')
    if spin_in is not None:
        return f'<g data-anim="pop" data-at="{spin_in}">{g}</g>'
    return g


def route(path_d, at=0.0, dur=2.2, color=None, dashed=True, width=5):
    """Gold dashed route that draws itself (use with a `jong` on data-anim="path")."""
    color = color or P["gold_hi"]
    pid = _id("rt")
    dash = ' stroke-dasharray="16 12"' if dashed else ""
    # dashed lines can't use the draw trick directly, so reveal them with a mask path that draws
    mid = _id("rm")
    return (f'<defs><mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="1080" height="1920">'
            f'<path d="{path_d}" fill="none" stroke="#fff" stroke-width="{width*4}" data-anim="draw" data-at="{at}" data-dur="{dur}"/></mask></defs>'
            f'<path id="{pid}" d="{path_d}" fill="none" stroke="{color}" stroke-width="{width}"{dash} stroke-linecap="round" mask="url(#{mid})"/>')


def land(path_d, fill=None, coast=GOLD, hatch=True):
    """Map landmass: rust fabric fill, gold coastline, inner hatch lines."""
    fill = fill or P["rust"]
    cid = _id("ld")
    hatch_svg = ""
    if hatch:
        pid = _id("lh")
        hatch_svg = (f'<defs><pattern id="{pid}" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(40)">'
                     f'<line x1="0" y1="0" x2="0" y2="16" stroke="{shade(fill,-.25)}" stroke-width="2"/></pattern></defs>'
                     f'<path d="{path_d}" fill="url(#{pid})" opacity=".55"/>')
    return (f'<path d="{path_d}" fill="{fill}"/>' + hatch_svg
            + f'<path d="{path_d}" fill="none" stroke="{coast}" stroke-width="4" stroke-linejoin="round"/>'
            f'<path d="{path_d}" fill="none" stroke="{coast}" stroke-width="1.4" opacity=".6" transform="translate(0,10)"/>')


def hill_motif(x, y, w=150, color=None):
    """Batik mountain/cloud bump (blue hills on maps, like batik 'gunungan' scallops)."""
    color = color or P["indigo_hi"]
    return (f'<path d="M{x-w/2},{y} Q{x-w/4},{y-w*.55} {x},{y-w*.2} Q{x+w/4},{y-w*.6} {x+w/2},{y} Z" fill="{color}" {_gstroke(2)}/>'
            f'<path d="M{x-w/3},{y-6} q{w/6:.0f},-{w*.2:.0f} {w/3:.0f},0" fill="none" stroke="#a9b7e6" stroke-width="2"/>')
