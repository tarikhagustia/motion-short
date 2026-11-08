"""buku kit: warm storybook pieces for the `buku` style.

    import sys; sys.path[:0] = ["<skill>/scripts", "<skill>/styles/buku"]
    from svgkit import *          # base helpers: write_scene, group, depth, cover, mix, shade ...
    from kit import *             # this file

Look: soft muted flat colours, thin dark-brown pencil outline (`INK`, ~3 px, slightly wobbly),
soft shading blobs, round friendly characters with dot eyes and blush, watercolour vignette circles
behind characters, lots of cream. Everything breathes (blink, bob, sway, float).
"""
import math
import random

from svgkit import _id, f, mix, shade, group, depth

INK = "#4b3427"
P = {
    "cream": "#f4ead6", "paper": "#efe3cc", "brown": "#7a4f35", "tan": "#c9a57e", "skin": "#efc29a",
    "blush": "#ee9c86", "red": "#d4552b", "orange": "#e58a4a", "mustard": "#e3b55b", "sage": "#a9c3a6",
    "mint": "#bcd8c9", "teal": "#6ea4a6", "sea": "#7fb0b8", "deep": "#4f7f8c", "sky": "#cfe2e6",
    "pink": "#f2c9bd", "lilac": "#c9b8d6", "grey": "#b9b2a6", "white": "#fbf6ec",
}


def _ink(w=3):
    return f'stroke="{INK}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"'


def wobble_path(pts, closed=True, seed=0, amt=2.5):
    """Smooth path through points with a tiny hand-drawn wobble."""
    r = random.Random(seed)
    pts = [(x + r.uniform(-amt, amt), y + r.uniform(-amt, amt)) for x, y in pts]
    n = len(pts)
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    rng = range(n if closed else n - 1)
    for i in rng:
        p0, p1 = pts[i - 1] if (i > 0 or closed) else pts[i], pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d + (" Z" if closed else "")


def blob_path(x, y, rx, ry, seed=0, n=10, rough=0.08):
    r = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        k = 1 + r.uniform(-rough, rough)
        pts.append((x + math.cos(a) * rx * k, y + math.sin(a) * ry * k))
    return wobble_path(pts, True, seed, 1.5)


# ---------------------------------------------------------------- backgrounds
def paper_bg(color=None):
    color = color or P["paper"]
    gid = _id("pb")
    return (f'<defs><radialGradient id="{gid}" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="{shade(color,.06)}"/>'
            f'<stop offset="1" stop-color="{shade(color,-.06)}"/></radialGradient></defs><rect width="1080" height="1920" fill="url(#{gid})"/>')


def wc_circle(x, y, r, color=None, seed=0, opacity=0.9):
    """Watercolour vignette disc behind a character: rough edge, darker rim, soft inner wash."""
    color = color or P["mint"]
    fid = _id("wc")
    return (f'<defs><filter id="{fid}" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="3" seed="{seed+3}" result="t"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="t" scale="26"/></filter></defs>'
            f'<g filter="url(#{fid})" opacity="{opacity}">'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{shade(color,-.12)}" stroke-width="16" opacity=".6"/>'
            f'<circle cx="{x-r*.25:.0f}" cy="{y-r*.3:.0f}" r="{r*.45:.0f}" fill="{shade(color,.12)}" opacity=".6"/></g>')


def sky_wash(top, bottom, y1=1920):
    gid = _id("sw")
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></linearGradient></defs><rect width="1080" height="{y1}" fill="url(#{gid})"/>')


def soft_clouds(n=4, y=(150, 600), seed=0, color="#f7efe4"):
    r = random.Random(seed)
    out = ""
    for _ in range(n):
        x, yy, w = r.uniform(-100, 1000), r.uniform(*y), r.uniform(160, 300)
        d = blob_path(x, yy, w / 2, w / 7, seed=r.randint(0, 999), n=12, rough=.18)
        out += f'<g data-anim="drift" data-speed="{r.uniform(4,10)*(1 if r.random()>.5 else -1):.1f}"><path d="{d}" fill="{color}" opacity=".9"/></g>'
    return out


def ground_strata(y, colors=("#c98a5e", "#b8774d", "#a6653f"), seed=0):
    """Layered soil/sand bands with wobbly edges and pebble dots (desert, cross-sections)."""
    r = random.Random(seed)
    out = ""
    for i, c in enumerate(colors):
        yy = y + i * 120
        pts = [(-20, yy + r.uniform(-10, 10))] + [(x, yy + r.uniform(-14, 14)) for x in range(100, 1101, 140)] + [(1100, 1940), (-20, 1940)]
        out += f'<path d="{wobble_path(pts, True, seed+i, 3)}" fill="{c}"/>'
        out += "".join(f'<ellipse cx="{r.uniform(0,1080):.0f}" cy="{r.uniform(yy+20, yy+110):.0f}" rx="{r.uniform(4,9):.0f}" ry="{r.uniform(3,5):.0f}" '
                       f'fill="{shade(c,-.15)}" opacity=".7"/>' for _ in range(16))
    return out


def bush(x, y, w=140, color=None, seed=0):
    color = color or P["sage"]
    r = random.Random(seed)
    out = ""
    for k in range(3):
        cx, cy, rr = x + (k - 1) * w * .3, y - w * (.25 + .1 * (k == 1)), w * (.3 + .08 * (k == 1))
        out += f'<path d="{blob_path(cx, cy, rr, rr*.85, seed+k, 9, .12)}" fill="{shade(color, -.08*k)}" {_ink(2.2)}/>'
    return f'<g data-anim="sway" data-pivot="{x} {y}" data-period="{r.uniform(3.5,5):.1f}" data-amp=".6">{out}</g>'


def grass_tufts(y, n=14, color=None, seed=0, x=(0, 1080)):
    color = color or "#8da36f"
    r = random.Random(seed)
    out = ""
    for _ in range(n):
        xx = r.uniform(*x)
        h = r.uniform(26, 50)
        blades = "".join(f'<path d="M{f(xx+o)},{y} q{o*.4:.0f},-{h*.6:.0f} {o*1.2+r.uniform(-4,4):.0f},-{h:.0f}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
                         for o in (-8, 0, 8))
        out += f'<g data-anim="sway" data-pivot="{f(xx)} {y}" data-period="{r.uniform(2.5,4):.1f}" data-phase="{r.uniform(0,6):.1f}">{blades}</g>'
    return out


def underwater_bg(top=None, bottom=None, rays=True, seed=0):
    """Soft sea: gradient, swaying light rays, a few drifting particles."""
    top = top or "#a9d0d2"
    bottom = bottom or "#4f7f8c"
    out = sky_wash(top, bottom)
    if rays:
        r = random.Random(seed)
        for k in range(5):
            x = r.uniform(80, 1000)
            out += (f'<g data-anim="sway" data-pivot="{x:.0f} 0" data-period="{r.uniform(6,9):.1f}" data-amp="1.5">'
                    f'<path d="M{x-30:.0f},0 L{x+30:.0f},0 L{x+150:.0f},1400 L{x-80:.0f},1400 Z" fill="#ffffff" opacity=".07"/></g>')
    return out


def seaweed(x, y, h=360, color=None, seed=0):
    color = color or "#7fa66e"
    r = random.Random(seed)
    pts = [(x, y)]
    for k in range(1, 7):
        pts.append((x + math.sin(k * 1.2 + r.random()) * 22, y - h * k / 6))
    left = [(px - 14 * (1 - i / 7), py) for i, (px, py) in enumerate(pts)]
    right = [(px + 14 * (1 - i / 7), py) for i, (px, py) in enumerate(pts)][::-1]
    d = wobble_path(left + right, True, seed, 1)
    return f'<g data-anim="sway" data-pivot="{x} {y}" data-period="{r.uniform(3,4.5):.1f}" data-amp="2.2"><path d="{d}" fill="{color}" {_ink(2.4)}/></g>'


def rock(x, y, w=200, h=110, color=None, seed=0):
    color = color or P["grey"]
    d = blob_path(x, y - h / 2, w / 2, h / 2, seed, 9, .14)
    return (f'<path d="{d}" fill="{color}" {_ink(2.6)}/>'
            f'<path d="{blob_path(x-w*.15, y-h*.62, w*.22, h*.16, seed+1, 7, .1)}" fill="{shade(color,.15)}" opacity=".8"/>')


def bubbles_rise(x, y, n=6, seed=0, color="#e8f4f2"):
    r = random.Random(seed)
    return "".join(f'<circle cx="{x+r.uniform(-30,30):.0f}" cy="{y}" r="{r.uniform(6,16):.0f}" fill="none" stroke="{color}" stroke-width="3" '
                   f'data-anim="rise" data-period="{r.uniform(2.5,4):.1f}" data-dist="{r.uniform(300,600):.0f}" data-phase="{r.uniform(0,4):.1f}"/>' for _ in range(n))


# ---------------------------------------------------------------- characters & props
def eyes(x, y, gap=40, r=8, look=(0, 0), blink_period=3.7):
    """Two dot eyes with a white glint; they blink."""
    lx, ly = look
    e = "".join(f'<g><circle cx="{f(x+s*gap/2+lx)}" cy="{f(y+ly)}" r="{r}" fill="{INK}"/>'
                f'<circle cx="{f(x+s*gap/2+lx+r*.35)}" cy="{f(y+ly-r*.35)}" r="{r*.32:.1f}" fill="#fff"/></g>' for s in (-1, 1))
    return f'<g data-anim="blink" data-period="{blink_period}" style="transform-box:fill-box;transform-origin:center">{e}</g>'


def blush(x, y, gap=90, r=14):
    return "".join(f'<ellipse cx="{f(x+s*gap/2)}" cy="{y}" rx="{r}" ry="{r*.6:.0f}" fill="{P["blush"]}" opacity=".7"/>' for s in (-1, 1))


def scientist(x, y, s=1.0, pose="think", coat=None, hair=None, at=0.0):
    """Bust of a friendly scientist (glasses, lab coat, tie). (x, y) = bottom centre of the bust.
    pose: think (hand scratches head), point (arm raised, pointing up), wow (both hands up), calm."""
    coat = coat or "#e9ecef"
    hair = hair or "#7a4f35"
    g = f'<g transform="translate({x},{y}) scale({s})">'
    # body / coat
    g += f'<path d="{wobble_path([(-230,0),(-210,-200),(-120,-290),(120,-290),(210,-200),(230,0)], True, 3, 2)}" fill="{coat}" {_ink(3)}/>'
    g += f'<path d="M-60,-290 L0,-170 L60,-290" fill="#7fb7c3" {_ink(2.6)}/>'
    g += f'<path d="M-14,-262 L14,-262 L22,-170 L0,-140 L-22,-170 Z" fill="{P["red"]}" {_ink(2.4)}/>'
    g += f'<path d="M-60,-290 L-20,-120 M60,-290 L20,-120" fill="none" {_ink(2.4)}/>'
    g += f'<path d="M-150,-120 q20,30 50,0" fill="none" {_ink(2.4)}/>'
    # neck + head
    g += f'<rect x="-30" y="-330" width="60" height="50" fill="{P["skin"]}" {_ink(2.4)}/>'
    g += f'<path d="{blob_path(0,-430,110,118,7,12,.04)}" fill="{P["skin"]}" {_ink(3)}/>'
    g += f'<ellipse cx="-110" cy="-420" rx="16" ry="24" fill="{P["skin"]}" {_ink(2.4)}/><ellipse cx="110" cy="-420" rx="16" ry="24" fill="{P["skin"]}" {_ink(2.4)}/>'
    g += f'<path d="{wobble_path([(-112,-450),(-100,-520),(-40,-560),(30,-556),(96,-520),(114,-450),(70,-480),(20,-500),(-40,-488)], True, 11, 3)}" fill="{hair}" {_ink(2.6)}/>'
    # glasses + face
    g += f'<circle cx="-42" cy="-428" r="32" fill="#ffffff" fill-opacity=".25" {_ink(3)}/><circle cx="42" cy="-428" r="32" fill="#ffffff" fill-opacity=".25" {_ink(3)}/>'
    g += f'<line x1="-10" y1="-430" x2="10" y2="-430" {_ink(3)}/>'
    g += eyes(0, -428, gap=84, r=7)
    g += blush(0, -386, gap=150, r=16)
    mouth = {"think": "M-18,-360 q9,-8 18,0 q9,8 18,0", "wow": "M-14,-362 q14,22 28,0 q-14,-8 -28,0", "point": "M-20,-366 q20,18 40,0",
             "calm": "M-16,-364 q16,12 32,0"}.get(pose, "M-16,-364 q16,12 32,0")
    g += f'<path d="{mouth}" fill="{"#a8483a" if pose=="wow" else "none"}" {_ink(3)}/>'
    if pose == "think":
        g += f'<path d="M-70,-478 q14,-14 30,-8 M40,-486 q16,-6 30,8" fill="none" {_ink(3)}/>'
        arm = (f'<g data-anim="swing" data-pivot="150 -230" data-angle="6" data-period="0.5">'
               f'<path d="M150,-240 Q230,-300 200,-420 L150,-440 Q170,-320 120,-280 Z" fill="{coat}" {_ink(3)}/>'
               f'<circle cx="168" cy="-460" r="38" fill="{P["skin"]}" {_ink(3)}/></g>')
        g += arm
    elif pose == "point":
        g += (f'<g data-anim="pop" data-at="{at}"><path d="M150,-240 Q240,-330 250,-470 L200,-480 Q195,-340 120,-280 Z" fill="{coat}" {_ink(3)}/>'
              f'<circle cx="228" cy="-500" r="34" fill="{P["skin"]}" {_ink(3)}/><rect x="218" y="-580" width="18" height="60" rx="9" fill="{P["skin"]}" {_ink(2.6)}/></g>')
    elif pose == "wow":
        for sgn in (-1, 1):
            g += (f'<g data-anim="swing" data-pivot="{sgn*150} -230" data-angle="5" data-period=".35" data-phase="{(sgn+1)}">'
                  f'<path d="M{sgn*150},-240 Q{sgn*250},-330 {sgn*240},-470 L{sgn*190},-470 Q{sgn*190},-340 {sgn*120},-280 Z" fill="{coat}" {_ink(3)}/>'
                  f'<circle cx="{sgn*218}" cy="-492" r="34" fill="{P["skin"]}" {_ink(3)}/></g>')
    return f'<g data-anim="bob" data-period="3.2" data-amp=".5">{g}</g></g>'


def thought_bubble(x, y, w=380, h=230, at=0.0, inner="", tail=(-1, 1)):
    """Cloud-shaped thought bubble that pops in at `at`, with two small circles toward the thinker.
    `inner` is SVG drawn centred around (x, y)."""
    d = blob_path(x, y, w / 2, h / 2, 21, 14, .1)
    bumps = "".join(f'<circle cx="{f(x+math.cos(a)*w*.46)}" cy="{f(y+math.sin(a)*h*.44)}" r="{w*.13:.0f}" fill="{P["white"]}" {_ink(3)}/>'
                    for a in [i * math.pi / 5 for i in range(10)])
    tx, ty = tail
    tails = (f'<circle cx="{f(x+tx*w*.35)}" cy="{f(y+ty*h*.75)}" r="18" fill="{P["white"]}" {_ink(3)}/>'
             f'<circle cx="{f(x+tx*w*.45)}" cy="{f(y+ty*h*.98)}" r="10" fill="{P["white"]}" {_ink(3)}/>')
    body = bumps + f'<path d="{d}" fill="{P["white"]}"/>'
    return f'<g data-anim="pop" data-at="{at}">{tails}{body}{inner}</g>'


def question(x, y, size=120, color=None, at=None, seed=0):
    """Bobbing question mark (curious moments)."""
    color = color or P["orange"]
    a = f' data-at="{at}"' if at is not None else ""
    anim = "pop float" if at is not None else "float"
    return (f'<g data-anim="{anim}"{a} data-period="2.2" data-amp="1.2" data-phase="{seed}"><text x="{x}" y="{y}" text-anchor="middle" '
            f'font-family="Fredoka" font-weight="700" font-size="{size}" fill="{color}" stroke="{INK}" stroke-width="4" paint-order="stroke">?</text></g>')


def sparkle(x, y, s=24, color=None, phase=0):
    color = color or P["mustard"]
    d = f"M{x},{y-s} Q{x},{y} {x+s},{y} Q{x},{y} {x},{y+s} Q{x},{y} {x-s},{y} Q{x},{y} {x},{y-s}Z"
    return f'<path d="{d}" fill="{color}" {_ink(2)} data-anim="twinkle pulse" data-phase="{phase}"/>'


def heart(x, y, s=60, color=None, at=None, beat=True):
    """Heart icon; `beat` makes it pulse like a heartbeat."""
    color = color or P["red"]
    d = (f"M{x},{y+s*.9} C{x-s*1.4},{y} {x-s*.8},{y-s*.9} {x},{y-s*.35} C{x+s*.8},{y-s*.9} {x+s*1.4},{y} {x},{y+s*.9}Z")
    inner = f'<path d="{d}" fill="{color}" {_ink(3)}/><ellipse cx="{x-s*.45:.0f}" cy="{y-s*.25:.0f}" rx="{s*.18:.0f}" ry="{s*.12:.0f}" fill="#fff" opacity=".55"/>'
    if beat:
        inner = f'<g data-anim="pulse" data-period=".8" data-amp="2.5">{inner}</g>'
    if at is not None:
        return f'<g data-anim="pop" data-at="{at}">{inner}</g>'
    return inner


def callout(x, y, text, tx, ty, at=0.0, size=40, color=None):
    """Hand-drawn label: text at (tx, ty) with a curvy pointer line to (x, y)."""
    color = color or INK
    mx, my = (x + tx) / 2 + 30, (y + ty) / 2 - 30
    return (f'<g data-anim="fade" data-at="{at}" data-dur=".4">'
            f'<path d="M{tx},{ty+10} Q{mx:.0f},{my:.0f} {x},{y}" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/>'
            f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"/>'
            f'<text x="{tx}" y="{ty}" text-anchor="middle" font-family="Fredoka" font-weight="600" font-size="{size}" fill="{color}" '
            f'stroke="{P["white"]}" stroke-width="8" paint-order="stroke">{text}</text></g>')


def lens(x, y, r, content, ring=None, at=None):
    """Circular 'zoom-in' inset (cross-section, close-up): content clipped to a circle with a thick ring."""
    cid = _id("ln")
    ring = ring or "#f0dcc4"
    g = (f'<defs><clipPath id="{cid}"><circle cx="{x}" cy="{y}" r="{r}"/></clipPath></defs>'
         f'<circle cx="{x}" cy="{y}" r="{r+22}" fill="{ring}" {_ink(3)}/>'
         f'<g clip-path="url(#{cid})">{content}</g><circle cx="{x}" cy="{y}" r="{r}" fill="none" {_ink(3)}/>')
    return f'<g data-anim="pop" data-at="{at}">{g}</g>' if at is not None else g


def medal(x, y, r=110, label="", at=None):
    """Gold medal with ribbons and a label (awards, records)."""
    g = (f'<path d="M{x-60},{y-r-260} L{x-10},{y-r-260} L{x+20},{y-r+10} L{x-30},{y-r+10} Z" fill="#5c9a95" {_ink(3)}/>'
         f'<path d="M{x+60},{y-r-260} L{x+10},{y-r-260} L{x-20},{y-r+10} L{x+30},{y-r+10} Z" fill="#c9533c" {_ink(3)}/>'
         f'<circle cx="{x}" cy="{y}" r="{r}" fill="#e7b85a" {_ink(3.4)}/><circle cx="{x}" cy="{y}" r="{r*.72:.0f}" fill="#f1cd7a" {_ink(2.4)}/>'
         f'<text x="{x}" y="{y+r*.18:.0f}" text-anchor="middle" font-family="Fredoka" font-weight="700" font-size="{r*.55:.0f}" fill="{INK}">{label}</text>')
    return f'<g data-anim="pop" data-at="{at}">{g}</g>' if at is not None else g


def sunburst(x, y, r=600, color="#f6dc9a", n=18, spin=True):
    """Soft radial rays behind a reveal (awards, 'aha' moments)."""
    rays = ""
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n
        rays += f'<path d="M{x},{y} L{f(x+math.cos(a0)*r)},{f(y+math.sin(a0)*r)} L{f(x+math.cos(a1)*r)},{f(y+math.sin(a1)*r)} Z" fill="{color}" opacity=".55"/>'
    return f'<g data-anim="spin" data-period="40">{rays}</g>' if spin else rays


def label_hand(x, y, text, size=44, color=None, at=None, anchor="middle"):
    color = color or INK
    a = f' data-anim="fade" data-at="{at}"' if at is not None else ""
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Fredoka" font-weight="600" font-size="{size}" fill="{color}" '
            f'stroke="{P["white"]}" stroke-width="7" paint-order="stroke"{a}>{text}</text>')
