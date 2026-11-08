"""svgkit: detailed, pre-animated building blocks for fakta-shorts scene SVGs.

Import it from a small generator script in the project folder:

    import sys; sys.path.insert(0, "<skill>/scripts")
    from svgkit import *

    parts = [
        sky("#e9d9b8", "#cfd3c4"),
        clouds(4, y=(380, 640), seed=1),
        birds(5, y=(520, 700), seed=2),
        mountain_range(1080, base_y=1100, color="#8c8f7a", seed=3),
        ground(1100, "#7f8f5e", "#6b7b4e"),
        forest(0, 1080, 1180, n=14, depth=0.4, seed=4),
        person(420, 1500, pose="chop", tool="axe", hat="caping", at=0.0),
        tree(560, 1500, kind="round", h=420, fall_at=1.8, fall_dir=1),
        dirt_burst(470, 1500, at=0.6),
        grass(1560, "#5c6b44", seed=5),
    ]
    write_scene("scenes/s07.svg", parts)

Every function returns an SVG string with data-anim attributes already set, so the pieces move on
their own (sway, walk, chop, flicker, drift…). Coordinates are stage pixels (1080x1920).
Use `seed` to get different but repeatable variations.
"""
import math
import random

_uid = [0]


def _id(prefix="k"):
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


# ---------------------------------------------------------------- colour helpers
def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    """Blend two hex colours: t=0 -> c1, t=1 -> c2. Use it for atmospheric depth."""
    a, b = _hex(c1), _hex(c2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    """Darken (k<0) or lighten (k>0) a hex colour by k (-1..1)."""
    return mix(c, "#000000", -k) if k < 0 else mix(c, "#ffffff", k)


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- scene wrapper
def write_scene(path, parts, bg="#e9dcc0"):
    """Write a complete scene SVG from a list of part strings (bottom layer first)."""
    body = "\n".join(p for p in parts if p)
    svg = (f'<svg viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg">\n'
           f'<rect width="1080" height="1920" fill="{bg}"/>\n{body}\n</svg>\n')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return path


def sky(top, bottom, y0=0, y1=1920):
    gid = _id("sky")
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></linearGradient></defs>'
            f'<rect x="0" y="{y0}" width="1080" height="{y1 - y0}" fill="url(#{gid})"/>')


def depth(content, d):
    """Wrap parts in a parallax layer (0.1 far … 1 near)."""
    return f'<g data-depth="{d}">{content}</g>'


def group(content, anim=None, **data):
    """Wrap content in an animated group: group(x, "pop", at=1.2) -> <g data-anim="pop" data-at="1.2">."""
    attrs = (f' data-anim="{anim}"' if anim else "") + "".join(f' data-{k.replace("_", "-")}="{v}"' for k, v in data.items())
    return f"<g{attrs}>{content}</g>"


# ---------------------------------------------------------------- sky things
def sun(x, y, r=90, color="#f3d48a", rays=True):
    out = []
    if rays:
        rr = "".join(f'<path d="M0 {-r * 1.25} L{r * .09} {-r * 1.9} L{-r * .09} {-r * 1.9}Z" transform="rotate({a})"/>' for a in range(0, 360, 20))
        out.append(f'<g transform="translate({x} {y})"><g data-anim="spin" data-period="60" fill="{color}" opacity=".45">{rr}</g></g>')
    out.append(f'<circle cx="{x}" cy="{y}" r="{r * 1.35}" fill="{color}" opacity=".25" data-anim="pulse" data-period="5"/>')
    out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')
    return "".join(out)


def cloud(x, y, w=320, color="#f4eee2", speed=8):
    h = w * .42
    shadow = shade(color, -.12)
    bumps = [(.18, .62, .2), (.36, .42, .26), (.58, .38, .24), (.76, .55, .19), (.5, .66, .22)]
    circles = "".join(f'<circle cx="{f(x + w * bx)}" cy="{f(y + h * by)}" r="{f(w * br)}"/>' for bx, by, br in bumps)
    base = f'<rect x="{f(x + w * .05)}" y="{f(y + h * .6)}" width="{f(w * .9)}" height="{f(h * .4)}" rx="{f(h * .2)}"/>'
    under = f'<rect x="{f(x + w * .05)}" y="{f(y + h * .78)}" width="{f(w * .9)}" height="{f(h * .22)}" rx="{f(h * .11)}" fill="{shadow}"/>'
    return f'<g data-anim="drift" data-speed="{speed}"><g fill="{color}">{circles}{base}</g>{under}</g>'


def clouds(n, y=(300, 700), seed=0, color="#f4eee2", x=(-80, 1000)):
    r = random.Random(seed)
    return "".join(cloud(r.uniform(*x), r.uniform(*y), r.uniform(200, 380), mix(color, "#ffffff", r.uniform(0, .3)),
                         r.choice([-1, 1]) * r.uniform(5, 16)) for _ in range(n))


def birds(n, y=(450, 750), seed=0, color="#3b302a", x=(-150, 700), speed=(55, 95)):
    r = random.Random(seed)
    out = []
    for i in range(n):
        s = r.uniform(.6, 1.2)
        bx, by = r.uniform(*x), r.uniform(*y)
        wing = f'<path d="M{-20 * s} 0 Q{-10 * s} {-10 * s} 0 0 Q{10 * s} {-10 * s} {20 * s} 0 Q{10 * s} {-4 * s} 0 {4 * s} Q{-10 * s} {-4 * s} {-20 * s} 0Z" fill="{color}"/>'
        out.append(f'<g transform="translate({f(bx)} {f(by)})"><g data-anim="fly" data-speed="{f(r.uniform(*speed))}" data-phase="{f(r.uniform(0, 6))}">{wing}</g></g>')
    return "".join(out)


def stars(n, y=(0, 900), seed=0, color="#f5ecd0"):
    r = random.Random(seed)
    return "".join(f'<circle cx="{f(r.uniform(0, 1080))}" cy="{f(r.uniform(*y))}" r="{f(r.uniform(1.5, 4))}" fill="{color}" '
                   f'data-anim="twinkle" data-phase="{f(r.uniform(0, 6))}"/>' for _ in range(n))


# ---------------------------------------------------------------- land
def mountain_range(width=1080, base_y=1100, color="#8c8f7a", peaks=3, height=(260, 480), seed=0, snow=False, x0=0):
    r = random.Random(seed)
    out = []
    xs = sorted(r.uniform(x0 + 80, x0 + width - 80) for _ in range(peaks))
    for i, px in enumerate(xs):
        h = r.uniform(*height)
        hw = h * r.uniform(1.1, 1.6)
        c = mix(color, "#ffffff", .08 * (peaks - i - 1) / max(peaks - 1, 1))
        top = base_y - h
        out.append(f'<path d="M{f(px - hw)} {base_y} L{f(px - 18)} {f(top + 8)} Q{f(px)} {f(top - 6)} {f(px + 18)} {f(top + 8)} L{f(px + hw)} {base_y}Z" fill="{c}"/>')
        out.append(f'<path d="M{f(px)} {f(top)} L{f(px + 18)} {f(top + 8)} L{f(px + hw)} {base_y} L{f(px + hw * .25)} {base_y} L{f(px + 30)} {f(top + h * .45)}Z" fill="{shade(c, -.12)}"/>')
        for k in range(3):  # ridges
            yy = top + h * (.25 + k * .2)
            out.append(f'<path d="M{f(px - 6 - k * 9)} {f(yy)} l{f(-14 - k * 6)} {f(40 + k * 10)}" stroke="{shade(c, -.1)}" stroke-width="5" fill="none" stroke-linecap="round"/>')
        if snow:
            out.append(f'<path d="M{f(px - 18)} {f(top + 8)} Q{f(px)} {f(top - 6)} {f(px + 18)} {f(top + 8)} L{f(px + 50)} {f(top + 60)} L{f(px + 22)} {f(top + 48)} L{f(px)} {f(top + 66)} L{f(px - 24)} {f(top + 46)} L{f(px - 50)} {f(top + 58)}Z" fill="#f2eee6"/>')
    return "".join(out)


def volcano(x, base_y, w=760, h=470, color="#7d7468", erupting=False, at=0.0):
    top = base_y - h
    c2 = shade(color, -.15)
    out = [f'<path d="M{f(x - w / 2)} {base_y} L{f(x - 55)} {f(top + 10)} L{f(x + 55)} {f(top + 10)} L{f(x + w / 2)} {base_y}Z" fill="{color}"/>',
           f'<path d="M{f(x + 20)} {f(top + 10)} L{f(x + 55)} {f(top + 10)} L{f(x + w / 2)} {base_y} L{f(x + w * .12)} {base_y}Z" fill="{c2}"/>',
           f'<path d="M{f(x - 55)} {f(top + 10)} Q{f(x)} {f(top - 4)} {f(x + 55)} {f(top + 10)} Q{f(x)} {f(top + 24)} {f(x - 55)} {f(top + 10)}Z" fill="{shade(color, -.45)}"/>']
    for k in range(5):
        xx = x - 40 + k * 22
        out.append(f'<path d="M{f(xx)} {f(top + 30)} q{f(-10 + k * 4)} {f(80 + k * 20)} {f(-30 + k * 14)} {f(170 + k * 30)}" stroke="{c2}" stroke-width="7" fill="none" stroke-linecap="round" opacity=".7"/>')
    if erupting:
        out.append(f'<g data-anim="fade" data-at="{at}" data-dur="0.3"><ellipse cx="{x}" cy="{f(top + 6)}" rx="90" ry="40" fill="#f2a93b" opacity=".85" data-anim="flicker"/></g>')
        for k in range(4):
            out.append(f'<path d="M{f(x - 30 + k * 18)} {f(top + 12)} q{f(-20 + k * 14)} {f(90 + k * 30)} {f(-50 + k * 30)} {f(200 + k * 40)}" stroke="#e0702f" stroke-width="9" '
                       f'fill="none" stroke-linecap="round" data-anim="draw" data-at="{f(at + .2 * k)}" data-dur="1.6"/>')
        out.append(f'<g data-anim="fade" data-at="{at}" data-dur="0.5">{smoke_column(x, top, n=6, scale=1.6, color="#6d655d")}</g>')
        out.append(dirt_burst(x, top + 10, at=at, n=14, color="#3e3732", spread=180, height=-420, period=2.2))
    return "".join(out)


def hills(y, color="#7f8f5e", seed=0, amp=60, layers=2):
    r = random.Random(seed)
    out = []
    for L in range(layers):
        c = shade(color, -.08 * L)
        yy = y + L * 70
        pts = [(x, yy - r.uniform(0, amp)) for x in range(-100, 1281, 220)]
        d = f"M-100 1920 L{f(pts[0][0])} {f(pts[0][1])} " + " ".join(
            f"Q{f(pts[i][0] + 110)} {f(pts[i][1] - amp * .6)} {f(pts[i + 1][0])} {f(pts[i + 1][1])}" for i in range(len(pts) - 1)) + " L1280 1920Z"
        out.append(f'<path d="{d}" fill="{c}"/>')
    return "".join(out)


def ground(y, color="#7f8f5e", bottom=None, texture=True, seed=0):
    bottom = bottom or shade(color, -.18)
    gid = _id("gr")
    out = [f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>',
           f'<rect x="-60" y="{y}" width="1200" height="{1980 - y}" fill="url(#{gid})"/>']
    if texture:
        r = random.Random(seed)
        for _ in range(40):
            xx, yy = r.uniform(0, 1080), r.uniform(y + 30, 1900)
            w = r.uniform(20, 70)
            out.append(f'<path d="M{f(xx)} {f(yy)} q{f(w / 2)} -6 {f(w)} 0" stroke="{shade(color, -.12)}" stroke-width="4" fill="none" stroke-linecap="round" opacity=".6"/>')
    return "".join(out)


def grass(y, color="#5c6b44", seed=0, density=60, height=(30, 70), x=(-20, 1100)):
    """A row of swaying grass tufts along y."""
    r = random.Random(seed)
    out = []
    for _ in range(density):
        gx = r.uniform(*x)
        h = r.uniform(*height)
        c = mix(color, shade(color, .15), r.random())
        blades = "".join(f'<path d="M{f(gx + dx)} {y} Q{f(gx + dx + lean * .3)} {f(y - h * .6)} {f(gx + dx + lean)} {f(y - h * hk)} Q{f(gx + dx + lean * .3 + 4)} {f(y - h * .5)} {f(gx + dx + 7)} {y}Z"/>'
                         for dx, lean, hk in ((0, -14, .8), (6, 4, 1), (12, 18, .75)))
        out.append(f'<g fill="{c}" data-anim="sway" data-origin="bottom" data-amp="{f(r.uniform(.8, 2))}" data-period="{f(r.uniform(2.5, 4))}" data-phase="{f(r.uniform(0, 6))}">{blades}</g>')
    return "".join(out)


def water(y, color="#4f7f8a", seed=0, light="#e7efe9", h=None):
    """Water surface from y down, with moving wave lines."""
    r = random.Random(seed)
    out = [f'<rect x="-60" y="{y}" width="1200" height="{(h or 1980 - y)}" fill="{color}"/>']
    for k in range(14):
        yy = y + 20 + k * k * 6
        xx = r.uniform(-100, 900)
        w = r.uniform(80, 220) * (1 + k * .08)
        out.append(f'<path d="M{f(xx)} {f(yy)} q{f(w / 4)} -8 {f(w / 2)} 0 t{f(w / 2)} 0" stroke="{light}" stroke-width="{f(3 + k * .3)}" fill="none" '
                   f'stroke-linecap="round" opacity=".55" data-anim="drift float" data-speed="{f(r.uniform(-12, 12))}" data-period="{f(r.uniform(2, 4))}" data-amp=".3"/>')
    return "".join(out)


def ripple(x, y, rx=60, ry=16, n=3, color="#e7efe9", period=2.4):
    return "".join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="none" stroke="{color}" stroke-width="4" '
                   f'data-anim="ripple" data-period="{period}" data-phase="{f(i * period / n)}"/>' for i in range(n))


# ---------------------------------------------------------------- plants
def tree(x, y, kind="round", h=360, color=None, sway=True, fall_at=None, fall_dir=1, seed=0):
    """A detailed tree standing on (x, y). kind: round | palm | pine | bush | banana.
    fall_at=seconds makes it topple (fall_dir 1 = right, -1 = left)."""
    r = random.Random(seed)
    s = h / 360
    if kind == "palm":
        leaf = color or "#4f6b3d"
        trunk = "#6a5440"
        lean = r.uniform(-40, 40) * s
        tx, ty = x + lean, y - h
        body = [f'<path d="M{f(x - 10 * s)} {y} Q{f(x + lean * .2)} {f(y - h * .5)} {f(tx - 6 * s)} {f(ty)} L{f(tx + 6 * s)} {f(ty)} Q{f(x + lean * .2 + 14 * s)} {f(y - h * .5)} {f(x + 12 * s)} {y}Z" fill="{trunk}"/>']
        for k in range(1, 9):
            t = k / 9
            px = x + (tx - x) * t + lean * .2 * math.sin(t * math.pi)
            body.append(f'<path d="M{f(px - 9 * s)} {f(y - h * t)} l{f(18 * s)} -3" stroke="{shade(trunk, -.25)}" stroke-width="{f(3 * s)}"/>')
        fronds = []
        for a in (-160, -130, -100, -70, -40, -15, 10, -190, 30):
            L = r.uniform(130, 170) * s
            rad = math.radians(a)
            ex, ey = tx + math.cos(rad) * L, ty + math.sin(rad) * L * .6 + L * .35
            mx, my = tx + math.cos(rad) * L * .5, ty + math.sin(rad) * L * .6 - 20 * s
            c = mix(leaf, shade(leaf, -.2), r.random())
            fronds.append(f'<path d="M{f(tx)} {f(ty)} Q{f(mx)} {f(my - 18 * s)} {f(ex)} {f(ey)} Q{f(mx)} {f(my + 14 * s)} {f(tx)} {f(ty)}Z" fill="{c}"/>')
            for j in range(1, 7):  # leaflets
                t = j / 7
                lx, ly = tx + (ex - tx) * t, ty + (ey - ty) * t - math.sin(t * math.pi) * 18 * s
                fronds.append(f'<path d="M{f(lx)} {f(ly)} l{f(math.cos(rad + 1.2) * 26 * s)} {f(math.sin(rad + 1.2) * 26 * s + 14 * s)}" stroke="{c}" stroke-width="{f(6 * s)}" stroke-linecap="round"/>')
        body.append(f'<g data-anim="sway" data-pivot="{f(tx)} {f(ty)}" data-amp="2" data-period="{f(r.uniform(3, 4.5))}">{"".join(fronds)}'
                    f'<circle cx="{f(tx - 8 * s)}" cy="{f(ty + 12 * s)}" r="{f(9 * s)}" fill="#5a4636"/><circle cx="{f(tx + 8 * s)}" cy="{f(ty + 14 * s)}" r="{f(9 * s)}" fill="#4a3a2e"/></g>')
    elif kind == "pine":
        leaf = color or "#3f5a43"
        body = [f'<rect x="{f(x - 9 * s)}" y="{f(y - 60 * s)}" width="{f(18 * s)}" height="{f(60 * s)}" fill="#5a4636"/>']
        for k in range(4):
            w = (130 - k * 26) * s
            yb = y - 50 * s - k * 70 * s
            body.append(f'<path d="M{f(x - w)} {f(yb)} L{f(x)} {f(yb - 120 * s)} L{f(x + w)} {f(yb)}Z" fill="{leaf}"/>')
            body.append(f'<path d="M{f(x)} {f(yb - 120 * s)} L{f(x + w)} {f(yb)} L{f(x + w * .2)} {f(yb)}Z" fill="{shade(leaf, -.18)}"/>')
    elif kind == "banana":
        leaf = color or "#6f8a3e"
        body = [f'<path d="M{f(x - 10 * s)} {y} L{f(x - 6 * s)} {f(y - h * .55)} L{f(x + 6 * s)} {f(y - h * .55)} L{f(x + 10 * s)} {y}Z" fill="#7a7a46"/>']
        for a in (-150, -115, -70, -35, -95):
            rad = math.radians(a)
            L = r.uniform(150, 200) * s
            ex, ey = x + math.cos(rad) * L, y - h * .55 + math.sin(rad) * L
            body.append(f'<path d="M{x} {f(y - h * .55)} Q{f((x + ex) / 2 + 30 * s)} {f((y - h * .55 + ey) / 2 - 40 * s)} {f(ex)} {f(ey)} Q{f((x + ex) / 2 - 20 * s)} {f((y - h * .55 + ey) / 2 + 20 * s)} {x} {f(y - h * .55)}Z" '
                        f'fill="{mix(leaf, shade(leaf, .15), r.random())}" data-anim="sway" data-pivot="{x} {f(y - h * .55)}" data-amp="1.5" data-phase="{f(r.uniform(0, 6))}"/>')
    else:  # round / bush
        leaf = color or "#6f8350"
        trunk_h = h * (.45 if kind == "round" else .12)
        body = [f'<path d="M{f(x - 13 * s)} {y} L{f(x - 8 * s)} {f(y - trunk_h)} L{f(x + 8 * s)} {f(y - trunk_h)} L{f(x + 13 * s)} {y}Z" fill="#5e4936"/>',
                f'<path d="M{x} {f(y - trunk_h * .7)} l{f(36 * s)} {f(-50 * s)}" stroke="#5e4936" stroke-width="{f(9 * s)}" stroke-linecap="round"/>']
        cy = y - trunk_h - (h - trunk_h) * .45
        R = (h - trunk_h) * .42
        blobs = [(0, 0, 1), (-.62, .25, .72), (.62, .22, .74), (-.32, -.5, .7), (.35, -.48, .68), (0, .45, .7)]
        canopy = []
        for bx, by, br in blobs:
            canopy.append(f'<circle cx="{f(x + bx * R)}" cy="{f(cy + by * R)}" r="{f(br * R)}" fill="{leaf}"/>')
        for bx, by, br in blobs[1::2]:  # shadow side
            canopy.append(f'<circle cx="{f(x + bx * R + br * R * .25)}" cy="{f(cy + by * R + br * R * .2)}" r="{f(br * R * .75)}" fill="{shade(leaf, -.14)}" opacity=".8"/>')
        for _ in range(7):  # highlight dabs
            canopy.append(f'<circle cx="{f(x + r.uniform(-.7, .3) * R)}" cy="{f(cy + r.uniform(-.8, .1) * R)}" r="{f(r.uniform(.08, .16) * R)}" fill="{shade(leaf, .18)}"/>')
        body.append(f'<g data-anim="sway" data-pivot="{x} {f(y - trunk_h)}" data-amp="1.2" data-period="{f(r.uniform(3, 5))}" data-phase="{f(r.uniform(0, 6))}">{"".join(canopy)}</g>' if sway else "".join(canopy))
    inner = "".join(body)
    if fall_at is not None:
        inner = f'<g data-anim="fall" data-at="{fall_at}" data-pivot="{x} {y}" data-angle="{85 * fall_dir}">{inner}</g>'
    return inner


def forest(x0, x1, y, n=12, seed=0, kinds=("round", "round", "palm", "banana"), h=(240, 380), haze=0.0, haze_color="#e9dcc0", color=None):
    """A row of varied trees standing on y. haze 0..1 fades them toward haze_color for distance."""
    r = random.Random(seed)
    out = []
    xs = sorted(r.uniform(x0, x1) for _ in range(n))
    for i, xx in enumerate(xs):
        k = r.choice(kinds)
        base = color or {"round": "#6f8350", "palm": "#4f6b3d", "banana": "#6f8a3e", "pine": "#3f5a43", "bush": "#6f8350"}[k]
        out.append(tree(xx, y + r.uniform(-10, 10), kind=k, h=r.uniform(*h), color=mix(base, haze_color, haze), seed=seed * 100 + i))
    return "".join(out)


def vines(x, y, w, h, at=0.0, dur=2.0, seed=0, color="#4f6b3d", n=7):
    """Vines that grow over an area (x,y = top-left) — for jungle overgrowing ruins."""
    r = random.Random(seed)
    out = []
    for i in range(n):
        sx = x + r.uniform(0, w)
        pts = [(sx, y + h)]
        for k in range(1, 5):
            pts.append((sx + r.uniform(-60, 60), y + h - h * k / 4 * r.uniform(.7, 1)))
        d = f"M{f(pts[0][0])} {f(pts[0][1])} " + " ".join(f"T{f(px)} {f(py)}" for px, py in pts[1:])
        t0 = at + i * dur / n * .6
        out.append(f'<path d="{d}" stroke="{shade(color, -.1)}" stroke-width="7" fill="none" stroke-linecap="round" data-anim="draw" data-at="{f(t0)}" data-dur="{f(dur)}"/>')
        leaves = "".join(f'<ellipse cx="{f(px + r.choice([-12, 12]))}" cy="{f(py)}" rx="20" ry="10" fill="{mix(color, shade(color, .2), r.random())}" '
                         f'transform="rotate({r.randint(-40, 40)} {f(px)} {f(py)})" data-anim="pop"/>' for px, py in pts[1:])
        out.append(f'<g data-stagger="{f(dur / 5)}" data-at="{f(t0 + .2)}">{leaves}</g>')
    return "".join(out)


# ---------------------------------------------------------------- people
SKIN = ["#c58c5c", "#a9714a", "#d9a074", "#8a5a3a"]


def person(x, y, h=260, pose="walk", facing=1, shirt="#8a3a26", pants="#3a2f2a", skin=None, hat=None, tool=None,
           silhouette=None, period=0.9, phase=0.0, speed=0, at=0.0, seed=0):
    """A small articulated figure standing on (x, y).
    pose: walk | stand | chop | dig | carry | point | cheer
    tool: axe | hoe | shovel | spear | torch | brush (for chop/dig/point)
    hat: caping | peci | helmet | tricorn | turban
    silhouette='#2f2722' draws the whole figure in one colour (crowds, workers in the distance).
    speed (px/s) makes the figure walk across the frame; facing=-1 mirrors it."""
    r = random.Random(seed)
    skin = skin or r.choice(SKIN)
    if silhouette:
        shirt = pants = skin = silhouette
    s = h / 180
    hat_c = silhouette or "#c9a35a"
    P = period
    walking = pose in ("walk", "carry")

    def leg(ph, c):
        anim = f'data-anim="swing" data-pivot="0 -86" data-angle="26" data-period="{P}" data-phase="{ph}"' if walking else ""
        return (f'<g {anim}><path d="M-8 -90 L8 -90 L7 -46 L4 -4 L-5 -4 L-6 -46Z" fill="{c}"/>'
                f'<path d="M-6 -6 L14 -6 Q16 0 10 0 L-6 0Z" fill="{shade(c, -.3)}"/></g>')

    def arm(ph, c, angle=22):
        anim = f'data-anim="swing" data-pivot="0 -146" data-angle="{angle}" data-period="{P}" data-phase="{ph}"' if walking else ""
        return (f'<g {anim}><path d="M-6 -148 L6 -148 L5 -104 L-5 -104Z" fill="{c}"/>'
                f'<circle cx="0" cy="-100" r="6" fill="{skin}"/></g>')

    tools = {
        "axe": f'<path d="M-3 -104 L3 -104 L3 -30 L-3 -30Z" fill="#8a6a4a"/><path d="M3 -40 L26 -50 L24 -20 L3 -28Z" fill="#9aa4a6"/>',
        "hoe": f'<path d="M-3 -104 L3 -104 L3 -20 L-3 -20Z" fill="#8a6a4a"/><path d="M3 -26 L30 -18 L28 -8 L3 -16Z" fill="#9aa4a6"/>',
        "shovel": f'<path d="M-3 -104 L3 -104 L3 -36 L-3 -36Z" fill="#8a6a4a"/><path d="M-12 -38 L12 -38 L10 -10 Q0 0 -10 -10Z" fill="#9aa4a6"/>',
        "spear": f'<path d="M-2 -200 L2 -200 L2 -40 L-2 -40Z" fill="#6a5440"/><path d="M0 -226 L7 -200 L-7 -200Z" fill="#9aa4a6"/>',
        "torch": f'<path d="M-3 -104 L3 -104 L3 -150 L-3 -150Z" fill="#6a5440"/><path d="M0 -190 Q14 -165 6 -150 L-6 -150 Q-14 -165 0 -190Z" fill="#f2a93b" data-anim="flicker"/>',
        "brush": f'<path d="M-2 -104 L2 -104 L2 -50 L-2 -50Z" fill="#8a6a4a"/><path d="M-8 -52 L8 -52 L10 -30 L-10 -30Z" fill="#c9a35a"/>',
    }
    tool_svg = tools.get(tool, "")

    if pose == "chop":
        work = (f'<g data-anim="chop" data-pivot="0 -146" data-angle="95" data-period="{P}" data-phase="{phase}" data-at="{at}">'
                f'<g transform="rotate(-70 0 -146)"><path d="M-6 -148 L6 -148 L5 -104 L-5 -104Z" fill="{shirt}"/><circle cx="0" cy="-100" r="6" fill="{skin}"/><g transform="rotate(-55 0 -100)">{tool_svg}</g></g></g>')
        front_arm = work
        back_arm = f'<g transform="rotate(-40 0 -146)">{arm(0, shade(shirt, -.15))}</g>'
    elif pose == "dig":
        work = (f'<g data-anim="chop" data-pivot="0 -146" data-angle="40" data-period="{P * 1.3}" data-phase="{phase}">'
                f'<g transform="rotate(30 0 -146)"><path d="M-6 -148 L6 -148 L5 -104 L-5 -104Z" fill="{shirt}"/><circle cx="0" cy="-100" r="6" fill="{skin}"/><g transform="rotate(-35 0 -100)">{tool_svg}</g></g></g>')
        front_arm, back_arm = work, f'<g transform="rotate(20 0 -146)">{arm(0, shade(shirt, -.15))}</g>'
    elif pose == "point":
        front_arm = f'<g transform="rotate(-100 0 -146)"><path d="M-6 -148 L6 -148 L5 -104 L-5 -104Z" fill="{shirt}"/><circle cx="0" cy="-100" r="6" fill="{skin}"/>{tool_svg}</g>'
        back_arm = arm(0, shade(shirt, -.15))
    elif pose == "cheer":
        front_arm = f'<g data-anim="swing" data-pivot="0 -146" data-angle="12" data-period=".5"><g transform="rotate(-150 0 -146)">{arm(0, shirt)}</g></g>'
        back_arm = f'<g data-anim="swing" data-pivot="0 -146" data-angle="12" data-period=".5" data-phase="1.5"><g transform="rotate(150 0 -146)">{arm(0, shade(shirt, -.15))}</g></g>'
    else:
        front_arm = arm(math.pi + phase, shirt) + (tool_svg if tool and pose in ("stand", "walk") else "")
        back_arm = arm(phase, shade(shirt, -.15))

    hats = {
        "caping": f'<path d="M-30 -186 L0 -212 L30 -186Z" fill="{hat_c}"/><path d="M-30 -186 L30 -186" stroke="{shade(hat_c, -.25)}" stroke-width="3"/>',
        "peci": f'<rect x="-13" y="-200" width="26" height="12" rx="2" fill="{silhouette or "#222"}"/>',
        "helmet": f'<path d="M-17 -186 Q0 -214 17 -186Z" fill="{silhouette or "#4a5a3a"}"/><rect x="-20" y="-188" width="40" height="5" fill="{silhouette or "#4a5a3a"}"/>',
        "tricorn": f'<path d="M-22 -188 L0 -206 L22 -188 L0 -194Z" fill="{silhouette or "#1f2a44"}"/>',
        "turban": f'<path d="M-16 -186 Q-18 -206 0 -208 Q18 -206 16 -186Z" fill="{silhouette or "#efe6d4"}"/>',
    }
    head = (f'<path d="M-4 -164 L4 -164 L4 -156 L-4 -156Z" fill="{skin}"/>'
            f'<circle cx="2" cy="-176" r="15" fill="{skin}"/>'
            + ("" if silhouette else f'<path d="M-13 -180 Q0 -196 16 -180 Q8 -186 -13 -180Z" fill="#2a211c"/><circle cx="10" cy="-176" r="2" fill="#2a211c"/>')
            + hats.get(hat, ""))
    torso = (f'<path d="M-14 -158 Q0 -164 14 -158 L13 -92 L-13 -92Z" fill="{shirt}"/>'
             + ("" if silhouette else f'<path d="M-13 -100 L13 -100 L13 -88 L-13 -88Z" fill="{shade(pants, .1)}"/>'))
    carry = ""
    if pose == "carry":
        basket = lambda bx: (f'<g data-anim="sway" data-pivot="{bx} -158" data-amp="3" data-period="{P}"><path d="M{bx} -158 L{bx - 14} -100 M{bx} -158 L{bx + 14} -100" stroke="{shade(pants, .2)}" stroke-width="2"/>'
                             f'<path d="M{bx - 22} -100 L{bx + 22} -100 L{bx + 16} -66 L{bx - 16} -66Z" fill="{silhouette or "#9a7a4a"}"/></g>')
        carry = f'<path d="M-80 -160 L80 -156" stroke="{silhouette or "#6a5440"}" stroke-width="6" stroke-linecap="round"/>' + basket(-74) + basket(74)
    body = back_arm + leg(phase, shade(pants, -.15)) + leg(math.pi + phase, pants) + torso + head + carry + front_arm
    body_anim = f'data-anim="walk" data-period="{P}" data-phase="{phase}"' if walking else 'data-anim="float" data-amp=".15" data-period="3"'
    fig = f'<g transform="translate({f(x)} {f(y)}) scale({f(s * facing)} {f(s)})"><g {body_anim}>{body}</g></g>'
    if speed:
        fig = f'<g data-anim="drift" data-speed="{speed}">{fig}</g>'
    return fig


def crowd(x0, x1, y, n=8, seed=0, pose="walk", silhouette="#2f2722", h=(200, 260), speed=0, facing=1, hats=("caping", None, "peci"), tool=None):
    r = random.Random(seed)
    out = []
    for i in range(n):
        xx = x0 + (x1 - x0) * (i + r.uniform(-.3, .3)) / max(n - 1, 1)
        out.append(person(xx, y + r.uniform(-12, 12), h=r.uniform(*h), pose=pose, facing=facing, silhouette=silhouette,
                          hat=r.choice(hats), tool=tool, phase=r.uniform(0, 6), period=r.uniform(.8, 1.0), speed=speed, seed=seed * 50 + i))
    return "".join(out)


# ---------------------------------------------------------------- effects
def smoke_column(x, y, n=4, scale=1.0, color="#8f877d", at=0.0, period=4.0):
    out = []
    for i in range(n):
        w = 150 * scale
        c = mix(color, "#ffffff", .1 * (i % 2))
        puff = (f'<circle cx="{f(x - w * .25)}" cy="{f(y)}" r="{f(w * .3)}"/><circle cx="{f(x + w * .2)}" cy="{f(y - w * .08)}" r="{f(w * .36)}"/>'
                f'<circle cx="{f(x)}" cy="{f(y - w * .28)}" r="{f(w * .3)}"/>')
        out.append(f'<g fill="{c}" data-anim="rise" data-period="{period}" data-phase="{f(i * period / n)}" data-dist="{f(420 * scale)}" data-opacity=".85">{puff}</g>')
    return "".join(out)


def fire(x, y, s=1.0):
    def flame(w, hh, c, ph):
        return (f'<path d="M{f(x - w)} {f(y)} Q{f(x - w)} {f(y - hh * .6)} {f(x)} {f(y - hh)} Q{f(x + w)} {f(y - hh * .6)} {f(x + w)} {f(y)}Z" fill="{c}" '
                f'data-anim="flicker pulse" data-origin="bottom" data-period=".35" data-amp="3" data-phase="{ph}"/>')
    logs = f'<path d="M{f(x - 60 * s)} {f(y + 6)} L{f(x + 60 * s)} {f(y - 10)}" stroke="#5a3f2c" stroke-width="{f(14 * s)}" stroke-linecap="round"/>' \
           f'<path d="M{f(x - 60 * s)} {f(y - 10)} L{f(x + 60 * s)} {f(y + 6)}" stroke="#4a3426" stroke-width="{f(14 * s)}" stroke-linecap="round"/>'
    glow = f'<ellipse cx="{x}" cy="{f(y - 40 * s)}" rx="{f(140 * s)}" ry="{f(120 * s)}" fill="#f2a93b" opacity=".18" data-anim="pulse" data-period=".6" data-amp="2"/>'
    return glow + flame(50 * s, 150 * s, "#e0702f", 0) + flame(34 * s, 110 * s, "#f2a93b", 1.3) + flame(18 * s, 64 * s, "#fde3a0", 2.1) + logs + \
        dirt_burst(x, y - 80 * s, n=8, color="#ffb347", spread=50, height=-200, period=1.6, size=4)


def dirt_burst(x, y, at=0.0, n=10, color="#6a5440", spread=90, height=-260, period=1.2, size=7, seed=0):
    """Particles thrown up and falling back, looping: dirt from a hoe, debris, sparks."""
    r = random.Random(seed + int(x))
    return "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r.uniform(size * .5, size))}" fill="{color}" data-anim="burst" data-at="{at}" '
                   f'data-vx="{f(r.uniform(-spread, spread))}" data-vy="{f(height * r.uniform(.6, 1.1))}" data-period="{period}" data-phase="{f(r.uniform(0, period))}"/>'
                   for _ in range(n))


def cover(content, at=0.0, dur=1.6, direction="up"):
    """Make these parts APPEAR by wiping in, so they cover whatever is behind them
    (ash piling up on a temple, water rising, jungle spreading). Starts invisible."""
    return f'<g data-anim="reveal" data-dir="{direction}" data-at="{at}" data-dur="{dur}">{content}</g>'


def uncover(content, at=0.0, dur=1.6, direction="down"):
    """Make these parts DISAPPEAR by wiping away, uncovering what is behind them
    (clearing a jungle, digging out a ruin). Starts visible."""
    return f'<g data-anim="cover" data-dir="{direction}" data-at="{at}" data-dur="{dur}">{content}</g>'


def ash_mound(x, y, w, h, color="#8f877d", seed=0):
    """A heap of ash/earth sitting on y (use inside cover() to make it pile up)."""
    r = random.Random(seed)
    pts = [(x - w / 2 + w * i / 8, y - h * math.sin(math.pi * i / 8) * r.uniform(.85, 1.05)) for i in range(9)]
    d = f"M{f(x - w / 2)} {f(y)} " + " ".join(f"L{f(px)} {f(py)}" for px, py in pts) + f" L{f(x + w / 2)} {f(y)}Z"
    streaks = "".join(f'<path d="M{f(x - w * .35 + i * w * .1)} {f(y - h * .2)} q{f(w * .05)} {f(-h * .25)} {f(w * .12)} {f(-h * .3)}" stroke="{shade(color, -.12)}" stroke-width="6" fill="none" stroke-linecap="round"/>' for i in range(7))
    return f'<path d="{d}" fill="{color}"/>{streaks}'


def count(x, y, to, frm=0, at=0.0, dur=1.5, size=90, color="#3a2a20", prefix="", suffix="", anchor="middle"):
    """A number that counts up (Indonesian thousands separator)."""
    return (f'<text x="{x}" y="{y}" font-family="Lora, serif" font-weight="600" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
            f'data-anim="count" data-from="{frm}" data-to="{to}" data-at="{at}" data-dur="{dur}" data-prefix="{prefix}" data-suffix="{suffix}">{prefix}{frm}{suffix}</text>')


def label(x, y, text, size=40, color="#3a2a20", at=None, italic=False, anchor="middle", weight=500):
    anim = f' data-anim="fade" data-at="{at}"' if at is not None else ""
    st = ' font-style="italic"' if italic else ""
    return f'<text x="{x}" y="{y}" font-family="Lora, serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{st}{anim}>{text}</text>'


# ---------------------------------------------------------------- architecture / textures
def masonry(x, y, w, h, color="#8a8175", bw=46, bh=22, seed=0, mortar=None):
    """A stone-block wall texture filling the rectangle (temples, forts, roads)."""
    r = random.Random(seed)
    mortar = mortar or shade(color, -.25)
    out = [f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{mortar}"/>']
    row = 0
    yy = y
    while yy < y + h - 1:
        off = (bw / 2) if row % 2 else 0
        xx = x - off
        while xx < x + w:
            bx0, bx1 = max(xx + 1.5, x), min(xx + bw - 1.5, x + w)
            if bx1 > bx0:
                out.append(f'<rect x="{f(bx0)}" y="{f(yy + 1.5)}" width="{f(bx1 - bx0)}" height="{f(min(bh, y + h - yy) - 3)}" fill="{mix(color, shade(color, .12 if r.random() > .5 else -.08), r.random())}"/>')
            xx += bw
        yy += bh
        row += 1
    return "".join(out)


def stepped_temple(cx, base_y, w=760, levels=6, color="#8a8175", stupas=True, relief=True, seed=0, main_stupa=True):
    """A terraced stone monument (candi / ziggurat): stone courses, relief bands, stairs, small stupas, crown stupa."""
    r = random.Random(seed)
    out = []
    lh = 46
    dark = shade(color, -.18)
    for L in range(levels):
        ww = w * (1 - L * .12)
        y0 = base_y - (L + 1) * lh
        x0 = cx - ww / 2
        out.append(masonry(x0, y0, ww, lh, color=mix(color, shade(color, .08), L / levels), bw=34, bh=lh / 2, seed=seed + L))
        out.append(f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(ww)}" height="5" fill="{shade(color, .2)}"/>')
        out.append(f'<rect x="{f(cx + ww * .18)}" y="{f(y0)}" width="{f(ww * .32)}" height="{lh}" fill="{dark}" opacity=".35"/>')  # shadow side
        if relief and L < levels - 2:
            for k in range(int(ww // 60)):
                px = x0 + 14 + k * 60
                out.append(f'<rect x="{f(px)}" y="{f(y0 + 10)}" width="40" height="{lh - 20}" fill="{shade(color, -.12)}" opacity=".7"/>'
                           f'<circle cx="{f(px + 20)}" cy="{f(y0 + lh / 2)}" r="6" fill="{shade(color, .1)}" opacity=".8"/>')
        if stupas and L >= levels - 3:
            ns = int(ww // 70)
            for k in range(ns):
                sx = x0 + 35 + k * (ww - 70) / max(ns - 1, 1)
                out.append(f'<path d="M{f(sx - 16)} {f(y0)} Q{f(sx - 16)} {f(y0 - 30)} {f(sx)} {f(y0 - 32)} Q{f(sx + 16)} {f(y0 - 30)} {f(sx + 16)} {f(y0)}Z" fill="{shade(color, .05)}"/>'
                           f'<rect x="{f(sx - 3)}" y="{f(y0 - 44)}" width="6" height="12" fill="{dark}"/>'
                           f'<path d="M{f(sx - 8)} {f(y0 - 14)} l6 0 l-3 5z M{f(sx + 2)} {f(y0 - 20)} l6 0 l-3 5z" fill="{dark}"/>')
    # central stairs
    sh = levels * lh
    out.append(f'<rect x="{f(cx - 22)}" y="{f(base_y - sh)}" width="44" height="{sh}" fill="{shade(color, -.1)}"/>')
    for k in range(int(sh // 8)):
        out.append(f'<rect x="{f(cx - 22)}" y="{f(base_y - sh + k * 8)}" width="44" height="3" fill="{shade(color, -.28)}"/>')
    for k in range(levels):
        out.append(f'<path d="M{f(cx - 30)} {f(base_y - (k + 1) * lh)} q30 -26 60 0" fill="none" stroke="{shade(color, .15)}" stroke-width="5"/>')
    if main_stupa:
        top = base_y - levels * lh
        R = w * .09
        out.append(f'<path d="M{f(cx - R)} {f(top)} Q{f(cx - R)} {f(top - R * 1.2)} {f(cx)} {f(top - R * 1.25)} Q{f(cx + R)} {f(top - R * 1.2)} {f(cx + R)} {f(top)}Z" fill="{shade(color, .06)}"/>'
                   f'<path d="M{f(cx)} {f(top - R * 1.25)} Q{f(cx + R)} {f(top - R * 1.2)} {f(cx + R)} {f(top)} L{f(cx + R * .2)} {f(top)}Z" fill="{dark}" opacity=".45"/>'
                   f'<rect x="{f(cx - R * .3)}" y="{f(top - R * 1.55)}" width="{f(R * .6)}" height="{f(R * .3)}" fill="{color}"/>'
                   f'<path d="M{f(cx - R * .12)} {f(top - R * 1.55)} L{f(cx)} {f(top - R * 2.3)} L{f(cx + R * .12)} {f(top - R * 1.55)}Z" fill="{dark}"/>')
    return "".join(out)


def frame_border(color="#b5482f", inner="#f1e6cf", inset=40, top=440, bottom=1360):
    """A decorative picture frame around the middle of the screen (fresco / museum vignette)."""
    x0, x1 = inset, 1080 - inset
    return (f'<rect x="{x0}" y="{top}" width="{x1 - x0}" height="{bottom - top}" fill="none" stroke="{color}" stroke-width="26"/>'
            f'<rect x="{x0 + 22}" y="{top + 22}" width="{x1 - x0 - 44}" height="{bottom - top - 44}" fill="none" stroke="{inner}" stroke-width="6"/>'
            + "".join(f'<rect x="{x0 + 40 + k * 60}" y="{top - 6}" width="30" height="12" fill="{inner}"/>' for k in range(int((x1 - x0 - 60) // 60))))
