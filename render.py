"""Render the supplied 20 November 2026 news digest with Pillow."""

from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
PAPER = '#f6f1e7'
INK = '#16191d'
RED = '#b0232a'
BLUE = '#33566b'
GREY = '#686963'
image = Image.new('RGB', (1024, 1024), PAPER)
draw = ImageDraw.Draw(image)
regions = []


def font(name, size):
    path = FONT_DIR / (name + '.ttf')
    if not path.exists() and name == 'DejaVuSans-Oblique':
        path = FONT_DIR / 'DejaVuSans.ttf'
    return ImageFont.truetype(str(path), size)


def wrap(text, face, width):
    lines = []
    line = ''
    for word in text.split():
        candidate = f'{line} {word}'.strip()
        if draw.textbbox((0, 0), candidate, font=face)[2] > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def measure(text, name, size, width, max_lines=100):
    face = font(name, size)
    lines = wrap(text, face, width)
    step = size + max(2, round(size * .12))
    boxes = [draw.textbbox((0, 0), line, font=face) for line in lines]
    height = (len(lines) - 1) * step + max(b[3] - b[1] for b in boxes)
    fits = len(lines) <= max_lines and all(b[2] - min(0, b[0]) <= width for b in boxes)
    return face, lines, boxes, step, height, fits


def text_block(text, box, name, preferred, color=INK, max_lines=100, center=False):
    x, y, width, height = box
    for size in range(preferred, 6, -1):
        face, lines, boxes, step, used, fits = measure(text, name, size, width, max_lines)
        if fits and used <= height:
            break
    else:
        raise ValueError(f'Text cannot fit: {text}')
    for i, (line, bounds) in enumerate(zip(lines, boxes)):
        left = x + (width - (bounds[2] - bounds[0])) / 2 if center else x
        position = (left - bounds[0], y + i * step - bounds[1])
        actual = draw.textbbox(position, line, font=face)
        assert actual[0] >= x and actual[2] <= x + width, (text, actual, box)
        assert actual[1] >= y and actual[3] <= y + height, (text, actual, box)
        assert 48 <= actual[0] and actual[2] <= 976
        assert 48 <= actual[1] and actual[3] <= 976
        draw.text(position, line, font=face, fill=color)
        regions.append((actual, text))
    return used


def story(kicker, headline, deck, x, y, width, height):
    # Scale the whole story together so its hierarchy survives the tight grid.
    for scale in range(100, 35, -1):
        sizes = [round(n * scale / 100) for n in (20, 33, 22)]
        specifications = [(kicker, 'DejaVuSans-Bold', sizes[0], 1),
                          (headline, 'DejaVuSerif-Bold', sizes[1], 3),
                          (deck, 'DejaVuSans', sizes[2], 100)]
        measures = [measure(t, f, s, width, limit) for t, f, s, limit in specifications]
        if all(m[-1] for m in measures) and sum(m[4] for m in measures) + 14 <= height:
            break
    else:
        raise ValueError(f'Story cannot fit: {headline}')
    for (text, name, size, limit), measured, color in zip(
            specifications, measures, (RED, INK, INK)):
        used = text_block(text, (x, y, width, measured[4]), name, size, color, limit)
        y += used + 7


text_block('FRIDAY · 20 NOVEMBER 2026', (48, 48, 928, 18),
           'DejaVuSans-Bold', 17, center=True, max_lines=1)
text_block('THE WORLD IN ONE DAY', (48, 79, 928, 61),
           'DejaVuSerif-Bold', 88, center=True, max_lines=1)
draw.rectangle((48, 148, 976, 152), fill=INK)
text_block('The day in full — six stories, one page', (48, 164, 928, 23),
           'DejaVuSans-Oblique', 24, center=True, max_lines=1)

text_block('UKRAINE — THE WAR', (48, 205, 928, 18), 'DejaVuSans-Bold', 20, RED)
text_block("Missiles Shatter Kyiv's Bridges", (48, 237, 928, 105),
           'DejaVuSerif-Bold', 60, max_lines=2)
text_block("Russia's biggest barrage of the war — nearly 100 missiles and some 400 drones — "
           'smashed three bridges over the Dnipro, killed three people and cut power across the capital.',
           (48, 302, 928, 58), 'DejaVuSans', 25)

# A schematic river and three bridges; the impacts use fixed geometry.
draw.rectangle((48, 373, 976, 453), fill='#e8e3d9')
draw.rectangle((48, 390, 976, 437), fill=BLUE)
for cx in (220, 512, 804):
    draw.rectangle((cx - 60, 380, cx + 60, 443), fill=PAPER)
    draw.rectangle((cx - 48, 390, cx + 48, 437), fill=BLUE)
    draw.arc((cx - 49, 378, cx + 49, 436), 180, 360, fill=INK, width=4)
    draw.line((cx - 61, 412, cx + 61, 412), fill=INK, width=4)
    for dx in (-32, 0, 32):
        draw.line((cx + dx, 389 if dx else 381, cx + dx, 411), fill=INK, width=2)
    points = []
    for i in range(16):
        angle = i * math.pi / 8
        radius = 16 if i % 2 == 0 else 6
        points.append((cx + 23 + math.cos(angle) * radius, 397 + math.sin(angle) * radius))
    draw.polygon(points, fill=RED)
text_block('The Podilsko-Voskresenskyi, Darnytskyi and Pivdennyi bridges were all hit before dawn.',
           (48, 461, 928, 18), 'DejaVuSans', 19, max_lines=1)

draw.line((48, 491, 976, 491), fill=INK, width=2)
draw.line((512, 501, 512, 744), fill='#bab8af', width=1)
draw.line((48, 622, 976, 622), fill='#bab8af', width=1)
stories = [
    ('DIPLOMACY', 'Trump, Xi, Putin Sign Peace Pledge in Shenzhen',
     'The first three-way summit ended in a four-point declaration on nuclear risk, UN reform and energy — silent on Ukraine and Iran.'),
    ('MARKETS', 'Anthropic Soars 17% in Record Nasdaq Debut',
     'Shares opened at $111.50 against an $83 offer price, but AI doubts dragged world stocks lower; the Nikkei fell 4.8%.'),
    ('INDIA — WEATHER', 'Cyclone Akvan Slams the Odisha Coast',
     'The third cyclone in a month came ashore near Gopalpur with gusts to 100 km/h; about 300,000 people were evacuated.'),
    ('JUSTICE — THE HAGUE', 'World Court: Myanmar Committed Genocide',
     "The ICJ ruled that Myanmar's campaign against the Rohingya was genocide — its first such finding against a state."),
]
for i, contents in enumerate(stories):
    story(*contents, 48 + (i % 2) * 484, 503 + (i // 2) * 132, 444, 109)

draw.line((48, 756, 976, 756), fill=INK, width=2)
text_block('MIDDLE EAST', (48, 768, 928, 14), 'DejaVuSans-Bold', 17, RED)
text_block("Houthi Missile Damages Riyadh's PIF Tower", (48, 790, 928, 29),
           'DejaVuSerif-Bold', 36, max_lines=1)
text_block("Missiles struck the Saudi capital's financial district as the Iran war ground into its ninth "
           'month; President Trump deferred any new strikes to next year.',
           (48, 826, 928, 33), 'DejaVuSans', 23, max_lines=2)

draw.rectangle((48, 870, 976, 934), fill=INK)
text_block('KENYA DISCHARGES ITS LAST EBOLA PATIENT · TWO TRAINS COLLIDE IN PRAGUE — 46 HURT · '
           'GAZA TANKS CROSS THE YELLOW LINE · GOLD FALLS 5%',
           (61, 878, 902, 48), 'DejaVuSans-Bold', 21, PAPER, max_lines=2, center=True)
text_block("Compiled from Reuters, One Turn, Citizen's Daily Brief and The Wire Post — 20 November 2026.",
           (48, 943, 928, 20), 'DejaVuSans', 17, GREY, max_lines=1, center=True)

# Check the actual glyph rectangles across every text block before writing.
for i, (a, label) in enumerate(regions):
    for b, other in regions[i + 1:]:
        assert not (a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]), (label, other)
image.save(ROOT / 'frontpage.png', optimize=True)
print('Rendered frontpage.png; all text bounds and overlap checks passed.')
