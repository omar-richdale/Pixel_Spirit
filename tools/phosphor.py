#!/usr/bin/env python3
"""idcard.py - turn a photo into a green-phosphor terminal identity card.

    pip install pillow numpy
    python idcard.py                 # asks for the photo and every field
    python idcard.py me.jpg          # asks only for the fields
    python idcard.py me.jpg --defaults --name "Omar" -o card.png

Each question shows a few suggestions. Press Enter to take the first one,
type its number, type your own text, "?" for new suggestions, or "-" to
leave the field off the card.

The output is always 1280x720, the layout of the classic "wanted" terminal
screen: title line on top, portrait on the left, framed text on the right.
The font (IBM VGA 8x16, the DOS text-mode font) is embedded below, so the
script is a single file with nothing to download.
"""
import argparse
import base64
import getpass
import random
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

try:                      # nicer line editing where available
    import readline       # noqa: F401
except ImportError:
    pass

# --------------------------------------------------------------- font -----
# IBM VGA 8x16 ROM font, code page 437: 256 glyphs x 16 rows x 8 bits.
# Raw dump from github.com/viler-int10h/vga-text-mode-fonts (PC-IBM/VGA8.F16).
FONT = """
eNp9Vz9rI0cUXxzYatE53RALu7niyiUBewmLBEe+QppUy13YXDEEVYogy9658Xdwky5NvoNByGFJ
sbgUC1KEK6k5jCDgU2Fm8978fTPn5MlG+u28mff/zdsoCqm+/P3y8ub68rLWuF/1/e2u72vDwQVQ
lR0bfJxVFLI83+12jOUW17DZYcXC1K9e0u4WBSDJh3n5+nWZu/Xb65ub61u9fjr46utZCzSLNDNQ
zkCAwuNvxinQZH+v8Pu3798C/bTbzrVwtsp3+Urzf5jf7w/isL+ff5D4KB6cjsTodBAfWfUZY7VR
OCoVwbc+f7Va/XqCJGHVFBlvGp4lTUW8ii4LzqspRjLqSXIC4VEiEkYOSwtRpDRm8/lcEPiKC/7K
weMsqyohiC5Vlbl4BQSxyVEZrQ+Y+tJn4HC6/FfaVs1iXsXxVVMZCxZNwtKiuVIo4zybriFeU6V7
mhbeccAriSXaOJZIYs7CMu/zkqrook2ekQ2ReMYuu+MoRv10vCOM1nKJEdN82UxHINIBVeyNsDjO
4zg24U2GOW8FKHyqRUMwnsh6VgBugDQWsF/ZbM6DJbKOv2vYn8w8zYnBGhtzpXrgtdiVsPwzJNeQ
x56fkPjKB5vNZj2vTLaAQwQqpPATZECFGf9k6m0BFs4XukCjA1cFwQ/avvLNu9m74k0pPFwUe7J/
0zTltwqjJClOy8t1AZh+cSqzwdX7FkTNZiB0q/C+kGTlNQ9CLMl5zfZRbO4clr4m/pb2FU4/vb7c
VMnArqONW7teZEls99f1D56+TXC+RtwUnDx8uRQP3GAO1Vhxo59qZ+480Vxh8BYm//JUk+mn0MEm
2dD2qzzRlJtoRv9FPZYj+/z5LKlsvUb3RTGTIXbtrGogAYx9Q5DEW8cv14Vbz/iPxZ74F2iK7G2V
yJDC+XxaOv9CXmbUn3EcDWJJpUw54FcJoPmzIF+APgpw8NLZvdYt2+lH4mPXK6ui0c+U9Hpaevpj
j7ft/ThNnzAc50O7LrcTf5QqpharBOAO8yyjcVIZU8eJKakW+6mO/wBMnaC9A3dfROT+wDXkYRNt
zDoMr6xwc5yuZyjnJJYWtb7+2IdpPGGznx+tny/QbTycQV/1+FEihBDEmQT186Xx8wfP89bLyMsP
BjcDxchPceMamlGHYmyLoiwg9qW7M9rped11PyswguQW6I+7yOlL69vPJ6Wvw+ms9fyJ615+NCTe
M4SV1z+ayO8nYBcmI7YIv7y2TybZcBiqTT4c2vbwZ7sBeSq/BidMXp9A3UQ7gMYH4+35F9apPYg9
/SG/SH0Bsg1XBZvzEb2NcByI6GQE92CK1ysdl/AOndPpCcvfjDqLBsthDV1x5HB599tIsahqyHNS
b+e84+fkOEC8Uz+//M7/fP+H//n7F//DnqdDgCw+V/Sov40WwsMh/2Ns+UPS7vDXH2Obu/qJIGOR
1CdoAYdA/zOPn7E+vClCfubNrFEf7g+4zwJ/XHj6X6RjT9o49dc/RX1wb30K9l94/ukdv95v+bV1
feCv8Pw+tC8Iw9iz98z5T9LZZ/4ZB/t7Xx8W+jeMlz2vDyiir1FA+4BeBORvM/fxuuu6ta5nfLfq
Wijf1swfeNvTgsTxH8nABnqau59wJOqQJt71Bx12bsV5vqlZrt7gIjeQCzePy8sKxT3oeRDG2ZG8
UJ08eAVzLeaLGPA/tRE3TAts70U6jIIBkLwsCPrKoF8vjJP0+GybmB63DR6cnDzTEKj9cFhN53ds
kvZWlv3wf15WzAPz44Wc7T5yng91LyOhwOu/S4u//PSpFD07Av4LLXDb5Q==
"""
GLYPHS = np.unpackbits(
    np.frombuffer(zlib.decompress(base64.b64decode(FONT)), np.uint8).reshape(256, 16, 1),
    axis=2,
).astype(np.float32)                                   # (256, 16, 8)

# ------------------------------------------------------------- layout -----
S = 3                         # one font pixel = 3 screen pixels
W, H = 1280, 720
LW, LH = 427, 240             # the low-res "terminal" grid (x3 = screen)
TITLE_X, TITLE_Y = 23, 21
FRAME = (156, 403, 47, 217)   # x0, x1, top, bottom in grid pixels
PANEL_X = 172
PANEL_COLS = 28               # characters that fit on a panel line
TITLE_COLS = 47
ROW_PITCH = 18                # grid pixels between panel lines
GROUP_GAP = 10                # extra space between the two field groups
SLOT_X, SLOT_Y, SLOT_W, SLOT_ROWS = 72, 138, 318, 174   # portrait slot

# ------------------------------------------------------------- fields -----
# key, label, group, suggestion pool
FIELDS = [
    ("name", "Name", 0, ["Unknown Subject", "Citizen Zero", "Jane Doe", "John Doe"]),
    ("alias", "Alias", 0, ["Ghost", "null_pointer", "The Operator", "Root", "Static",
                           "Daemon", "Glitch", "Night Shift"]),
    ("class", "Class", 0, ["Netrunner", "Rogue Sysadmin", "Agent Wrangler", "Signal Smuggler",
                           "Kernel Whisperer", "Data Courier", "Orbital Mechanic", "Free Thinker"]),
    ("origin", "Origin", 0, ["Kepler-443b", "Proxima Centauri b", "Mars Colony 7", "Earth (Sol-3)",
                             "Titan Station", "Low Earth Orbit", "Unknown sector"]),
    ("clearance", "Clearance", 1, ["Level 7 / Root", "Omega Black", "Sudo, no password", "Read-only",
                                   "Eyes Only", "Revoked", "Classified"]),
    ("talent", "Talent", 1, ["Fluent in Bash", "Sees the Matrix", "Never sleeps", "Exits Vim unaided",
                             "Talks to machines", "Reads raw hex", "Regex from memory",
                             "Breaks prod Fridays"]),
    ("status", "Status", 1, ["Active", "At Large", "Off the grid", "Under observation",
                             "Rebooting", "Do not approach"]),
]
CARD_TYPES = ["Identity Card", "Citizen Record", "Access Pass", "Crew Manifest", "Operator License"]
TYPE_MAX, ID_MAX = 24, 20


def random_ids(rng):
    L = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    return [
        f"{rng.choice(L)}{rng.randint(1, 9)}-{rng.randint(10000, 99999)}",
        f"{rng.choice(L)}{rng.choice(L)}-{rng.randint(1000, 9999)}-{rng.choice(L)}",
        f"0x{rng.randint(0x100000, 0xFFFFFF):06X}",
        f"{rng.randint(100, 999)}-{rng.randint(100, 999)}-{rng.randint(10, 99)}",
    ]


# ------------------------------------------------------------- dialog -----
def unsupported(text):
    """Characters the DOS font has no glyph for."""
    bad = []
    for ch in text:
        try:
            ch.encode("cp437")
        except UnicodeEncodeError:
            bad.append(ch)
    return bad


def check(text, max_len):
    """Return an error message for a value, or None if it fits the card."""
    if len(text) > max_len:
        return f"too long by {len(text) - max_len} (max {max_len} characters)"
    bad = unsupported(text)
    if bad:
        return "this font has no glyph for: " + " ".join(dict.fromkeys(bad))
    return None


def read_line(prompt):
    try:
        return input(prompt).strip()
    except EOFError:          # input closed: take the default from here on
        print()
        return ""


def ask(label, pool, max_len, rng, first=None, skippable=True, fixed=False):
    """Ask one question. Returns the chosen text, or None if skipped."""
    pool = [p for p in pool if len(p) <= max_len]

    def pick():
        rest = [p for p in pool if p != first]
        if not fixed:
            rng.shuffle(rest)
        return ([first] if first else []) + rest[: 4 - bool(first)]

    options = pick()
    while True:
        print(f"\n{label}  (max {max_len} characters)")
        for i, s in enumerate(options, 1):
            print(f"   {i}) {s}")
        hint = "Enter = 1, a number, your own text" + ("" if fixed else ", ? = more ideas")
        hint += ", - = leave out" if skippable else ""
        raw = read_line(f"   [{hint}]\n > ")
        if not raw:
            return options[0]
        if raw == "?" and not fixed:
            first = None
            options = pick()
            continue
        if raw == "-" and skippable:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        problem = check(raw, max_len)
        if problem:
            print(f"   ! {problem}")
            continue
        return raw


def choose(label, options, default=0):
    """Pick one of a few named options; returns the option key."""
    print(f"\n{label}")
    for i, (_, text) in enumerate(options, 1):
        print(f"   {i}) {text}")
    while True:
        raw = read_line(f"   [Enter = {default + 1}, or a number]\n > ").lower()
        if not raw:
            return options[default][0]
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][0]
        for key, _ in options:
            if raw == key:
                return key
        print("   ! pick one of the numbers")


def clean_path(raw):
    """Accept quoted, drag-and-dropped and ~ paths."""
    raw = raw.strip().strip("\"'")
    if raw.startswith("file://"):
        raw = raw[7:]
    p = Path(raw).expanduser()
    if not p.exists() and "\\ " in raw:
        p = Path(raw.replace("\\ ", " ")).expanduser()
    return p


def ask_image():
    while True:
        raw = read_line("\nPath to the photo\n > ")
        if not raw:
            if not sys.stdin.isatty():
                sys.exit("No image given.")
            continue
        p = clean_path(raw)
        if p.is_file():
            return p
        print(f"   ! no file at {p}")


# ------------------------------------------------------------ drawing -----
def put_text(grid, x, y, text):
    for i, code in enumerate(text.encode("cp437", "replace")):
        cx = x + i * 8
        if cx + 8 > grid.shape[1]:
            break
        cell = grid[y:y + 16, cx:cx + 8]
        np.maximum(cell, GLYPHS[code], out=cell)


def draw_text_layer(title, rows):
    """rows: list of (group, text). Returns the full-size brightness layer."""
    grid = np.zeros((LH, LW), dtype=np.float32)
    put_text(grid, TITLE_X, TITLE_Y, title)

    x0, x1, yt, yb = FRAME
    grid[yt:yt + 2, x0:x1] = 1
    grid[yb:yb + 2, x0:x1] = 1
    grid[yt:yt + 13, x0:x0 + 2] = 1
    grid[yt:yt + 13, x1 - 2:x1] = 1
    grid[yb - 8:yb + 2, x0:x0 + 2] = 1
    grid[yb - 8:yb + 2, x1 - 2:x1] = 1

    # stack the lines, add a gap where the group changes, centre vertically
    ys, y = [], 0
    for i, (group, _) in enumerate(rows):
        if i and group != rows[i - 1][0]:
            y += GROUP_GAP
        ys.append(y)
        y += ROW_PITCH
    block = (ys[-1] + 16) if ys else 0
    top = yt + 2 + ((yb - yt - 2) - block) // 2
    for (_, text), dy in zip(rows, ys):
        put_text(grid, PANEL_X, top + dy, text)

    return np.kron(grid, np.ones((S, S), dtype=np.float32))[:H, :W]


# ----------------------------------------------------------- portrait -----
LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


def find_plain_background(img):
    """Find a plain, light backdrop (a wall, a studio sweep).

    Returns (mask, backdrop brightness) at reduced size, or (None, None) when
    the backdrop is dark, busy, or cannot be told apart from the subject.
    """
    small = img.copy()
    small.thumbnail((256, 256), Image.BILINEAR)
    rgb = np.asarray(small, dtype=np.float32) / 255
    h, w, _ = rgb.shape
    lum = rgb @ LUMA

    top, side = max(2, h // 30), max(2, w // 30)
    border = np.concatenate([
        rgb[:top].reshape(-1, 3),
        rgb[: int(h * 0.6), :side].reshape(-1, 3),
        rgb[: int(h * 0.6), -side:].reshape(-1, 3),
    ])
    b_lum = border @ LUMA
    l0 = float(np.median(b_lum))
    if l0 < 0.35 or float(np.std(b_lum)) > 0.17:
        return None, None

    def chroma(a):
        return a / (a.sum(axis=-1, keepdims=True) + 1e-6)

    c0 = np.median(chroma(border), axis=0)
    spread = float(np.percentile(np.linalg.norm(chroma(border) - c0, axis=1), 90))
    if spread > 0.03:
        return None, None

    cand = (np.linalg.norm(chroma(rgb) - c0, axis=2) < max(0.045, 3.5 * spread)) & (lum > 0.55 * l0)

    # keep only what is connected to the picture border
    m = Image.fromarray(np.pad(cand, 1, constant_values=True).astype(np.uint8) * 255).copy()
    ImageDraw.floodfill(m, (0, 0), 128)
    bg = np.asarray(m)[1:-1, 1:-1] == 128

    # backdrop seen through gaps in hair sits next to the outline: take it too
    for _ in range(4):
        near = np.asarray(Image.fromarray(bg.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
        bg |= cand & near

    if not 0.08 < bg.mean() < 0.90:
        return None, None
    return bg, l0


def choose_crop(size, bg, framing):
    """Pick the part of the photo that goes into the portrait slot."""
    iw, ih = size
    aspect = SLOT_W / (SLOT_ROWS * S)
    cover_w = min(iw, ih * aspect)
    zoom = {"auto": 1.0, "wide": 0.78, "tight": 1.3}[framing]

    cw, cx, top = cover_w, iw / 2, None
    if bg is not None:
        subj = ~bg
        mh, mw = subj.shape
        rows = np.where(subj.sum(axis=1) > 0.02 * mw)[0]
        if len(rows):
            r0 = rows[0]
            band = subj[r0: r0 + max(1, int((mh - r0) * 0.40))]
            xs = [np.where(r)[0] for r in band if r.any()]
            if xs:
                widths = np.array([x[-1] - x[0] + 1 for x in xs])
                centres = np.array([(x[-1] + x[0]) / 2 for x in xs])
                head_w = float(np.percentile(widths, 90)) * iw / mw
                cw = head_w * 1.08
                cx = float(np.median(centres)) * iw / mw
                top = r0 * ih / mh

    cw = float(np.clip(cw / zoom, min(cover_w, 64), cover_w))
    ch = cw / aspect
    x0 = cx - cw / 2
    y0 = (top - 0.11 * ch) if top is not None else (ih - ch) * 0.42
    x0 = float(np.clip(x0, 0, iw - cw))
    y0 = float(np.clip(y0, 0, ih - ch))
    return tuple(int(round(v)) for v in (x0, y0, x0 + cw, y0 + ch))


def render_portrait(img, bg, l0, box, background, black, gamma, levels, rng):
    """Photo -> SLOT_ROWS x SLOT_W brightness array with true blacks."""
    crop = img.crop(box)
    gray = np.asarray(crop.convert("L"), dtype=np.float32) / 255

    alpha = None
    if bg is not None and background != "keep":
        m = Image.fromarray(bg.astype(np.uint8) * 255).resize(img.size, Image.BILINEAR).crop(box)
        m = m.filter(ImageFilter.GaussianBlur(max(1.0, crop.width / 300)))
        alpha = np.asarray(m, dtype=np.float32) / 255

    # stretch the subject's tones, sharpen a little
    sample = gray[alpha < 0.5] if alpha is not None and (alpha < 0.5).any() else gray
    lo, hi = np.percentile(sample, [1, 99.5])
    t = np.clip((gray - lo) / max(hi - lo, 1e-3), 0, 1)
    t_img = Image.fromarray((t * 255).astype(np.uint8))
    t_img = t_img.filter(ImageFilter.UnsharpMask(radius=max(2, crop.width // 80), percent=80, threshold=0))
    t = np.asarray(t_img, dtype=np.float32) / 255

    # crush the shadows: everything below `black` becomes exactly 0
    v = np.clip((t - black) / (1 - black), 0, 1) ** gamma

    if alpha is not None:
        if background == "dim":
            back = 0.30 * np.clip(gray / l0, 0.6, 1.15)
            v = v * (1 - alpha) + back * alpha
        else:                                   # "black"
            v = v * (1 - alpha)

    small = Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8)).resize((SLOT_W, SLOT_ROWS), Image.LANCZOS)
    p = np.asarray(small, dtype=np.float32) / 255

    # posterise; the noise only touches lit pixels, so black stays black
    lit = p > 0.5 / levels
    p = np.clip(p + rng.normal(0, 0.035, p.shape) * lit, 0, 0.999)
    p = np.floor(p * levels) / (levels - 1) * 0.92

    # ragged line ends, as if each line were drawn on its own
    for r in range(SLOT_ROWS):
        a, b = rng.integers(0, 5), rng.integers(0, 7)
        p[r, :a] = 0
        if b:
            p[r, -b:] = 0
    return p


# ---------------------------------------------------------------- CRT -----
def blur(a, radius):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255


def compose(text_layer, portrait, dots, amber=False):
    lum = text_layer.copy()
    port = np.repeat(portrait, S, axis=0)                 # one row -> one scan line
    slot = lum[SLOT_Y:SLOT_Y + port.shape[0], SLOT_X:SLOT_X + SLOT_W]
    np.maximum(slot, port, out=slot)

    scan = np.ones((H, 1), dtype=np.float32)
    scan[2::3] = 0.18                                     # one dark line in three
    lum *= scan

    if dots:
        layer = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(layer)
        for fx, fy in dots:
            cx, cy = SLOT_X + fx * SLOT_W, SLOT_Y + fy * SLOT_ROWS * S
            d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=255)
        layer = np.asarray(layer.filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32) / 255
        lum = np.maximum(lum, layer * 1.15)

    out = 0.65 * lum + 0.35 * blur(lum, 0.8)
    out = out + 0.55 * blur(lum, 4) + 0.35 * blur(lum, 14)   # phosphor glow

    base = np.clip(out, 0, 1)
    hot = np.clip(out - 0.85, 0, 0.4) / 0.4               # hottest spots drift to white
    r, g, b = (1.0, 0.62, 0.05) if amber else (0.10, 1.0, 0.06)
    rgb = np.stack([
        r * base + 0.55 * hot * (1 - r),
        g * base + 0.55 * hot * (1 - g),
        b * base + 0.40 * hot * (1 - b),
    ], axis=2)
    return Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))


# --------------------------------------------------------------- main -----
def parse_dot(text):
    try:
        x, y = (float(v) for v in text.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("use X,Y with both between 0 and 1, e.g. 0.33,0.31")
    return x, y


def main():
    ap = argparse.ArgumentParser(
        description="Turn a photo into a green-phosphor terminal identity card.",
        epilog="Fields you do not pass as options are asked for interactively.")
    ap.add_argument("image", nargs="?", help="photo to use (asked for if missing)")
    ap.add_argument("-o", "--output", help="output PNG (default: <photo>_idcard.png)")
    ap.add_argument("--defaults", action="store_true", help="no questions: take the first suggestion everywhere")
    g = ap.add_argument_group("card text ('-' leaves a field out)")
    g.add_argument("--type", dest="card_type", metavar="TEXT", help="title, e.g. 'Identity Card'")
    g.add_argument("--id", dest="card_id", metavar="TEXT", help="card number shown after the title")
    for key, label, _, _ in FIELDS:
        g.add_argument(f"--{key}", dest=f"f_{key}", metavar="TEXT", help=f"{label} line")
    g = ap.add_argument_group("portrait")
    g.add_argument("--background", choices=["auto", "dim", "black", "keep"], default=None,
                   help="what to do with a plain light backdrop (auto = dim it if one is found)")
    g.add_argument("--framing", choices=["auto", "wide", "tight"], default=None)
    g.add_argument("--black", type=float, default=0.16,
                   help="shadow cut-off 0..0.6; higher = more of the photo turns pure black (default 0.16)")
    g.add_argument("--gamma", type=float, default=0.85, help="<1 brightens midtones, >1 darkens (default 0.85)")
    g.add_argument("--levels", type=int, default=6, help="brightness steps (default 6)")
    g.add_argument("--dot", type=parse_dot, action="append", metavar="X,Y",
                   help="tracking dot position inside the portrait, 0..1 from its top-left; repeatable")
    g.add_argument("--no-dots", action="store_true", help="no tracking dots")
    g.add_argument("--amber", action="store_true", help="amber monitor instead of green")
    g.add_argument("--seed", type=int, help="fix the random suggestions and scan noise")
    a = ap.parse_args()

    if not 0 <= a.black <= 0.6:
        ap.error("--black must be between 0 and 0.6")
    if a.levels < 2:
        ap.error("--levels must be at least 2")

    rng = random.Random(a.seed)
    np_rng = np.random.default_rng(a.seed if a.seed is not None else 7)
    talk = not a.defaults

    if talk:
        print("=" * 56)
        print(" TERMINAL IDENTITY CARD")
        print(" Enter takes the first suggestion. Ctrl+C quits.")
        print("=" * 56)

    # ---- image
    if a.image:
        path = clean_path(a.image)
        if not path.is_file():
            sys.exit(f"No file at {path}")
    elif talk:
        path = ask_image()
    else:
        sys.exit("Give the photo path: python idcard.py photo.jpg --defaults")
    try:
        img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    except Exception as e:                                # not an image, unreadable, ...
        sys.exit(f"Could not open {path} as an image: {e}")

    # ---- title
    def from_flag(value, max_len, what):
        if value is None or value == "-":
            return value
        problem = check(value, max_len)
        if problem:
            sys.exit(f"{what}: {problem}")
        return value

    card_type = from_flag(a.card_type, TYPE_MAX, "--type")
    if card_type is None:
        card_type = ask("Card type", CARD_TYPES, TYPE_MAX, rng, first=CARD_TYPES[0], skippable=False) \
            if talk else CARD_TYPES[0]
    ids = random_ids(rng)
    card_id = from_flag(a.card_id, ID_MAX, "--id")
    if card_id is None:
        card_id = ask("Card number", ids, ID_MAX, rng, first=ids[0], fixed=True) if talk else ids[0]
    title = card_type if card_id in (None, "-") else f"{card_type}: {card_id}"

    # ---- fields
    try:
        user = getpass.getuser()
    except Exception:                                     # no login name available
        user = ""
    rows = []
    for key, label, group, pool in FIELDS:
        max_len = PANEL_COLS - len(label) - 2
        value = from_flag(getattr(a, f"f_{key}"), max_len, f"--{key}")
        if value is None:
            first = None
            if key == "name":
                nice = user.replace(".", " ").replace("_", " ").title()
                if nice and nice.lower() not in ("root", "admin", "user") and not check(nice, max_len):
                    first = nice
            if talk:
                value = ask(label, pool, max_len, rng, first=first or pool[0])
            else:
                value = first or pool[0]
        if value not in (None, "-"):
            rows.append((group, f"{label}: {value}"))

    # ---- portrait options
    bg, l0 = find_plain_background(img)
    background = a.background
    if background in (None, "auto"):
        if bg is None:
            background = "keep"
        elif talk and a.background is None:
            background = choose("The photo has a plain light backdrop. What should happen to it?", [
                ("dim", "dim it, so the outline of the head stays visible"),
                ("black", "remove it: only the lit parts of the subject remain"),
                ("keep", "keep it as bright as it is"),
            ])
        else:
            background = "dim"
    elif bg is None and background != "keep":
        print("Note: no plain light backdrop found in this photo, leaving it as it is.")
        background = "keep"

    framing = a.framing
    if framing is None:
        framing = choose("Framing of the portrait", [
            ("auto", "automatic"),
            ("tight", "closer in"),
            ("wide", "further out"),
        ]) if talk else "auto"

    if a.no_dots:
        dots = []
    elif a.dot:
        dots = a.dot
    else:
        dots = [(0.04, 0.24), (0.33, 0.31)]               # where the original has them
        if talk and choose("Glowing tracking dots on the portrait?", [("yes", "yes"), ("no", "no")]) == "no":
            dots = []

    # ---- render
    box = choose_crop(img.size, bg, framing)
    portrait = render_portrait(img, bg, l0, box, background, a.black, a.gamma, a.levels, np_rng)
    card = compose(draw_text_layer(title[:TITLE_COLS], rows), portrait, dots, a.amber)

    out = Path(a.output).expanduser() if a.output else path.with_name(path.stem + "_idcard.png")
    card.save(out)
    print(f"\nSaved {out}  ({card.width}x{card.height})")
    if talk:
        print("Too dark or too bright? Re-run with --black 0.08 (keeps more shadow detail)")
        print("or --black 0.25 (more pure black). See --help for the rest.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled.")