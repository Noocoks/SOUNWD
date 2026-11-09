"""Create SOUNWD's branded, dark-crimson PyInstaller startup screen."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sounwd.png"
TARGET = ROOT / "sounwd-splash.png"

if not SOURCE.is_file():
    raise FileNotFoundError(f"Canonical SOUNWD logo not found: {SOURCE}")

WIDTH, HEIGHT = 620, 380
BG = "#09090B"
PANEL = "#111115"
RED = "#B20F32"
RED_DARK = "#451323"
WHITE = "#F0F0F2"
MUTED = "#858A94"
LINE = "#292930"

image = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((2, 2, WIDTH - 3, HEIGHT - 3), radius=22,
                       fill=PANEL, outline=RED_DARK, width=2)
draw.rounded_rectangle((17, 17, WIDTH - 18, HEIGHT - 18), radius=16,
                       outline=LINE, width=1)
draw.rounded_rectangle((30, 31, 35, HEIGHT - 31), radius=2, fill=RED)
draw.line((56, 62, WIDTH - 56, 62), fill=LINE, width=1)
draw.line((56, 310, WIDTH - 56, 310), fill=LINE, width=1)


def load_font(size: int, bold: bool = False):
    candidates = (
        ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]
        if bold else ["C:/Windows/Fonts/arial.ttf"]
    )
    candidates += (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def centered(text: str, y: int, font, color: str):
    bounds = draw.textbbox((0, 0), text, font=font)
    x = (WIDTH - (bounds[2] - bounds[0])) // 2
    draw.text((x, y), text, font=font, fill=color)


small = load_font(10, True)
medium = load_font(12, True)
large = load_font(34, True)

draw.text((56, 39), "NOOCOKS  /  DESKTOP AUDIO", font=small, fill=MUTED)
draw.text((WIDTH - 116, 39), "BUILD 01", font=small, fill=RED)

with Image.open(SOURCE) as source:
    logo = source.convert("RGBA")
    logo.thumbnail((142, 142), Image.Resampling.LANCZOS)
    image.paste(logo, ((WIDTH - logo.width) // 2, 76), logo)

centered("S O U N W D  //", 224, large, WHITE)
centered("UNDERGROUND AUDIO DIVISION", 270, medium, MUTED)

# Static segmented motif; PyInstaller overlays its live startup status text below.
bar_left, bar_top, bar_right = 112, 322, 508
draw.rounded_rectangle((bar_left, bar_top, bar_right, bar_top + 5),
                       radius=2, fill=LINE)
for index in range(12):
    x = bar_left + 3 + index * 32
    draw.rounded_rectangle((x, bar_top + 1, x + 18, bar_top + 4),
                           radius=1, fill=RED if index < 4 else RED_DARK)

image.save(TARGET, optimize=True)
print(f"Generated {TARGET}")
