#!/usr/bin/env python3
"""The Daily Orbit -- Wednesday 18 November 2026, drawn as a front page.

A small program, Python standard library only, that paints a 1024x1024
broadsheet front page summing up the day's world news and saves it as a
PNG.  Letters come from a 5x7 bitmap font kept as row bitmasks (one
integer per row, most significant bit on the left); the page itself is
assembled on a canvas object with boxes, discs, line segments and wrapped
paragraphs; the PNG writer packs the canvas with zlib.  Nothing here
touches the network, the clock or any random source, so every run writes
exactly the same bytes.
"""

import os, struct, sys, zlib

WIDTH, HEIGHT = 1024, 1024
PAPER, INK = (0xF8, 0xF4, 0xE9), (0x16, 0x13, 0x0D)
RED, BLUE = (0xA3, 0x16, 0x21), (0x1D, 0x4E, 0x89)

# 5x7 bitmap font, one 7-tuple of row bitmasks per glyph.  Bit 4 is the
# leftmost column, bit 0 the rightmost; a set bit paints ink.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0F, 0x10, 0x10, 0x10, 0x10, 0x10, 0x0F),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0F, 0x10, 0x10, 0x17, 0x11, 0x11, 0x0E),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x1F),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x0A, 0x04, 0x04, 0x04, 0x0A, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "a": (0x00, 0x00, 0x0F, 0x01, 0x0F, 0x11, 0x0F),
    "b": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    "c": (0x00, 0x00, 0x0F, 0x10, 0x10, 0x10, 0x0F),
    "d": (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    "e": (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0F),
    "f": (0x06, 0x08, 0x1F, 0x08, 0x08, 0x08, 0x08),
    "g": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "h": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "i": (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    "j": (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    "k": (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    "l": (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "m": (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    "n": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "o": (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    "p": (0x00, 0x00, 0x1E, 0x11, 0x1E, 0x10, 0x10),
    "q": (0x00, 0x00, 0x0F, 0x11, 0x0F, 0x01, 0x01),
    "r": (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    "s": (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    "t": (0x08, 0x08, 0x1F, 0x08, 0x08, 0x09, 0x06),
    "u": (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    "v": (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "w": (0x00, 0x00, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "x": (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    "y": (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "z": (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    "0": (0x0E, 0x13, 0x15, 0x19, 0x11, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1E, 0x01, 0x01, 0x0E, 0x01, 0x01, 0x1E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x0E, 0x10, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x01, 0x0E),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C, 0x08),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x09, 0x1E, 0x04),
    "•": (0x00, 0x00, 0x0E, 0x0E, 0x0E, 0x00, 0x00),
    "—": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
}


def tidy(text):
    return text.replace("’", "'").replace("‘", "'")


class Sheet:
    """A flat RGB canvas with drawing helpers and a PNG writer."""

    def __init__(self, w, h, paper):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.box(0, 0, w, h, paper)

    def box(self, x, y, w, h, colour):
        left, top = max(0, x), max(0, y)
        right, bottom = min(self.w, x + w), min(self.h, y + h)
        if w <= 0 or h <= 0 or right <= left or bottom <= top:
            return
        row = bytes(colour) * (right - left)
        stride = self.w * 3
        off = top * stride + left * 3
        for _ in range(top, bottom):
            self.px[off:off + len(row)] = row
            off += stride

    def disc(self, cx, cy, r, colour):
        rr = r * r
        for dy in range(-r, r + 1):
            dx = int((rr - dy * dy) ** 0.5)
            self.box(cx - dx, cy + dy, dx * 2 + 1, 1, colour)

    def oval(self, cx, cy, rx, ry, colour):
        if rx <= 0 or ry <= 0:
            return
        for dy in range(-ry, ry + 1):
            frac = 1.0 - (dy / ry) ** 2
            dx = int(rx * (frac ** 0.5)) if frac > 0 else 0
            self.box(cx - dx, cy + dy, dx * 2 + 1, 1, colour)

    def seg(self, x0, y0, x1, y1, thick, colour):
        dx, dy = x1 - x0, y1 - y0
        steps = int(max(abs(dx), abs(dy)))
        half = thick // 2
        if steps == 0:
            self.box(x0 - half, y0 - half, thick, thick, colour)
            return
        for i in range(steps + 1):
            self.box(x0 + dx * i // steps - half, y0 + dy * i // steps - half,
                     thick, thick, colour)

    def bar(self, x, y, w, thick, colour=INK):
        self.box(x, y, w, thick, colour)

    def _gap(self, scale):
        return scale if scale > 1 else 1

    def measure(self, text, scale):
        text = tidy(text)
        if not text:
            return 0
        adv = 5 * scale + self._gap(scale)
        return adv * len(text) - self._gap(scale)

    def glyph(self, x, y, ch, scale, colour):
        rows = FONT.get(ch, FONT["?"])
        for r in range(7):
            bits = rows[r]
            for c in range(5):
                if bits & (1 << (4 - c)):
                    self.box(x + c * scale, y + r * scale, scale, scale, colour)

    def put(self, x, y, text, scale, colour):
        text = tidy(text)
        adv = 5 * scale + self._gap(scale)
        cx = x
        for ch in text:
            self.glyph(cx, y, ch, scale, colour)
            cx += adv
        return cx - self._gap(scale)

    def put_centre(self, cx, y, text, scale, colour):
        return self.put(cx - self.measure(text, scale) // 2, y, text, scale, colour)

    def wrap(self, text, scale, width):
        words = tidy(text).split(" ")
        lines, cur = [], ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if self.measure(trial, scale) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def flow(self, x, y, text, scale, colour, width, gap):
        lines = self.wrap(text, scale, width)
        for i, line in enumerate(lines):
            self.put(x, y + i * (7 * scale + gap), line, scale, colour)
        return y + len(lines) * (7 * scale + gap)

    def png_bytes(self):
        raw = bytearray()
        stride = self.w * 3
        for yy in range(self.h):
            raw.append(0)
            raw += self.px[yy * stride:(yy + 1) * stride]
        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)

        def _chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data +
                    struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
                _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
                _chunk(b"IEND", b""))


def lead_art(pg, x, y, w, h):
    """Sea, an island launch site, a missile arc and a burst."""
    pg.box(x, y, w, h, BLUE)
    for i in range(5):
        yy = y + h - 18 - i * 16
        for xx in range(x + 10 + (i % 2) * 22, x + w - 26, 46):
            pg.box(xx, yy, 24, 3, PAPER)
    pg.oval(x + w // 2, y + h - 28, 96, 26, INK)
    pg.oval(x + w // 2 - 20, y + h - 40, 34, 8, PAPER)
    pg.box(x + w // 2 - 8, y + h - 62, 16, 14, INK)
    ax, ay = x + w // 2, y + h - 64
    bx, by = x + w // 2 + 40, y + 8
    cx, cy = x + w - 42, y + 44
    for i in range(61):
        t = i / 60
        u = 1.0 - t
        px = int(u * u * ax + 2 * u * t * bx + t * t * cx)
        py = int(u * u * ay + 2 * u * t * by + t * t * cy)
        if i % 3 != 2:
            pg.box(px - 2, py - 2, 5, 5, RED)
    pg.disc(cx, cy, 6, RED)
    ex, ey = x + w - 42, y + 58
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1),
                   (1, -1), (-1, 1), (2, 1), (-2, -1), (1, 2), (-1, -2)):
        pg.seg(ex, ey, ex + dx * 9, ey + dy * 9, 3, RED)
    pg.disc(ex, ey, 5, RED)
    pg.box(x, y + h - 14, w, 14, INK)


def bridge_icon(pg, x, y):
    """A bridge with its middle span dropped into the water."""
    pg.box(x, y + 22, 74, 5, INK)
    pg.box(x + 6, y + 4, 6, 40, INK)
    pg.box(x + 62, y + 4, 6, 40, INK)
    pg.seg(x + 9, y + 4, x + 37, y + 22, 3, BLUE)
    pg.seg(x + 65, y + 4, x + 48, y + 18, 3, BLUE)
    pg.seg(x + 36, y + 24, x + 50, y + 40, 5, RED)
    pg.box(x, y + 44, 74, 4, BLUE)


def virus_icon(pg, x, y):
    pg.disc(x + 26, y + 24, 15, RED)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1),
                   (1, -1), (-1, 1)):
        pg.seg(x + 26, y + 24, x + 26 + dx * 22, y + 24 + dy * 22, 3, RED)
        pg.disc(x + 26 + dx * 24, y + 24 + dy * 24, 4, RED)
    pg.disc(x + 21, y + 19, 4, PAPER)
    pg.disc(x + 32, y + 29, 3, PAPER)


def syringe_icon(pg, x, y):
    pg.seg(x + 8, y + 40, x + 40, y + 8, 7, BLUE)
    pg.seg(x + 40, y + 8, x + 52, y - 4 + 8, 3, INK)
    pg.box(x + 2, y + 38, 14, 6, INK)
    pg.box(x + 34, y + 2, 16, 6, RED)
    pg.disc(x + 52, y + 40, 5, RED)


def globe_icon(pg, x, y):
    pg.disc(x + 26, y + 24, 20, BLUE)
    pg.box(x + 24, y + 4, 4, 40, PAPER)
    pg.box(x + 6, y + 22, 40, 4, PAPER)
    pg.seg(x + 12, y + 10, x + 40, y + 38, 3, PAPER)
    pg.seg(x + 40, y + 10, x + 12, y + 38, 3, PAPER)


MARGIN = 32
CONTENT = WIDTH - 2 * MARGIN


def draw_front(pg):
    pg.bar(MARGIN - 8, 18, CONTENT + 16, 3)
    pg.bar(MARGIN - 8, HEIGHT - 10, CONTENT + 16, 3)

    # 1. Masthead
    pg.put_centre(WIDTH // 2, 32, "THE DAILY ORBIT", 10, INK)
    pg.put_centre(WIDTH // 2, 110, "ALL THE WORLD'S NEWS OF ONE DAY — ON ONE PAGE", 2, INK)
    pg.bar(MARGIN, 134, CONTENT, 2)

    # 2. Date band
    pg.box(MARGIN, 142, CONTENT, 48, INK)
    pg.put_centre(WIDTH // 2 - 40, 152, "WEDNESDAY 18 NOVEMBER 2026", 4, PAPER)
    pg.put(856, 150, "Vol. I", 2, PAPER)
    pg.put(856, 168, "No. 18", 1, PAPER)

    # 3. Lead story
    pg.put(MARGIN, 204, "GULF WAR • QESHM ISLAND", 2, RED)
    y = pg.flow(MARGIN, 224, "US BOMBS IRANIAN MISSILE SITE; TEHRAN HITS BACK ACROSS THE GULF",
                5, INK, CONTENT, 8)
    pg.flow(MARGIN, y + 12, "American jets strike a Revolutionary Guard launch site on "
            "Qeshm Island; Iran answers with drones on Bahrain and "
            "Kuwait as the war widens.", 2, INK, 590, 6)
    pg.put(MARGIN, y + 94, "THE WAR WIDENS ACROSS THE GULF", 2, BLUE)
    lead_art(pg, 654, y + 8, 338, 112)
    pg.bar(MARGIN, 434, CONTENT, 3)

    # 4. Secondary stories, two rows of two columns
    stories = [
        ("KERCH BRIDGE SPAN FALLS AFTER SECOND DAY OF STRIKES",
         "Ukraine hits the bridge to Crimea for a second day and part of "
         "its road span collapses into the strait.", bridge_icon),
        ("EBOLA CASES MORE THAN DOUBLE IN CONGO",
         "The outbreak passes 11,000 cases and 5,400 deaths, the UN says; "
         "three of four infected under-fives die.", virus_icon),
        ("US LOSES MEASLES-FREE STATUS AFTER 26 YEARS",
         "A record year tops 5,400 cases and 10 deaths, ending the "
         "elimination status held since 2000.", syringe_icon),
        ("XI HOSTS PUTIN IN SHENZHEN AND DENOUNCES SANCTIONS",
         "At the APEC summit Xi urges lower trade barriers; the first "
         "US-China-Russia trilateral follows on Thursday.", globe_icon),
    ]
    col_x = (MARGIN, MARGIN + CONTENT // 2 + 16)
    col_w = CONTENT // 2 - 32
    row_y = (446, 588)
    for idx, (head, body, icon) in enumerate(stories):
        cx = col_x[idx % 2]
        cy = row_y[idx // 2]
        icon(pg, cx + col_w - 78, cy)
        head_end = pg.flow(cx, cy, head, 3, INK, col_w - 86, 2)
        pg.flow(cx, head_end + 4, body, 2, INK, col_w, 4)
    pg.bar(MARGIN, 578, CONTENT, 2)
    pg.bar(MARGIN, 738, CONTENT, 3)

    # 5. In brief
    pg.put(MARGIN, 750, "IN BRIEF", 3, RED)
    briefs = [
        "US POLITICS — Peltola wins Alaska; Democrats take a 56-seat Senate majority.",
        "RUSSIA — Military plane crashes in Siberia, killing all 19 aboard.",
        "PACIFIC — Category 5 Cyclone Xavier strikes the northern Cook Islands.",
        "ISRAEL — President taps Eisenkot to form a government, bypassing Netanyahu.",
    ]
    by = 782
    for line in briefs:
        pg.box(MARGIN + 2, by + 5, 8, 8, BLUE)
        pg.put(MARGIN + 20, by, line, 2, INK)
        by += 25
    pg.bar(MARGIN, 878, CONTENT, 2)

    # 6. The day in numbers
    box_y = 890
    pg.box(MARGIN, box_y, CONTENT, 90, INK)
    pg.put(MARGIN + 16, box_y + 10, "THE DAY IN NUMBERS", 3, PAPER)
    ny = box_y + 42
    for line in ("11,000+ Ebola cases in DR Congo (UN)",
                 "5,400 measles cases in the US this year"):
        pg.put(MARGIN + 16, ny, line, 2, PAPER)
        ny += 22
    ny = box_y + 42
    for line in ("19 killed in Siberian plane crash",
                 "56 Senate seats for the Democrats"):
        pg.put(MARGIN + 500, ny, line, 2, PAPER)
        ny += 22

    # 7. Footer
    pg.bar(MARGIN, 990, CONTENT, 2)
    pg.put_centre(WIDTH // 2, 1000, "Stories as reported on Wednesday 18 November 2026 — "
                  "Al Jazeera, Associated Press, CBS News, Japan Times wires.", 1, INK)


def main():
    pg = Sheet(WIDTH, HEIGHT, PAPER)
    draw_front(pg)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(pg.png_bytes())
    return 0


if __name__ == "__main__":
    sys.exit(main())
