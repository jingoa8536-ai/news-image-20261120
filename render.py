"""Typeset the fixed 20 November 2026 front page with Pillow."""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SIZE = 1024
MARGIN = 48
PAGE = (MARGIN, MARGIN, SIZE - MARGIN, SIZE - MARGIN)
PAPER, INK, RED, BLUE, GREY = "#f6f1e7", "#16191d", "#b0232a", "#33566b", "#686963"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
TRANSFORM = getattr(Image, "Transform", Image)
RESAMPLING = getattr(Image, "Resampling", Image)
SERIF = "DejaVuSerif-Bold"
BOLD = "DejaVuSans-Bold"
SANS = "DejaVuSans"
ITALIC = "DejaVuSans-Oblique"

GRID = (
    (
        "DIPLOMACY",
        "Trump, Xi, Putin Sign Peace\nPledge in Shenzhen",
        "The first three-way summit ended in a four-point\n"
        "declaration on nuclear risk, UN reform and energy —\n"
        "silent on Ukraine and Iran.",
    ),
    (
        "MARKETS",
        "Anthropic Soars 17% in\nRecord Nasdaq Debut",
        "Shares opened at $111.50 against an $83 offer price, but AI doubts "
        "dragged world stocks lower; the Nikkei fell 4.8%.",
    ),
    (
        "INDIA — WEATHER",
        "Cyclone Akvan Slams\nthe Odisha Coast",
        "The third cyclone in a month came ashore near Gopalpur with gusts "
        "to 100 km/h; about 300,000 people were evacuated.",
    ),
    (
        "JUSTICE — THE HAGUE",
        "World Court: Myanmar\nCommitted Genocide",
        "The ICJ ruled that Myanmar's campaign against the Rohingya was "
        "genocide — its first such finding against a state.",
    ),
)


def contains(outer, inner):
    return (outer[0] <= inner[0] < inner[2] <= outer[2]
            and outer[1] <= inner[1] < inner[3] <= outer[3])


def overlaps(a, b):
    return (max(a[0], b[0]) < min(a[2], b[2])
            and max(a[1], b[1]) < min(a[3], b[3]))


@lru_cache(maxsize=None)
def font_for(face, size):
    path = FONT_DIR / f"{face}.ttf"
    synthetic = face == ITALIC and not path.is_file()
    if synthetic:
        path = FONT_DIR / f"{SANS}.ttf"
    return ImageFont.truetype(str(path), size), synthetic


def line_mask(text, font, synthetic):
    """Return an exact ink mask and its top offset from the baseline."""
    left, top, right, bottom = font.getbbox(text, anchor="ls")
    height = bottom - top
    pad = (height + 3) // 4 + 2 if synthetic else 0
    mask = Image.new("L", (right - left + pad, height))
    ImageDraw.Draw(mask).text((-left, -top), text, font=font, fill=255, anchor="ls")
    if synthetic:
        mask = mask.transform(mask.size, TRANSFORM.AFFINE,
                              (1, .23, -.23 * height, 0, 1, 0),
                              resample=RESAMPLING.BICUBIC)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError(f"No visible glyphs in {text!r}")
    return mask.crop(bounds), top + bounds[1]


def wrap(text, font, width):
    lines = []
    for paragraph in text.splitlines():
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}" if line else word
            left, _, right, _ = font.getbbox(candidate)
            if line and right - left > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


class FrontPage:
    def __init__(self):
        self.image = Image.new("RGB", (SIZE, SIZE), PAPER)
        self.draw = ImageDraw.Draw(self.image)
        self.text_rectangles = []

    def text(self, copy, box, face, size, *, color=INK, align="left",
             wrap_words=False, min_size=11, valign="top"):
        if not contains(PAGE, box):
            raise ValueError(f"Text box outside the {MARGIN}px margin: {copy!r} {box}")
        x0, y0, x1, y1 = box
        width, height = x1 - x0, y1 - y0

        for points in range(size, min_size - 1, -1):
            font, synthetic = font_for(face, points)
            lines = wrap(copy, font, width) if wrap_words else copy.splitlines()
            pitch = (points * 6 + 4) // 5
            masks = []
            for index, line in enumerate(lines):
                mask, baseline_offset = line_mask(line, font, synthetic)
                masks.append((mask, index * pitch + baseline_offset))
            top = min(y for _, y in masks)
            bottom = max(y + mask.height for mask, y in masks)
            if bottom - top <= height and all(mask.width <= width for mask, _ in masks):
                break
        else:
            raise ValueError(f"Unable to fit {copy!r} in {box} at {min_size}px or larger")

        origin_y = y0 - top
        if valign == "center":
            origin_y += (height - (bottom - top)) // 2
        for line, (mask, offset) in zip(lines, masks):
            x = {"left": x0, "center": x0 + (width - mask.width) // 2,
                 "right": x1 - mask.width}[align]
            y = origin_y + offset
            rect = (x, y, x + mask.width, y + mask.height)
            if not contains(box, rect) or not contains(PAGE, rect):
                raise AssertionError(f"Text escaped its box or the page margin: {line!r} {rect}")
            for previous, previous_rect in self.text_rectangles:
                if overlaps(rect, previous_rect):
                    raise AssertionError(f"Text overlaps: {line!r} {rect} and "
                                         f"{previous!r} {previous_rect}")
            self.text_rectangles.append((line, rect))
            self.image.paste(color, (x, y), mask)

    def rule(self, y, color=INK, width=1):
        self.draw.line((48, y, 975, y), fill=color, width=width)


def bridge_band():
    """Draw the schematic at triple resolution for smooth edges."""
    width, height, scale = 928, 137, 3
    art = Image.new("RGB", (width * scale, height * scale), "#e3e9e7")
    draw = ImageDraw.Draw(art)

    def polygon(points, color):
        draw.polygon([(x * scale, y * scale) for x, y in points], fill=color)

    def line(points, color, weight=1):
        draw.line([(x * scale, y * scale) for x, y in points],
                  fill=color, width=weight * scale, joint="curve")

    def curve(points):
        a, b, c, d = points
        return [tuple(((32 - t) ** 3 * a[i] + 3 * (32 - t) ** 2 * t * b[i]
                       + 3 * (32 - t) * t ** 2 * c[i] + t ** 3 * d[i]) / 32 ** 3
                      for i in (0, 1)) for t in range(33)]

    upper_bank = ((0, 39), (211, 5), (527, 96), (928, 49))
    lower_bank = ((0, 119), (274, 88), (593, 166), (928, 116))
    polygon(curve(upper_bank) + curve(lower_bank)[::-1], BLUE)
    for shift, color in ((10, "#91a7b2"), (20, "#678596"), (48, "#678596"),
                         (58, "#91a7b2")):
        line(curve(tuple((x, y + shift) for x, y in upper_bank)), color)

    for center, deck_y, strike in ((171, 56, -35), (462, 62, 29), (753, 65, -16)):
        half_span = 91
        left, right = center - half_span, center + half_span
        arch = curve(((left + 11, deck_y + 48), (center - 39, deck_y - 9),
                      (center + 39, deck_y - 9), (right - 11, deck_y + 48)))
        for x in (left + 11, right - 11):
            line(((x, deck_y), (x, deck_y + 56)), "#223c4d", 9)
        line(arch, "#223c4d", 12)
        line(arch, PAPER, 6)
        line(((left, deck_y + 3), (right, deck_y + 3)), "#223c4d", 10)
        line(((left, deck_y), (right, deck_y)), PAPER, 5)
        for x in (left + 32, center, right - 32):
            end = deck_y + (9 if x == center else 21)
            line(((x, deck_y + 3), (x, end)), PAPER, 2)

        x, y = center + strike, deck_y - 5
        burst = ((0, -19), (4, -7), (15, -11), (8, -2), (20, 3), (7, 6),
                 (11, 17), (1, 11), (-6, 19), (-7, 8), (-19, 10), (-11, 1),
                 (-18, -8), (-6, -6))
        polygon([(x + dx, y + dy) for dx, dy in burst], RED)
        polygon(((x, y - 4), (x + 5, y + 1), (x, y + 6), (x - 5, y + 1)), PAPER)

    return art.resize((width, height), RESAMPLING.LANCZOS)


def render():
    page = FrontPage()
    text = page.text
    page.rule(49, RED, 3)
    text("THE WORLD IN ONE DAY", (48, 61, 976, 126), SERIF, 69, align="center")
    page.rule(133, INK, 2)
    text("FRIDAY · 20 NOVEMBER 2026", (48, 143, 430, 162), BOLD, 15, color=BLUE)
    text("The day in full — six stories, one page", (512, 142, 976, 162), ITALIC,
         16, color=GREY, align="right")
    page.rule(167, GREY)

    text("UKRAINE — THE WAR", (48, 183, 976, 203), BOLD, 16, color=RED)
    text("Missiles Shatter Kyiv's Bridges", (48, 211, 976, 263), SERIF, 57)
    text("Russia's biggest barrage of the war — nearly 100 missiles and some 400 drones — "
         "smashed three bridges over the Dnipro, killed three people and cut power across the capital.",
         (48, 274, 976, 320), SANS, 22, wrap_words=True)
    page.image.paste(bridge_band(), (48, 328))
    text("The Podilsko-Voskresenskyi, Darnytskyi and Pivdennyi bridges were all hit before dawn.",
         (48, 473, 976, 492), ITALIC, 15, color=GREY)

    for y in (501, 649, 797):
        page.rule(y, INK if y != 649 else GREY)
    page.draw.line((511, 512, 511, 639), fill=GREY)
    page.draw.line((511, 659, 511, 786), fill=GREY)
    for index, (kicker, headline, deck) in enumerate(GRID):
        left, right = ((48, 490), (533, 976))[index % 2]
        y = (512, 660)[index // 2]
        text(kicker, (left, y, right, y + 16), BOLD, 14, color=RED)
        text(headline, (left, y + 23, right, y + 83), SERIF, 28)
        text(deck, (left, y + 87, right, y + 132), SANS, 16, wrap_words=True)

    page.draw.rectangle((48, 807, 975, 897), fill="#e8e9e1")
    page.draw.rectangle((48, 807, 52, 897), fill=RED)
    text("MIDDLE EAST", (64, 816, 960, 831), BOLD, 14, color=RED)
    text("Houthi Missile Damages Riyadh's PIF Tower", (64, 836, 960, 862), SERIF, 29)
    text("Missiles struck the Saudi capital's financial district as the Iran war ground into its ninth month;\n"
         "President Trump deferred any new strikes to next year.",
         (64, 865, 960, 893), SANS, 15, wrap_words=True)

    page.draw.rectangle((48, 905, 975, 950), fill="#000000")
    text("KENYA DISCHARGES ITS LAST EBOLA PATIENT · TWO TRAINS COLLIDE IN PRAGUE — 46 HURT ·\n"
         "GAZA TANKS CROSS THE YELLOW LINE · GOLD FALLS 5%",
         (60, 908, 964, 948), BOLD, 15, color=PAPER, align="center", valign="center")
    text("Compiled from Reuters, One Turn, Citizen's Daily Brief and The Wire Post — 20 November 2026.",
         (48, 959, 976, 976), SANS, 13, color=GREY, align="center")

    output = Path(__file__).resolve().with_name("frontpage.png")
    page.image.save(output, optimize=True)
    data = output.read_bytes()
    if len(data) > 1024 ** 2:
        raise ValueError(f"{output.name} exceeds 1 MiB: {len(data)} bytes")
    print(f"{output.name}: {len(data)} bytes")
    print(f"sha256: {sha256(data).hexdigest()}")


if __name__ == "__main__":
    render()
