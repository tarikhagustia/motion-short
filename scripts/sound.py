#!/usr/bin/env python3
"""Synthesize the sound effects and the music bed for a motion-shorts project (no API needed).

Usage:
    python sound.py PROJECT_DIR              # audio/sfx.wav + audio/music.wav
    python sound.py PROJECT_DIR --no-music   # effects only
    python sound.py PROJECT_DIR --music-only

Reads storyboard.json (scene `sfx` cues, top-level `style` and optional `music`) and timeline.json
(scene starts and word times, so `word:` cues land on the spoken word). Everything is generated
procedurally with numpy/scipy and is deterministic, so re-running gives the same mix.

Cue kinds (one-shots): whoosh, swoosh, pop, tick, ticks, chime, shimmer, sparkle, impact, thud, boom,
rumble, scribble, paper, page, bubbles, beep, blip, data, glitch, scan, alarm, heartbeat, thunder, scream, screams, gong,
pluck, splash, click, rise, drop.
Recordings: `{"kind": "file", "src": "audio/sfx_src/x.mp3", "word": ..., "volume": .5, "lp": 2500, "dur": 2}`
(path relative to the project; `lp` makes it sound far away).
Ambience kinds (`"ambience": true`): wind, ocean, underwater, jungle, night, hum, room, crowd, rain, fire, space.

Music presets (storyboard `music`, default from the style): emas (gamelan-like pentatonic plucks over a
warm drone), buku (soft music-box / marimba waltz), hud (dark synth pulse with arps), lukis (dark minor
pad over a drone), none.

Scary mode (storyboard `paint.scary: true`, lukis style): adds a rising sub drone + wind, a heartbeat
every 0.92 s, boom + impact + fire on every `paint.blast_words` blast and thunder on every
`paint.lightning` extra flash. `paint_times()` is shared with render (style.js) and hyperframes.py.
"""
import argparse
import json
import math
import re
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
STYLE_MUSIC = {"emas": "emas", "buku": "buku", "hud": "hud", "lukis": "lukis", "bedah": "bedah"}


# ---------------------------------------------------------------- dsp helpers
def rng_for(*keys):
    h = 0
    for k in keys:
        for ch in str(k):
            h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return np.random.default_rng(h)


def t_axis(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=2):
    lo, hi = max(lo, 20), min(hi, SR / 2 - 100)
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, min(f, SR / 2 - 100), btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, max(f, 20), btype="high", fs=SR, output="sos"), x)


def env_ad(n, a, d_curve=4.0):
    """attack fraction a, exponential decay"""
    t = np.linspace(0, 1, n)
    e = np.where(t < a, t / max(a, 1e-6), np.exp(-d_curve * (t - a) / max(1 - a, 1e-6)))
    return e


def fade(x, fi=0.01, fo=0.05):
    n = len(x)
    a, b = int(fi * SR), int(fo * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def sine(f, d, phase=0):
    t = t_axis(d)
    if callable(f):
        ph = 2 * np.pi * np.cumsum(f(t)) / SR
    else:
        ph = 2 * np.pi * f * t
    return np.sin(ph + phase)


def noise(d, r):
    return r.standard_normal(int(d * SR))


# ---------------------------------------------------------------- one-shots
def s_whoosh(d, r, hi=False):
    d = d or 0.7
    n = noise(d, r)
    t = np.linspace(0, 1, len(n))
    k = 1.6 if hi else 1.0
    low = bp(n, 300 * k, 1200 * k)
    high = bp(n, 1500 * k, 6000 * k)
    mix = np.sin(np.pi * t) ** 1.5  # sweep up then down
    out = low * (1 - mix) + high * mix * 0.8
    e = np.sin(np.pi * t) ** 2.2
    return norm(out * e, 0.8)


def s_pop(d, r):
    d = d or 0.16
    f = lambda t: 900 * np.exp(-t * 28) + 260
    return sine(f, d) * env_ad(int(d * SR), 0.02, 9) * 0.9


def s_click(d, r):
    d = 0.03
    return hp(noise(d, r), 2000) * env_ad(int(d * SR), 0.01, 12) * 0.7


def s_tick(d, r):
    d = 0.05
    return (sine(2600, d) * 0.5 + hp(noise(d, r), 3000) * 0.5) * env_ad(int(d * SR), 0.01, 14)


def s_ticks(d, r):
    d = d or 1.2
    out = np.zeros(int(d * SR))
    step = 0.085
    i = 0
    while i * step < d - 0.05:
        tk = s_tick(0, r) * (0.7 + 0.3 * (i % 2))
        a = int(i * step * SR)
        out[a:a + len(tk)] += tk[: len(out) - a]
        i += 1
    return out


def s_chime(d, r, notes=(1318.5, 1760, 1975.5, 2637)):
    d = d or 2.2
    out = np.zeros(int(d * SR))
    for i, f in enumerate(notes):
        a = int(i * 0.07 * SR)
        seg = d - i * 0.07
        tone = (sine(f, seg) + 0.3 * sine(f * 2.01, seg) + 0.15 * sine(f * 3.98, seg)) * env_ad(int(seg * SR), 0.005, 5)
        out[a:a + len(tone)] += tone * 0.35
    return out


def s_shimmer(d, r):
    d = d or 2.0
    out = np.zeros(int(d * SR))
    for i in range(14):
        f = r.choice([1568, 1760, 2093, 2349, 2637, 3136, 3520])
        a = int(r.uniform(0, d * 0.6) * SR)
        seg = 0.9
        tone = sine(f, seg) * env_ad(int(seg * SR), 0.01, 6) * 0.16
        out[a:a + len(tone)] += tone[: len(out) - a]
    sw = bp(noise(d, r), 5000, 12000) * np.sin(np.linspace(0, np.pi, int(d * SR))) * 0.08
    return out + sw


def s_impact(d, r):
    d = d or 1.2
    body = sine(lambda t: 90 * np.exp(-t * 3) + 38, d) * env_ad(int(d * SR), 0.003, 6)
    crack = lp(noise(d, r), 2500) * env_ad(int(d * SR), 0.001, 22) * 0.6
    return (body + crack) * 0.9


def s_boom(d, r):
    d = d or 2.6
    body = sine(lambda t: 60 * np.exp(-t * 1.2) + 28, d) * env_ad(int(d * SR), 0.004, 3.5)
    rum = lp(noise(d, r), 300, 4) * env_ad(int(d * SR), 0.01, 3) * 2.5
    return norm(body + rum, 0.95)


def s_rumble(d, r):
    d = d or 2.5
    x = lp(noise(d, r), 160, 4) * 4
    t = np.linspace(0, 1, len(x))
    return norm(x * np.sin(np.pi * t) ** 0.6, 0.8)


def s_scribble(d, r):
    d = d or 1.2
    x = bp(noise(d, r), 1800, 6000)
    t = t_axis(d)
    m = (0.5 + 0.5 * np.sin(2 * np.pi * 7.5 * t + r.uniform(0, 6))) ** 2
    return x * m * 0.35


def s_paper(d, r):
    d = d or 0.5
    x = bp(noise(d, r), 1200, 9000)
    return x * env_ad(len(x), 0.15, 4) * 0.5


def s_page(d, r):
    d = d or 0.8
    x = bp(noise(d, r), 600, 7000)
    t = np.linspace(0, 1, len(x))
    return x * (np.sin(np.pi * t) ** 1.5) * (0.6 + 0.4 * np.sin(t * 40)) * 0.55


def s_bubbles(d, r):
    d = d or 1.4
    out = np.zeros(int(d * SR))
    for _ in range(int(d * 9)):
        f0 = r.uniform(400, 1100)
        seg = r.uniform(0.04, 0.09)
        b = sine(lambda t: f0 + 4000 * t, seg) * env_ad(int(seg * SR), 0.1, 5) * 0.4
        a = int(r.uniform(0, d - seg) * SR)
        out[a:a + len(b)] += b
    return out


def s_beep(d, r, f=1320):
    d = d or 0.12
    x = np.sign(sine(f, d)) * 0.25 + sine(f, d) * 0.4
    return lp(x, 6000) * env_ad(int(d * SR), 0.02, 3) * 0.6


def s_blip(d, r):
    d = d or 0.09
    return sine(lambda t: 1800 + 6000 * t, d) * env_ad(int(d * SR), 0.05, 6) * 0.5


def s_data(d, r):
    d = d or 0.8
    out = np.zeros(int(d * SR))
    t, i = 0.0, 0
    while t < d - 0.05:
        seg = r.uniform(0.02, 0.05)
        f = r.choice([880, 1320, 1760, 2200, 2640])
        b = s_beep(seg, r, f) * 0.6
        a = int(t * SR)
        out[a:a + len(b)] += b[: len(out) - a]
        t += seg + r.uniform(0.01, 0.04)
        i += 1
    return out


def s_glitch(d, r):
    d = d or 0.35
    x = noise(d, r)
    gate = np.repeat(r.random(int(d * 60) + 1) > 0.45, SR // 60 + 1)[: len(x)]
    return bp(x, 300, 8000) * gate * 0.45 + np.sign(sine(110, d)) * gate * 0.1


def s_scan(d, r):
    d = d or 1.0
    return sine(lambda t: 300 + 2400 * (t / d), d) * 0.25 * np.sin(np.linspace(0, np.pi, int(d * SR)))


def s_alarm(d, r):
    d = d or 1.2
    t = t_axis(d)
    f = np.where((t * 4) % 1 < 0.5, 880, 660)
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.15


def s_heartbeat(d, r):
    d = d or 1.6
    out = np.zeros(int(d * SR))
    k = 0
    while k * 0.85 < d - 0.4:
        for off, g in ((0, 1.0), (0.22, 0.7)):
            th = sine(lambda t: 70 * np.exp(-t * 8) + 40, 0.25) * env_ad(int(0.25 * SR), 0.02, 9) * g
            a = int((k * 0.85 + off) * SR)
            out[a:a + len(th)] += th[: len(out) - a]
        k += 1
    return out


def s_thunder(d, r):
    """Close lightning: sharp crack, then rolling low rumble."""
    d = d or 3.2
    n = int(d * SR)
    crack = hp(noise(0.25, r), 1500) * env_ad(int(0.25 * SR), 0.002, 18) * 1.2
    roll = lp(noise(d, r), 260, 4) * 4
    t = np.linspace(0, 1, n)
    roll *= (np.exp(-t * 2.2) * (0.7 + 0.3 * np.sin(2 * np.pi * 3.1 * t * d)))
    out = norm(roll, 0.85)
    out[: len(crack)] += crack
    return out


def s_scream(dur, r, f0=None, vowel=None):
    """One panicked human scream: glottal pulse train with a rise-fall pitch contour, vibrato and
    jitter, shaped by vowel formants, with breath noise."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f0 = f0 or r.uniform(320, 1050)
    contour = f0 * (1 + r.uniform(.15, .4) * np.sin(np.pi * np.clip(tt / dur * 1.2, 0, 1))) * (1 - r.uniform(.05, .25) * tt / dur)
    jit = np.cumsum(r.standard_normal(n)) / np.sqrt(SR) * 0.02
    f = contour * (1 + .03 * np.sin(2 * np.pi * r.uniform(5, 8) * tt) + jit)
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = np.zeros(n)
    for h in range(1, 16):
        if h * f0 > 9000:
            break
        src += np.sin(h * ph) / h ** 0.9
    src = src * (1 + .6 * np.abs(r.standard_normal(n)) * .15) + r.standard_normal(n) * .35   # rough, breathy
    vowel = vowel or ([(850, 1250, 2800), (700, 1150, 2700), (500, 1900, 2700), (400, 2200, 3000)][r.integers(0, 4)])
    out = sum(bp(src, F * .88, F * 1.12) * g for F, g in zip(vowel, (1.0, .7, .45)))
    env = np.minimum(1, tt / r.uniform(.02, .08)) * np.clip((dur - tt) / r.uniform(.15, .4), 0, 1)
    return norm(out * env, 0.9)


def s_screams(d, r):
    """A crowd screaming in panic: many voices, near and far, overlapping."""
    d = d or 4.0
    out = np.zeros(int(d * SR))
    for k in range(int(6 + d * 3)):
        dur = r.uniform(.45, 1.6)
        a = int(r.uniform(0, max(d - dur, .01)) * SR)
        near = r.uniform(.25, 1.0) ** 1.5
        x = s_scream(dur, r)
        x = lp(x, 1800 + near * 6000) * near                         # far voices duller and quieter
        out[a:a + len(x)] += x[: len(out) - a]
    out += bp(noise(d, r), 300, 2500) * .05                             # running, shuffling crowd bed
    return norm(fade(out, .05, .4), 0.9)


def s_gong(d, r):
    d = d or 3.5
    base = 196
    out = np.zeros(int(d * SR))
    for ratio, g, dec in ((1, 1, 1.4), (1.48, .5, 2), (2.0, .35, 2.4), (2.76, .25, 3), (4.1, .12, 4)):
        tone = sine(base * ratio, d) * env_ad(int(d * SR), 0.004, dec * 1.8) * g
        out += tone
    # wobble
    t = t_axis(d)
    return out * (1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)) * 0.45


def s_pluck(d, r, f=392):
    d = d or 1.4
    x = (sine(f, d) + 0.5 * sine(f * 2, d) + 0.25 * sine(f * 3.01, d)) * env_ad(int(d * SR), 0.003, 5)
    return x * 0.4


def s_splash(d, r):
    d = d or 0.9
    return bp(noise(d, r), 400, 9000) * env_ad(int(d * SR), 0.02, 5) * 0.6


def s_rise(d, r):
    d = d or 1.5
    t = np.linspace(0, 1, int(d * SR))
    x = sine(lambda tt: 200 + 900 * (tt / d) ** 2, d) * 0.2 + bp(noise(d, r), 2000, 9000) * 0.12
    return x * t ** 1.5


def s_drop(d, r):
    d = d or 0.7
    return sine(lambda t: 900 * np.exp(-t * 6) + 80, d) * env_ad(int(d * SR), 0.01, 4) * 0.5


# --- mechanical foley (bedah): the object's own sounds, loud and close
def s_klik(d, r):
    """Latch / switch snapping: sharp plastic transient + short body thunk (magic com, saklar, MCB)."""
    d = d or 0.35
    n = int(d * SR)
    snap = hp(noise(0.012, r), 1800) * env_ad(int(0.012 * SR), 0.05, 6)
    body = (sine(lambda t: 420 * np.exp(-t * 30) + 140, d) * 0.8 + bp(noise(d, r), 300, 1600) * 0.4) * env_ad(n, 0.005, 16)
    out = body.copy()
    out[: len(snap)] += snap * 1.4
    b = int(0.045 * SR)  # second, smaller click of the mechanism settling
    out[b:b + len(snap)] += snap[: n - b] * 0.5
    return norm(out, 0.9)


def s_hiss(d, r):
    """Steam / air escaping (presto valve, tyre, spray): bright noise with a fast attack and flutter."""
    d = d or 1.2
    t = t_axis(d)
    x = bp(noise(d, r), 2500, 11000) * (1 + 0.25 * np.sin(2 * np.pi * 23 * t) * np.sin(2 * np.pi * 3 * t))
    e = np.minimum(t / 0.04, 1) * np.exp(-np.maximum(t - d * 0.55, 0) * 6)
    return norm(x * e, 0.75)


def s_rev(d, r):
    """Small engine revving up (motor, blender, drill): rising harmonic buzz."""
    d = d or 1.6
    t = t_axis(d)
    f = lambda tt: 38 + 95 * (1 - np.exp(-tt * 2.2))
    saw = np.zeros(len(t))
    ph = 2 * np.pi * np.cumsum(f(t)) / SR
    for k in range(1, 9):
        saw += np.sin(ph * k) / k
    x = lp(saw, 1800) + bp(noise(d, r), 200, 1200) * 0.15
    e = np.minimum(t / 0.08, 1) * np.minimum((d - t) / 0.25, 1)
    return norm(x * e, 0.7)


def s_relay(d, r):
    """Relay / solenoid clack: metallic double knock."""
    d = d or 0.25
    out = np.zeros(int(d * SR))
    for k, (at, v) in enumerate(((0, 1.0), (0.018, 0.55))):
        g = bp(noise(0.05, r), 900 + 900 * k, 5000) * env_ad(int(0.05 * SR), 0.02, 9) * v
        g += sine(1850 + 400 * k, 0.05) * env_ad(int(0.05 * SR), 0.01, 12) * 0.3 * v
        a = int(at * SR)
        out[a:a + len(g)] += g[: len(out) - a]
    return norm(out, 0.8)


def s_beep3(d, r):
    """Device warning beeps: three short square-ish beeps (token meter, microwave)."""
    d = d or 0.75
    out = np.zeros(int(d * SR))
    for k in range(3):
        b = np.sign(sine(2900, 0.11)) * 0.35 * env_ad(int(0.11 * SR), 0.03, 2)
        a = int(k * 0.2 * SR)
        out[a:a + len(b)] += lp(b, 7000)[: len(out) - a]
    return out


def s_boil(d, r):
    """Water boiling / simmering: many small bubble pops over a low rumble."""
    d = d or 2.0
    out = lp(noise(d, r), 300) * 0.25
    for _ in range(int(d * 40)):
        f0 = r.uniform(300, 900)
        b = sine(lambda tt: f0 * (1 + tt * 6), 0.04) * env_ad(int(0.04 * SR), 0.05, 6) * r.uniform(0.1, 0.35)
        a = int(r.uniform(0, d - 0.05) * SR)
        out[a:a + len(b)] += b
    return norm(out, 0.6)


ONESHOT = {
    "whoosh": s_whoosh, "swoosh": lambda d, r: s_whoosh(d or 0.45, r, hi=True), "pop": s_pop, "click": s_click,
    "tick": s_tick, "ticks": s_ticks, "chime": s_chime, "shimmer": s_shimmer, "sparkle": s_shimmer,
    "impact": s_impact, "thud": s_impact, "crash": s_impact, "boom": s_boom, "explosion": s_boom,
    "rumble": s_rumble, "scribble": s_scribble, "paper": s_paper, "page": s_page, "bubbles": s_bubbles,
    "klik": s_klik, "latch": s_klik, "hiss": s_hiss, "steam": s_hiss, "rev": s_rev, "relay": s_relay,
    "beep3": s_beep3, "boil": s_boil,
    "beep": s_beep, "blip": s_blip, "data": s_data, "glitch": s_glitch, "scan": s_scan, "alarm": s_alarm,
    "heartbeat": s_heartbeat, "thunder": s_thunder, "scream": lambda d, r: s_scream(d or 1.2, r), "screams": s_screams, "gong": s_gong, "pluck": s_pluck, "splash": s_splash, "rise": s_rise, "drop": s_drop,
}


# ---------------------------------------------------------------- ambience beds
def a_wind(d, r):
    x = lp(noise(d, r), 700, 2)
    t = t_axis(d)
    m = 0.55 + 0.45 * np.sin(2 * np.pi * 0.13 * t + 1) * np.sin(2 * np.pi * 0.07 * t)
    return norm(x * m, 0.5)


def a_ocean(d, r):
    x = lp(noise(d, r), 1200, 2)
    t = t_axis(d)
    m = 0.3 + 0.7 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 6.5)) ** 2
    return norm(x * m, 0.5)


def a_underwater(d, r):
    x = lp(noise(d, r), 260, 4)
    return norm(x, 0.55) + s_bubbles(d, r) * 0.25


def a_jungle(d, r):
    base = bp(noise(d, r), 3500, 7000) * 0.12
    t = t_axis(d)
    base *= 0.6 + 0.4 * (np.sin(2 * np.pi * 9 * t) > 0)
    out = base
    for _ in range(int(d * 1.2)):
        seg = 0.25
        f0 = r.uniform(2200, 4200)
        ch = sine(lambda tt: f0 + 900 * np.sin(2 * np.pi * 14 * tt), seg) * env_ad(int(seg * SR), 0.1, 3) * 0.2
        a = int(r.uniform(0, max(d - seg, 0.01)) * SR)
        out[a:a + len(ch)] += ch[: len(out) - a]
    return norm(out, 0.5)


def a_night(d, r):
    t = t_axis(d)
    cr = sine(4400, d) * (np.sin(2 * np.pi * 28 * t) > 0.6) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.6 * t)) * 0.15
    return cr + lp(noise(d, r), 400) * 0.08


def a_hum(d, r):
    t = t_axis(d)
    x = sine(55, d) * 0.5 + sine(110, d) * 0.25 + sine(165, d) * 0.1 + lp(noise(d, r), 900) * 0.08
    return x * (0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * t))


def a_room(d, r):
    return lp(noise(d, r), 500, 2) * 0.25


def a_crowd(d, r):
    x = bp(noise(d, r), 250, 2200)
    t = t_axis(d)
    return norm(x * (0.7 + 0.3 * np.sin(2 * np.pi * 0.4 * t)), 0.4)


def a_rain(d, r):
    return norm(hp(noise(d, r), 1500), 0.35)


def a_fire(d, r):
    x = lp(noise(d, r), 900) * 0.4
    for _ in range(int(d * 14)):
        a = int(r.uniform(0, d - 0.03) * SR)
        c = s_click(0, r) * r.uniform(0.2, 0.7)
        x[a:a + len(c)] += c
    return norm(x, 0.5)


def a_space(d, r):
    t = t_axis(d)
    x = sine(41.2, d) * 0.4 + sine(61.7, d) * 0.25 + lp(noise(d, r), 200) * 0.15
    return x * (0.8 + 0.2 * np.sin(2 * np.pi * 0.11 * t))


AMBIENCE = {"wind": a_wind, "ocean": a_ocean, "underwater": a_underwater, "jungle": a_jungle, "night": a_night,
            "hum": a_hum, "room": a_room, "crowd": a_crowd, "rain": a_rain, "fire": a_fire, "space": a_space,
            "birds": a_jungle, "forest": a_jungle}


# ---------------------------------------------------------------- music beds
def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def mallet(f, d, bright=1.0):
    x = sine(f, d) + 0.35 * bright * sine(f * 4.0, d) * env_ad(int(d * SR), 0.002, 14) + 0.15 * sine(f * 2, d)
    return x * env_ad(int(d * SR), 0.004, 6)


def m_emas(dur, r):
    """Gamelan-flavoured: pelog-ish pentatonic, slow saron line, bonang answer, drone + soft gong every 8 bars."""
    out = np.zeros(int(dur * SR) + SR)
    scale = [62, 63, 65, 69, 70, 74, 75, 77]  # D Eb F A Bb (pelog-like)
    beat = 0.5
    drone = (sine(midi(38), dur + 1) * 0.35 + sine(midi(45), dur + 1) * 0.2) * 0.35
    drone = lp(drone, 600)
    out[:len(drone)] += drone
    pattern = [0, 2, 1, 3, 2, 4, 3, 1]
    i = 0
    t = 0.0
    while t < dur:
        n = scale[pattern[i % 8] + (2 if (i // 16) % 2 else 0)]
        tone = mallet(midi(n), 1.6, 0.9) * 0.22
        a = int(t * SR)
        out[a:a + len(tone)] += tone[: len(out) - a]
        if i % 2 == 1:  # bonang answer an octave up, softer
            tone2 = mallet(midi(n + 12), 0.8, 1.2) * 0.09
            out[a:a + len(tone2)] += tone2[: len(out) - a]
        if i % 32 == 0:
            g = s_gong(4.0, r) * 0.5
            out[a:a + len(g)] += g[: len(out) - a]
        t += beat
        i += 1
    return out[: int(dur * SR)]


def m_buku(dur, r):
    """Warm music-box waltz in C major with soft pad."""
    out = np.zeros(int(dur * SR) + SR)
    chords = [(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)]
    mel = [76, 74, 72, 74, 76, 76, 79, 77, 76, 74, 72, 71]
    beat = 0.42
    t, i = 0.0, 0
    while t < dur:
        ch = chords[(i // 6) % 4]
        if i % 3 == 0:  # bass + pad on beat 1
            b = mallet(midi(ch[0] - 12), 2.4, 0.3) * 0.2
            a = int(t * SR)
            out[a:a + len(b)] += b[: len(out) - a]
        else:
            for n in ch[1:]:
                b = mallet(midi(n), 0.9, 0.4) * 0.06
                a = int(t * SR)
                out[a:a + len(b)] += b[: len(out) - a]
        n = mel[i % len(mel)]
        if (i % 6) != 5:
            box = (sine(midi(n), 1.2) + 0.4 * sine(midi(n) * 3, 1.2)) * env_ad(int(1.2 * SR), 0.003, 7) * 0.11
            a = int(t * SR)
            out[a:a + len(box)] += box[: len(out) - a]
        t += beat
        i += 1
    return lp(out[: int(dur * SR)], 7000)


def m_hud(dur, r):
    """Dark synth: sub drone, pulsing filtered bass on 8ths, sparse arp, soft hats."""
    out = np.zeros(int(dur * SR) + SR)
    T = t_axis(dur + 1)
    root = midi(33)
    sub = sine(root, dur + 1) * 0.25 + sine(root * 1.5, dur + 1) * 0.08
    out += lp(sub, 200)
    step = 60 / 100 / 2  # 100 bpm, 8ths
    seq = [0, 0, 12, 0, 7, 0, 10, 3]
    arp = [57, 60, 64, 67, 64, 60]
    t, i = 0.0, 0
    while t < dur:
        f = midi(45 + seq[i % 8] - 12)
        saw = 2 * ((np.arange(int(step * SR)) * f / SR) % 1) - 1
        b = lp(saw, 420 + 300 * (i % 4 == 0)) * env_ad(len(saw), 0.01, 3) * 0.16
        a = int(t * SR)
        out[a:a + len(b)] += b[: len(out) - a]
        if i % 2 == 0:
            h = hp(noise(0.04, r), 7000) * env_ad(int(0.04 * SR), 0.01, 10) * 0.05
            out[a:a + len(h)] += h[: len(out) - a]
        if i % 3 == 0 and (i // 16) % 2 == 1:
            n = arp[(i // 3) % len(arp)] + 12
            p = sine(midi(n), 0.5) * env_ad(int(0.5 * SR), 0.005, 6) * 0.07
            out[a:a + len(p)] += p[: len(out) - a]
        t += step
        i += 1
    return out[: int(dur * SR)]


def m_lukis(dur, r):
    """Dark cinematic pad: slow minor chords (detuned saws, low-passed) with a swelling low drone."""
    out = np.zeros(int(dur * SR) + SR)
    chords = [(45, 52, 57, 60), (41, 48, 53, 57), (43, 50, 55, 59), (40, 47, 52, 55)]
    bar = 4.0
    t, i = 0.0, 0
    while t < dur:
        seg = bar + 1.5
        x = np.zeros(int(seg * SR))
        for n in chords[i % 4]:
            f = midi(n)
            for det in (-0.12, 0.12):
                ph = np.arange(len(x)) * f * (1 + det / 100) / SR
                x += (2 * (ph % 1) - 1) * 0.05
        x = lp(x, 900, 2)
        e = np.minimum(np.linspace(0, 1, len(x)) / 0.35, 1) * np.minimum(np.linspace(1, 0, len(x)) / 0.3, 1)
        x *= e
        a = int(t * SR)
        out[a:a + len(x)] += x[: len(out) - a]
        t += bar
        i += 1
    drone = lp(sine(midi(33), dur + 1) * 0.3 + noise(dur + 1, r) * 0.03, 180)
    out[: len(drone)] += drone[: len(out)]
    return out[: int(dur * SR)]


def m_bedah(dur, r):
    """Light 'workshop' lo-fi: soft electric-piano 7th chords, round bass, brushed kick/rim, 92 bpm.
    Sits low and steady under a fast narrator; the object's own foley carries the accents."""
    out = np.zeros(int(dur * SR) + SR)
    beat = 60 / 92
    chords = [(57, 60, 64, 67), (53, 57, 60, 64), (55, 59, 62, 65), (52, 55, 59, 62)]  # Am7 Fmaj7 G7 Em7
    def ep(f, d):  # electric piano: sine + soft bell partial, slow decay, tremolo
        tt = t_axis(d)
        x = sine(f, d) + 0.22 * sine(f * 2, d) + 0.08 * sine(f * 7.1, d) * env_ad(int(d * SR), 0.002, 18)
        return x * env_ad(int(d * SR), 0.01, 3.2) * (1 + 0.12 * np.sin(2 * np.pi * 4.2 * tt))
    t, i = 0.0, 0
    while t < dur:
        a = int(t * SR)
        bar, b4 = i // 4, i % 4
        ch = chords[bar % 4]
        if b4 == 0:
            for n in ch:
                x = ep(midi(n), beat * 4) * 0.055
                out[a:a + len(x)] += x[: len(out) - a]
        if b4 in (0, 2):  # bass
            n = ch[0] - 12 - (0 if b4 == 0 else -7)
            x = sine(midi(n), beat * 1.6) * env_ad(int(beat * 1.6 * SR), 0.02, 4) * 0.16
            out[a:a + len(x)] += x[: len(out) - a]
            k = sine(lambda tt: 110 * np.exp(-tt * 30) + 48, 0.25) * env_ad(int(0.25 * SR), 0.01, 7) * 0.22
            out[a:a + len(k)] += k[: len(out) - a]
        else:  # rim / brush
            h = bp(noise(0.06, r), 1800, 6000) * env_ad(int(0.06 * SR), 0.01, 9) * 0.05
            out[a:a + len(h)] += h[: len(out) - a]
        # off-beat shaker
        o = int((t + beat / 2) * SR)
        sh = hp(noise(0.03, r), 6000) * env_ad(int(0.03 * SR), 0.2, 5) * 0.025
        out[o:o + len(sh)] += sh[: max(len(out) - o, 0)]
        t += beat
        i += 1
    return lp(out[: int(dur * SR)], 9000)


MUSIC = {"emas": m_emas, "buku": m_buku, "hud": m_hud, "lukis": m_lukis, "bedah": m_bedah}


# ---------------------------------------------------------------- mixing
def write_wav(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], axis=1) if x.ndim == 1 else x
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def norm_word(w):
    return re.sub(r"[^\w±%]", "", w.lower())


def cue_time(cue, si, tl):
    sc = tl["scenes"][si]
    if "word" in cue:
        want = norm_word(cue["word"])
        for w in tl["words"]:
            if w["scene"] == si and norm_word(w["text"]).startswith(want):
                return w["start"] + cue.get("offset", 0)
        print(f"  ! word '{cue['word']}' not found in scene {sc['id']}, using scene start")
    return sc["start"] + cue.get("at", 0) + cue.get("offset", 0)


def load_file(path, dur=None):
    """Decode any audio file (mp3/wav/...) to mono float at SR with ffmpeg."""
    import subprocess
    cmd = ["ffmpeg", "-v", "error", "-i", str(path)] + (["-t", str(dur)] if dur else []) + ["-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def build_sfx(sb, tl, proj=None):
    dur = tl["duration"]
    out = np.zeros(int((dur + 4) * SR))
    for si, sc in enumerate(sb["scenes"]):
        s0, s1 = tl["scenes"][si]["start"], tl["scenes"][si]["end"]
        for k, cue in enumerate(sc.get("sfx", [])):
            kind = cue.get("kind", "whoosh")
            r = rng_for(sc["id"], k, kind)
            vol = cue.get("volume", 0.25 if cue.get("ambience") else 0.6)
            if kind == "file":                        # a real recording: {"kind": "file", "src": "audio/sfx_src/x.mp3", "lp": 2500}
                src = Path(cue["src"]) if Path(cue["src"]).is_absolute() else Path(proj or ".") / cue["src"]
                if not src.exists():
                    print(f"  ! sfx file not found: {src}")
                    continue
                x = load_file(src, cue.get("dur"))
                if cue.get("lp"):
                    x = lp(x, cue["lp"], 4)          # far away: duller
                x = fade(x, 0.005, cue.get("fade_out", 0.15)) * vol
                a = int(max(cue_time(cue, si, tl), 0) * SR)
            elif cue.get("ambience"):
                fn = AMBIENCE.get(kind, a_room)
                a0, a1 = max(s0 - 0.3, 0), s1 + 0.4
                x = fade(fn(a1 - a0, r), 0.4, 0.5) * vol
                a = int(a0 * SR)
            else:
                fn = ONESHOT.get(kind)
                if not fn:
                    print(f"  ! unknown sfx kind '{kind}' in {sc['id']}, using whoosh")
                    fn = s_whoosh
                x = fade(np.asarray(fn(cue.get("dur"), r), dtype=np.float64), 0.002, 0.03) * vol
                a = int(max(cue_time(cue, si, tl), 0) * SR)
            out[a:a + len(x)] += x[: len(out) - a]
        # automatic soft whoosh on scene changes
        if si > 0 and sc.get("transition", "fade") != "cut" and sb.get("auto_whoosh", True):
            x = s_whoosh(0.6, rng_for(sc["id"], "auto")) * 0.18
            a = int(max(s0 - 0.35, 0) * SR)
            out[a:a + len(x)] += x[: len(out) - a]
    return out[: int(dur * SR)]


def word_at(tl, sid, w):
    si = next((i for i, s in enumerate(tl["scenes"]) if s["id"] == sid), None)
    for x in tl["words"]:
        if si is not None and x["scene"] == si and norm_word(x["text"]).startswith(norm_word(w)):
            return x["start"]
    return None


def paint_times(sb, tl):
    """Resolve the lukis painter's event times: lightning flashes (flash_words + extra `lightning`
    seconds) and big blasts (blast_words). Returns (flashes, blasts, extra_lightning), all sorted."""
    p = sb.get("paint", {})
    def words(key):
        out = []
        for s, w, *o in p.get(key, []):
            t = word_at(tl, s, w)
            if t is None:
                print(f"  ! paint {key}: word '{w}' not found in {s}")
            else:
                out.append(round(t + (o[0] if o else 0), 3))
        return out
    extra = sorted(p.get("lightning", []))
    flashes = sorted(words("flash_words") + p.get("flashes", []) + extra)
    return flashes, sorted(words("blast_words")), extra


def paint_config(sb, tl):
    """The fully resolved painter config for the page (render.py and hyperframes.py pass it as is).
    Word lists become seconds. If any scene has its own `paint`, the result is a `sequence`: a scene
    with `paint` starts a segment, scenes without one continue it. Inside a segment, `<key>_word`
    options ([sid, word, offset]) become `<key>` in seconds local to the segment start; `waves_word`
    becomes a list `waves`."""
    p = dict(sb.get("paint", {}))
    flashes, blasts, _ = paint_times(sb, tl)
    for k in ("flash_words", "blast_words", "lightning", "flashes"):
        p.pop(k, None)
    out = {**p, "flashes": flashes, "blasts": blasts, "duration": tl["duration"]}
    if not any(sc.get("paint") for sc in sb["scenes"]):
        out.setdefault("scene", "volcano")
        return out
    segs = []
    for si, sc in enumerate(sb["scenes"]):
        if not sc.get("paint") and segs:
            continue
        s0 = tl["scenes"][si]["start"]
        seg = {"start": s0, "cut": sc.get("transition") == "cut" and si > 0}
        for k, v in (sc.get("paint") or {"scene": p.get("scene", "volcano")}).items():
            if k.endswith("_word"):
                t = word_at(tl, v[0], v[1])
                if t is None:
                    print(f"  ! paint {sc['id']}.{k}: word '{v[1]}' not found in {v[0]}")
                    continue
                t = round(t + (v[2] if len(v) > 2 else 0) - s0, 3)
                key = k[:-5]
                seg[key] = [t] if key == "waves" else t
            else:
                seg[k] = v
        segs.append(seg)
    for a, b in zip(segs, segs[1:] + [None]):
        a["end"] = b["start"] if b else tl["duration"]
    out.update({"scene": "sequence", "segments": segs})
    return out


def build_scary(sb, tl):
    """Dread layer for paint.scary: rising sub drone, wind, heartbeat, booms on blasts, thunder on lightning."""
    dur = tl["duration"]
    out = np.zeros(int((dur + 4) * SR))
    def put(x, t, v):
        a = int(max(t, 0) * SR); out[a:a + len(x)] += x[: len(out) - a] * v
    r = rng_for("scary")
    tt = t_axis(dur)
    drone = lp(sine(36.7, dur) * .6 + sine(55, dur) * .25 + noise(dur, r) * .25, 140, 4) * (0.4 + 0.6 * tt / dur)
    put(fade(norm(drone, .8), 1.0, 1.0), 0, .55)
    put(fade(a_wind(dur, r), 1, 1), 0, .2)
    k = 0.5
    while k < dur - 0.5:
        put(s_heartbeat(0.9, r), k, .38 + .25 * (k / dur)); k += 0.92
    _, blasts, extra = paint_times(sb, tl)
    for b in blasts:
        put(s_boom(3.0, r), b, .9); put(s_impact(1.2, r), b, .6); put(a_fire(2.5, r), b + .2, .25)
    for l in extra:
        put(s_thunder(2.6, r), l, .45)
    return out[: int(dur * SR)]


def build_music(preset, dur):
    fn = MUSIC.get(preset)
    if not fn:
        return None
    x = fn(dur, rng_for("music", preset))
    x = norm(x, 0.8)
    x = fade(x, 1.0, 2.0)
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--music-only", action="store_true")
    args = ap.parse_args()
    proj = Path(args.project).resolve()
    sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
    tl = json.loads((proj / "timeline.json").read_text(encoding="utf-8"))
    adir = proj / "audio"
    adir.mkdir(exist_ok=True)
    res = {}
    if not args.music_only:
        sfx = build_sfx(sb, tl, proj)
        if sb.get("paint", {}).get("scary"):
            sfx = sfx + build_scary(sb, tl) * 1.1
            res["scary"] = True
        write_wav(adir / "sfx.wav", sfx)
        res["sfx"] = str(adir / "sfx.wav")
    if not args.no_music:
        preset = sb.get("music", STYLE_MUSIC.get(sb.get("style", ""), "none"))
        m = build_music(preset, tl["duration"])
        if m is not None:
            write_wav(adir / "music.wav", m)
            res["music"] = str(adir / "music.wav")
            res["music_preset"] = preset
    print(json.dumps(res))


if __name__ == "__main__":
    main()
