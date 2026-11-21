#!/usr/bin/env python3
"""THE WORLD IN ONE DAY - 21 November 2026.

Renders a 1024x1024 broadsheet front page that sums up the world news of
Saturday 21 November 2026 as a single PNG and writes it to /output/entry.png
(a copy is also left beside this script). Pure Python 3.13 standard library:
the page is drawn pixel by pixel with a small hand-built stroke font, then
encoded as a PNG with zlib. No network, no third-party packages, and the
output is deterministic - two runs produce byte-identical files.
"""

import struct
import zlib
from pathlib import Path

W = 1024
H = 1024

PAPER = (247, 243, 232)
INK = (18, 18, 20)
FAINT = (96, 92, 84)
RULE = (30, 30, 34)
ACCENT = (154, 26, 26)
PHOTO = (38, 52, 74)
PHOTO2 = (84, 104, 128)
SKIN = (216, 178, 148)
WHITE = (250, 249, 245)


# ---------------------------------------------------------------------------
# Framebuffer helpers
# ---------------------------------------------------------------------------

class Canvas:
    """A flat RGB framebuffer with just enough drawing primitives."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(0, (thick - 1) // 2)
        for s in range(steps + 1):
            cx = x0 + (x1 - x0) * s // steps
            cy = y0 + (y1 - y0) * s // steps
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    self.set(cx + dx, cy + dy, color)

    def circle(self, cx, cy, rad, color, thick=1):
        import math
        for deg in range(0, 360, 1):
            a = math.radians(deg)
            for rr in range(rad - thick + 1, rad + 1):
                self.set(int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a)), color)

    def disc(self, cx, cy, rad, color):
        for yy in range(cy - rad, cy + rad + 1):
            for xx in range(cx - rad, cx + rad + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= rad * rad:
                    self.set(xx, yy, color)


def encode_png(canvas):
    """Encode the framebuffer as a deterministic PNG (filter 0 rows)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png



# ---------------------------------------------------------------------------
# Stroke font. Each glyph is a list of polylines on a grid 8 wide, 12 tall
# (y grows downward, baseline at y=12). Drawn with round-ish thick strokes.
# ---------------------------------------------------------------------------

FONT = {
    "A": [[(0, 12), (4, 0), (8, 12)], [(2, 8), (6, 8)]],
    "B": [[(0, 0), (0, 12)], [(0, 0), (5, 0), (7, 1), (7, 4), (5, 6), (0, 6)],
          [(5, 6), (7, 7), (7, 10), (5, 12), (0, 12)]],
    "C": [[(8, 2), (6, 0), (2, 0), (0, 2), (0, 10), (2, 12), (6, 12), (8, 10)]],
    "D": [[(0, 0), (0, 12)], [(0, 0), (5, 0), (8, 3), (8, 9), (5, 12), (0, 12)]],
    "E": [[(8, 0), (0, 0), (0, 12), (8, 12)], [(0, 6), (6, 6)]],
    "F": [[(8, 0), (0, 0), (0, 12)], [(0, 6), (6, 6)]],
    "G": [[(8, 2), (6, 0), (2, 0), (0, 2), (0, 10), (2, 12), (6, 12), (8, 10),
           (8, 7), (5, 7)]],
    "H": [[(0, 0), (0, 12)], [(8, 0), (8, 12)], [(0, 6), (8, 6)]],
    "I": [[(4, 0), (4, 12)], [(1, 0), (7, 0)], [(1, 12), (7, 12)]],
    "J": [[(8, 0), (8, 10), (6, 12), (2, 12), (0, 10)]],
    "K": [[(0, 0), (0, 12)], [(8, 0), (1, 6)], [(2, 7), (8, 12)]],
    "L": [[(0, 0), (0, 12), (8, 12)]],
    "M": [[(0, 12), (0, 0), (4, 7), (8, 0), (8, 12)]],
    "N": [[(0, 12), (0, 0), (8, 12), (8, 0)]],
    "O": [[(2, 0), (6, 0), (8, 2), (8, 10), (6, 12), (2, 12), (0, 10), (0, 2),
           (2, 0)]],
    "P": [[(0, 12), (0, 0), (6, 0), (8, 2), (8, 5), (6, 7), (0, 7)]],
    "Q": [[(2, 0), (6, 0), (8, 2), (8, 10), (6, 12), (2, 12), (0, 10), (0, 2),
           (2, 0)], [(5, 9), (8, 12)]],
    "R": [[(0, 12), (0, 0), (6, 0), (8, 2), (8, 5), (6, 7), (0, 7)],
          [(4, 7), (8, 12)]],
    "S": [[(8, 1), (5, 0), (2, 0), (0, 2), (1, 5), (7, 7), (8, 9), (6, 12),
           (2, 12), (0, 11)]],
    "T": [[(0, 0), (8, 0)], [(4, 0), (4, 12)]],
    "U": [[(0, 0), (0, 10), (2, 12), (6, 12), (8, 10), (8, 0)]],
    "V": [[(0, 0), (4, 12), (8, 0)]],
    "W": [[(0, 0), (2, 12), (4, 5), (6, 12), (8, 0)]],
    "X": [[(0, 0), (8, 12)], [(8, 0), (0, 12)]],
    "Y": [[(0, 0), (4, 6), (8, 0)], [(4, 6), (4, 12)]],
    "Z": [[(0, 0), (8, 0), (0, 12), (8, 12)]],
    "0": [[(2, 0), (6, 0), (8, 2), (8, 10), (6, 12), (2, 12), (0, 10), (0, 2),
           (2, 0)], [(2, 10), (6, 2)]],
    "1": [[(2, 2), (5, 0), (5, 12)], [(2, 12), (8, 12)]],
    "2": [[(0, 2), (2, 0), (6, 0), (8, 2), (0, 12), (8, 12)]],
    "3": [[(0, 2), (2, 0), (6, 0), (8, 2), (6, 6), (3, 6)],
          [(6, 6), (8, 8), (8, 10), (6, 12), (2, 12), (0, 10)]],
    "4": [[(5, 12), (5, 0), (0, 8), (8, 8)]],
    "5": [[(8, 0), (0, 0), (0, 5), (6, 5), (8, 7), (8, 10), (6, 12), (1, 12),
           (0, 10)]],
    "6": [[(7, 0), (3, 0), (0, 4), (0, 10), (2, 12), (6, 12), (8, 10), (7, 6),
           (4, 5), (1, 6)]],
    "7": [[(0, 0), (8, 0), (3, 12)]],
    "8": [[(3, 0), (5, 0), (7, 2), (7, 4), (5, 6), (3, 6), (1, 4), (1, 2),
           (3, 0)], [(3, 6), (5, 6), (7, 8), (7, 11), (5, 12), (3, 12),
                      (1, 11), (1, 8), (3, 6)]],
    "9": [[(1, 12), (4, 12), (7, 9), (8, 4), (6, 0), (2, 0), (0, 2), (0, 5),
           (2, 7), (5, 7), (8, 5)]],
    ".": [[(4, 11), (4, 12)]],
    ",": [[(4, 10), (3, 13)]],
    "'": [[(4, 0), (4, 3)]],
    "-": [[(1, 6), (7, 6)]],
    "–": [[(0, 6), (8, 6)]],
    "—": [[(0, 6), (8, 6)]],
    ":": [[(4, 3), (4, 4)], [(4, 9), (4, 10)]],
    ";": [[(4, 3), (4, 4)], [(4, 9), (3, 12)]],
    "!": [[(4, 0), (4, 8)], [(4, 11), (4, 12)]],
    "?": [[(0, 2), (2, 0), (6, 0), (8, 2), (8, 4), (4, 7), (4, 9)],
          [(4, 11), (4, 12)]],
    "£": [[(7, 1), (4, 0), (2, 1), (2, 5), (0, 9), (0, 12), (8, 12)],
          [(0, 7), (5, 7)]],
    "$": [[(8, 1), (5, 0), (2, 0), (0, 2), (1, 5), (7, 7), (8, 9), (6, 12),
           (2, 12), (0, 11)], [(4, 0), (4, 12)]],
    "%": [[(0, 12), (8, 0)], [(1, 1), (3, 1), (3, 4), (1, 4), (1, 1)],
          [(5, 8), (7, 8), (7, 11), (5, 11), (5, 8)]],
    "+": [[(4, 2), (4, 10)], [(1, 6), (7, 6)]],
    "/": [[(1, 12), (7, 0)]],
    "(": [[(6, 0), (3, 2), (3, 10), (6, 12)]],
    ")": [[(2, 0), (5, 2), (5, 10), (2, 12)]],
    '"': [[(2, 0), (2, 3)], [(6, 0), (6, 3)]],
    "=": [[(1, 4), (7, 4)], [(1, 8), (7, 8)]],
    "·": [[(4, 6), (4, 7)]],
}

ADV = 10.0  # glyph advance in grid units (glyph body is 8 wide)


def text_width(text, size):
    """Pixel width of a string at a given cap-height-ish scale."""
    return len(text) * ADV * size / 12.0


def draw_text(cv, x, y, text, size, color, thick=None, align="left"):
    """Draw text with its top at y. size = pixels per grid unit * 12 / 12:
    a size of s means the glyph cell is 12*s px tall. Returns end x."""
    if thick is None:
        thick = max(1, round(size * 0.16))
    text = text.upper()
    w = text_width(text, size)
    if align == "center":
        x = x - w / 2
    elif align == "right":
        x = x - w
    cx = x
    for ch in text:
        glyph = FONT.get(ch)
        if glyph and ch != " ":
            for stroke in glyph:
                pts = [(cx + gx * size / 12.0, y + gy * size / 12.0)
                       for gx, gy in stroke]
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    cv.line(round(x0), round(y0), round(x1), round(y1),
                            color, thick)
        cx += ADV * size / 12.0
    return cx


def wrap(text, size, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines



# ---------------------------------------------------------------------------
# Page furniture and story blocks
# ---------------------------------------------------------------------------

MARGIN = 36
PAGE_W = W - 2 * MARGIN


def rule(cv, y, thick=2, color=RULE):
    cv.hline(MARGIN, y, PAGE_W, color, thick)


def story_block(cv, x, y, w, dateline, headline, body, hsize=17, bsize=12):
    """One grid story: red dateline, bold headline, three-line body.
    Returns the y just below the block."""
    draw_text(cv, x, y, dateline, 11.5, ACCENT, thick=2)
    y += 17
    for ln in wrap(headline, hsize, w):
        draw_text(cv, x, y, ln, hsize, INK, thick=3)
        y += int(hsize * 1.3)
    y += 1
    for ln in wrap(body, bsize, w):
        draw_text(cv, x, y, ln, bsize, INK, thick=2)
        y += int(bsize * 1.33)
    return y


def draw_photo(cv, x, y, w, h):
    """A simple drawn 'photograph': night sky over fields, missile trails
    arcing down, burst stars where the debris fell."""
    cv.rect(x, y, w, h, PHOTO)
    for i in range(6):  # sky bands, lighter towards the horizon
        band = tuple(min(255, c + i * 7) for c in PHOTO2)
        cv.rect(x, y + h // 3 + i * 8, w, 8, band)
    cv.rect(x, y + int(h * 0.72), w, h - int(h * 0.72), (52, 62, 44))
    cv.disc(x + w - 52, y + 34, 15, (232, 230, 214))  # moon
    # missile trails: three descending arcs made of short segments
    import math
    for sx, ex, peak in ((30, 150, 66), (90, 235, 44), (170, 300, 80)):
        for t in range(0, 21):
            f = t / 20.0
            px = x + sx + (ex - sx) * f
            py = y + 16 + (h * 0.72 - 26) * (f * f) - peak * 4 * f * (1 - f)
            cv.disc(int(px), int(py), 2, (240, 200, 120))
    # burst stars on the ground line
    for bx in (150, 235, 300):
        cx, cy = x + bx, y + int(h * 0.72) - 4
        for dx, dy in ((0, -11), (0, 11), (-11, 0), (11, 0), (-8, -8), (8, -8),
                       (-8, 8), (8, 8)):
            cv.line(cx, cy, cx + dx, cy + dy, (246, 178, 84), 2)
        cv.disc(cx, cy, 4, (250, 214, 140))
    cv.rect(x, y, w, 2, INK)
    cv.rect(x, y + h - 2, w, 2, INK)
    cv.rect(x, y, 2, h, INK)
    cv.rect(x + w - 2, y, 2, h, INK)


def compose():
    cv = Canvas(W, H, PAPER)

    # --- top strip -------------------------------------------------------
    draw_text(cv, MARGIN, 14, "ONE PAGE · THE WHOLE PLANET", 12.5, FAINT,
              thick=2)
    draw_text(cv, W - MARGIN, 14, "NO. 21,111 · PRICE: ONE IMAGE", 12.5,
              FAINT, thick=2, align="right")
    rule(cv, 36, 2)

    # --- masthead ---------------------------------------------------------
    draw_text(cv, W // 2, 46, "THE WORLD IN ONE DAY", 52, INK, thick=6,
              align="center")
    rule(cv, 110, 5)
    cv.rect(MARGIN, 120, PAGE_W, 32, INK)
    draw_text(cv, W // 2, 126, "SATURDAY · 21 NOVEMBER 2026", 20, WHITE,
              thick=3, align="center")
    rule(cv, 158, 2)

    # --- lead story -------------------------------------------------------
    draw_text(cv, MARGIN, 168, "WAR IN EUROPE · THE NATO FRONTIER", 14,
              ACCENT, thick=2)
    draw_text(cv, MARGIN, 188, "RUSSIAN MISSILES FALL", 38, INK, thick=5)
    draw_text(cv, MARGIN, 236, "ON POLISH SOIL", 38, INK, thick=5)
    lead = ("Two cruise missiles and a drone came down inside Poland near "
            "a coalition training ground. Warsaw called it a deliberate "
            "provocation, and NATO's secretary general flew in within "
            "hours. The debris fell in eastern fields as allied units "
            "exercised nearby. No deaths were reported, but Poland has "
            "put its air defences on the highest alert.")
    sy = 296
    for ln in wrap(lead, 14.5, 560):
        draw_text(cv, MARGIN, sy, ln, 14.5, INK, thick=2)
        sy += 20
    draw_photo(cv, 628, 292, 360, 150)
    draw_text(cv, 628, 450, "DEBRIS FIELD IN THE EAST, FROM WIRE REPORTS",
              10.5, FAINT, thick=2)
    rule(cv, 466, 2)

    # --- grid of world stories -------------------------------------------
    draw_text(cv, MARGIN, 478, "AROUND THE WORLD", 15, INK, thick=3)
    rule(cv, 502, 1, FAINT)
    col_w = (PAGE_W - 28) // 2
    col_x = (MARGIN, MARGIN + col_w + 28)
    stories = [
        ("KYIV", "KYIV WEATHERS NOVEMBER'S HEAVIEST BOMBARDMENT",
         "Ukraine counted 515 weapons overnight: 27 ballistic missiles, "
         "84 cruise missiles, 404 drones. Three Dnipro bridges damaged; "
         "nine dead."),
        ("LONDON", "LONDON AND BRUSSELS SIGN A RESET",
         "Britain and the EU agreed 100,000 youth visas in both "
         "directions, an end to food checks, a £17bn package and a "
         "British return to Erasmus+."),
        ("MARKETS", "AI SELLOFF ERASES $4 TRILLION",
         "The Nasdaq fell 5.3% in its worst week since 2020 as investors "
         "fled AI stocks. Anthropic dropped 8.5% the day after its "
         "market debut."),
        ("BELEM", "CLIMATE TALKS RUN PAST THE CLOCK, STILL NO DEAL",
         "The talks went into overtime with fossil fuels struck from "
         "the draft. A third draft is due Saturday, and Panama "
         "threatens to block it."),
        ("COPENHAGEN", "COPENHAGEN FOILS PLOT AGAINST UKRAINIAN RAPPER",
         "Danish police say they broke up a Russian plan to murder "
         "rapper Kyivstoner. A Russian envoy has seven days to "
         "leave the country."),
        ("MUSCAT", "TANKER SET ABLAZE OFF OMAN IN HORMUZ SCARE",
         "A projectile struck a tanker off Khasab and set it alight. "
         "The crew are safe, but the strait's shipping lanes are on "
         "edge again."),
    ]
    row_y = [518, 518]
    for i, (dl, hd, bd) in enumerate(stories):
        col = i % 2
        row_y[col] = story_block(cv, col_x[col], row_y[col], col_w, dl, hd,
                                 bd) + 9
    grid_bottom = max(row_y)
    rule(cv, grid_bottom + 2, 2)

    # --- in brief ----------------------------------------------------------
    fy = grid_bottom + 11
    draw_text(cv, MARGIN, fy, "IN BRIEF", 14, ACCENT, thick=3)
    briefs = [
        "LIMA — Magnitude 6.8 quake deep under Junin; Lima empties into streets, none hurt.",
        "JAIPUR — Congress takes 33 of 37 seats in Rajasthan as Modi opens SCO forum.",
        "WASHINGTON — Shutdown looms as Congress splits over $350bn for the Iran war.",
        "SCIENCE — Two rival claims to a Riemann hypothesis proof land in a single week.",
        "SPORT — Lauren Price is the first Welsh boxer to hold every belt at once.",
        "HEALTH — Measles cases in the United States climb towards 6,000 this year.",
        "NEW YORK — Mamdani vows Rikers shut by 2032; Pentagon airs fresh UFO film.",
    ]
    byy = fy + 20
    for b in briefs:
        for ln in wrap(b, 11, PAGE_W):
            draw_text(cv, MARGIN, byy, ln, 11, INK, thick=2)
            byy += 13
    rule(cv, H - 30, 2)
    draw_text(cv, W // 2, H - 22, "SET IN CODE · DRAWN BY PROGRAM · NO PHOTOGRAPHS",
              10, FAINT, thick=2, align="center")
    return cv


def main():
    data = encode_png(compose())
    out = Path("/output/entry.png")
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    except OSError:
        pass
    Path(__file__).with_name("entry.png").write_bytes(data)
    print("entry.png:", len(data), "bytes")


if __name__ == "__main__":
    main()
