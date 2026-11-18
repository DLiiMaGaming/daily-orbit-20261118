#!/usr/bin/env python3
"""The Daily Orbit -- a newspaper front page for Wednesday 18 November 2026.

Draws a complete 1024x1024 broadsheet front page using only the Python
standard library (zlib, struct, os, sys).  The image is rendered into a
bytearray framebuffer with a hand-authored 5x7 bitmap font, a small
word-wrap / layout engine, horizontal rules, columns and simple geometric
illustrations.  Output is deterministic: no network, no randomness, no
timestamps -- two runs produce byte-identical PNG files.
"""

import os
import struct
import sys
import zlib

W = 1024
H = 1024

PAPER = (0xF8, 0xF4, 0xE9)
INK = (0x16, 0x13, 0x0D)
RED = (0xA3, 0x16, 0x21)
BLUE = (0x1D, 0x4E, 0x89)
WHITE = PAPER

# --------------------------------------------------------------------------
# 5x7 bitmap font.  Each glyph is 7 rows of 5 characters; '#' is ink.
# --------------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": (".....", ".....", ".####", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".####"),
    "f": ("..##.", ".#...", "#####", ".#...", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".....", ".####", "#...#", ".####", "....#", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "#####", ".#...", ".#...", ".#..#", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "•": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    "—": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
}


def normalise(text):
    return text.replace("’", "'").replace("‘", "'")


# --------------------------------------------------------------------------
# Framebuffer primitives (bytearray, row-slice fills -- no per-pixel loops
# for large areas).
# --------------------------------------------------------------------------
FB = bytearray(W * H * 3)


def fill_rect(x, y, w, h, colour):
    if w <= 0 or h <= 0:
        return
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(colour) * (x1 - x0)
    stride = W * 3
    off = y0 * stride + x0 * 3
    for _ in range(y0, y1):
        FB[off:off + len(row)] = row
        off += stride


def fill_circle(cx, cy, r, colour):
    r2 = r * r
    for dy in range(-r, r + 1):
        dx = int((r2 - dy * dy) ** 0.5)
        fill_rect(cx - dx, cy + dy, dx * 2 + 1, 1, colour)


def fill_ellipse(cx, cy, rx, ry, colour):
    if rx <= 0 or ry <= 0:
        return
    for dy in range(-ry, ry + 1):
        frac = 1.0 - (dy / ry) ** 2
        dx = int(rx * (frac ** 0.5)) if frac > 0 else 0
        fill_rect(cx - dx, cy + dy, dx * 2 + 1, 1, colour)


def draw_line(x0, y0, x1, y1, thick, colour):
    dx = x1 - x0
    dy = y1 - y0
    steps = int(max(abs(dx), abs(dy)))
    if steps == 0:
        fill_rect(x0 - thick // 2, y0 - thick // 2, thick, thick, colour)
        return
    half = thick // 2
    for i in range(steps + 1):
        x = x0 + dx * i // steps
        y = y0 + dy * i // steps
        fill_rect(x - half, y - half, thick, thick, colour)


def rule(x, y, w, thick, colour=INK):
    fill_rect(x, y, w, thick, colour)


# --------------------------------------------------------------------------
# Text engine
# --------------------------------------------------------------------------
def spacing_for(scale):
    return scale if scale > 1 else 1


def text_width(text, scale):
    text = normalise(text)
    if not text:
        return 0
    adv = 5 * scale + spacing_for(scale)
    return adv * len(text) - spacing_for(scale)


def draw_text(x, y, text, scale, colour):
    text = normalise(text)
    adv = 5 * scale + spacing_for(scale)
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT["?"])
        for gy in range(7):
            row = glyph[gy]
            for gx in range(5):
                if row[gx] == "#":
                    fill_rect(cx + gx * scale, y + gy * scale, scale, scale, colour)
        cx += adv
    return cx - spacing_for(scale)


def draw_text_centered(cx, y, text, scale, colour):
    w = text_width(text, scale)
    return draw_text(cx - w // 2, y, text, scale, colour)


def wrap_text(text, scale, max_width):
    words = normalise(text).split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(x, y, text, scale, colour, max_width, line_gap):
    lines = wrap_text(text, scale, max_width)
    for i, line in enumerate(lines):
        draw_text(x, y + i * (7 * scale + line_gap), line, scale, colour)
    return y + len(lines) * (7 * scale + line_gap)


# --------------------------------------------------------------------------
# Illustrations (flat geometric shapes only)
# --------------------------------------------------------------------------
def draw_lead_illustration(x, y, w, h):
    """Island, a missile arc over it, and a burst -- the Qeshm lead art."""
    # sea
    fill_rect(x, y, w, h, BLUE)
    # wavy horizon lines in paper colour
    for i in range(5):
        wy = y + h - 18 - i * 16
        for wx in range(x + 10 + (i % 2) * 22, x + w - 26, 46):
            fill_rect(wx, wy, 24, 3, PAPER)
    # island: a flattened ink mound sitting on the waterline
    fill_ellipse(x + w // 2, y + h - 28, 96, 26, INK)
    fill_ellipse(x + w // 2 - 20, y + h - 40, 34, 8, PAPER)
    # launch site: small ink block on the island
    fill_rect(x + w // 2 - 8, y + h - 62, 16, 14, INK)
    # missile arc: quadratic bezier from island up and to the right, in red
    x0, y0 = x + w // 2, y + h - 64
    x1, y1 = x + w // 2 + 40, y + 8
    x2, y2 = x + w - 42, y + 44
    steps = 60
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        px = int(u * u * x0 + 2 * u * t * x1 + t * t * x2)
        py = int(u * u * y0 + 2 * u * t * y1 + t * t * y2)
        if i % 3 != 2:  # dashed trail
            fill_rect(px - 2, py - 2, 5, 5, RED)
    # missile head
    fill_circle(x2, y2, 6, RED)
    # burst: red star of radiating lines at the far shore
    bx, by = x + w - 42, y + 58
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1),
                   (1, -1), (-1, 1), (2, 1), (-2, -1), (1, 2), (-1, -2)):
        draw_line(bx, by, bx + dx * 9, by + dy * 9, 3, RED)
    fill_circle(bx, by, 5, RED)
    # caption strip
    fill_rect(x, y + h - 14, w, 14, INK)


def draw_bridge_icon(x, y):
    """Tiny bridge with a broken span."""
    fill_rect(x, y + 22, 74, 5, INK)
    fill_rect(x + 6, y + 4, 6, 40, INK)
    fill_rect(x + 62, y + 4, 6, 40, INK)
    draw_line(x + 9, y + 4, x + 37, y + 22, 3, BLUE)
    draw_line(x + 65, y + 4, x + 48, y + 18, 3, BLUE)
    # fallen span, tilted into the water
    draw_line(x + 36, y + 24, x + 50, y + 40, 5, RED)
    fill_rect(x, y + 44, 74, 4, BLUE)


def draw_virus_icon(x, y):
    fill_circle(x + 26, y + 24, 15, RED)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1),
                   (1, -1), (-1, 1)):
        draw_line(x + 26, y + 24, x + 26 + dx * 22, y + 24 + dy * 22, 3, RED)
        fill_circle(x + 26 + dx * 24, y + 24 + dy * 24, 4, RED)
    fill_circle(x + 21, y + 19, 4, PAPER)
    fill_circle(x + 32, y + 29, 3, PAPER)


def draw_syringe_icon(x, y):
    draw_line(x + 8, y + 40, x + 40, y + 8, 7, BLUE)
    draw_line(x + 40, y + 8, x + 52, y - 4 + 8, 3, INK)
    fill_rect(x + 2, y + 38, 14, 6, INK)
    fill_rect(x + 34, y + 2, 16, 6, RED)
    fill_circle(x + 52, y + 40, 5, RED)


def draw_globe_icon(x, y):
    fill_circle(x + 26, y + 24, 20, BLUE)
    fill_rect(x + 24, y + 4, 4, 40, PAPER)
    fill_rect(x + 6, y + 22, 40, 4, PAPER)
    draw_line(x + 12, y + 10, x + 40, y + 38, 3, PAPER)
    draw_line(x + 40, y + 10, x + 12, y + 38, 3, PAPER)


# --------------------------------------------------------------------------
# Page layout
# --------------------------------------------------------------------------
M = 32               # page margin
CW = W - 2 * M       # content width = 960


def build_page():
    fill_rect(0, 0, W, H, PAPER)
    # outer frame
    rule(M - 8, 18, CW + 16, 3)
    rule(M - 8, H - 10, CW + 16, 3)

    # ---- 1. Masthead ------------------------------------------------------
    draw_text_centered(W // 2, 32, "THE DAILY ORBIT", 10, INK)
    draw_text_centered(W // 2, 110, "ALL THE WORLD'S NEWS OF ONE DAY — ON ONE PAGE", 2, INK)
    rule(M, 134, CW, 2)

    # ---- 2. Date band ------------------------------------------------------
    fill_rect(M, 142, CW, 48, INK)
    draw_text_centered(W // 2 - 40, 152, "WEDNESDAY 18 NOVEMBER 2026", 4, PAPER)
    draw_text(856, 150, "Vol. I", 2, PAPER)
    draw_text(856, 168, "No. 18", 1, PAPER)

    # ---- 3. Lead story -----------------------------------------------------
    draw_text(M, 204, "GULF WAR • QESHM ISLAND", 2, RED)
    y = draw_wrapped(M, 224,
                     "US BOMBS IRANIAN MISSILE SITE; TEHRAN HITS BACK ACROSS THE GULF",
                     5, INK, CW, 8)
    # deck (left) + illustration (right); y is now just past the headline
    deck_x, deck_w = M, 590
    draw_wrapped(deck_x, y + 12,
                 "American jets strike a Revolutionary Guard launch site on "
                 "Qeshm Island; Iran answers with drones on Bahrain and "
                 "Kuwait as the war widens.",
                 2, INK, deck_w, 6)
    draw_text(deck_x, y + 94, "THE WAR WIDENS ACROSS THE GULF", 2, BLUE)
    draw_lead_illustration(654, y + 8, 338, 112)
    rule(M, 434, CW, 3)

    # ---- 4. Secondary stories: two rows of two columns --------------------
    stories = [
        ("KERCH BRIDGE SPAN FALLS AFTER SECOND DAY OF STRIKES",
         "Ukraine hits the bridge to Crimea for a second day and part of "
         "its road span collapses into the strait.", draw_bridge_icon),
        ("EBOLA CASES MORE THAN DOUBLE IN CONGO",
         "The outbreak passes 11,000 cases and 5,400 deaths, the UN says; "
         "three of four infected under-fives die.", draw_virus_icon),
        ("US LOSES MEASLES-FREE STATUS AFTER 26 YEARS",
         "A record year tops 5,400 cases and 10 deaths, ending the "
         "elimination status held since 2000.", draw_syringe_icon),
        ("XI HOSTS PUTIN IN SHENZHEN AND DENOUNCES SANCTIONS",
         "At the APEC summit Xi urges lower trade barriers; the first "
         "US-China-Russia trilateral follows on Thursday.", draw_globe_icon),
    ]
    col_x = (M, M + CW // 2 + 16)
    col_w = CW // 2 - 32
    row_y = (446, 588)
    for idx, (head, body, icon) in enumerate(stories):
        cx = col_x[idx % 2]
        cy = row_y[idx // 2]
        icon(cx + col_w - 78, cy)
        # body starts wherever the (2- or 3-line) headline actually ends,
        # so headline and body can never collide
        head_end = draw_wrapped(cx, cy, head, 3, INK, col_w - 86, 2)
        draw_wrapped(cx, head_end + 4, body, 2, INK, col_w, 4)
    rule(M, 578, CW, 2)
    rule(M, 738, CW, 3)

    # ---- 5. In brief --------------------------------------------------------
    draw_text(M, 750, "IN BRIEF", 3, RED)
    briefs = [
        "US POLITICS — Peltola wins Alaska; Democrats take a 56-seat Senate majority.",
        "RUSSIA — Military plane crashes in Siberia, killing all 19 aboard.",
        "PACIFIC — Category 5 Cyclone Xavier strikes the northern Cook Islands.",
        "ISRAEL — President taps Eisenkot to form a government, bypassing Netanyahu.",
    ]
    by = 782
    for line in briefs:
        fill_rect(M + 2, by + 5, 8, 8, BLUE)
        draw_text(M + 20, by, line, 2, INK)
        by += 25
    rule(M, 878, CW, 2)

    # ---- 6. The day in numbers ---------------------------------------------
    box_y = 890
    fill_rect(M, box_y, CW, 90, INK)
    draw_text(M + 16, box_y + 10, "THE DAY IN NUMBERS", 3, PAPER)
    nums_left = [
        "11,000+ Ebola cases in DR Congo (UN)",
        "5,400 measles cases in the US this year",
    ]
    nums_right = [
        "19 killed in Siberian plane crash",
        "56 Senate seats for the Democrats",
    ]
    ny = box_y + 42
    for line in nums_left:
        draw_text(M + 16, ny, line, 2, PAPER)
        ny += 22
    ny = box_y + 42
    for line in nums_right:
        draw_text(M + 500, ny, line, 2, PAPER)
        ny += 22

    # ---- 7. Footer ------------------------------------------------------------
    rule(M, 990, CW, 2)
    draw_text_centered(W // 2, 1000,
                       "Stories as reported on Wednesday 18 November 2026 — "
                       "Al Jazeera, Associated Press, CBS News, Japan Times wires.",
                       1, INK)


# --------------------------------------------------------------------------
# PNG encoder (pure stdlib)
# --------------------------------------------------------------------------
def chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def encode_png():
    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)  # filter type 0 for every row
        raw += FB[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


def main():
    build_page()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(encode_png())
    return 0


if __name__ == "__main__":
    sys.exit(main())
