"""Generate the opaque, cross-platform PyInstaller boot splash from the canonical logo."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sounwd.png"
TARGET = ROOT / "sounwd-splash.png"

if not SOURCE.is_file():
    raise FileNotFoundError(f"Canonical SOUNWD logo not found: {SOURCE}")

W, H = 560, 340
image = Image.new("RGB", (W, H), "#080808")
draw = ImageDraw.Draw(image)

# Subtle industrial frame and crimson accent.
draw.rounded_rectangle((2, 2, W - 3, H - 3), radius=22, outline="#3D000D", width=3)
draw.rounded_rectangle((28, 26, W - 29, H - 27), radius=16, outline="#242424", width=1)

def font(size: int, bold: bool = False):
    candidates = (
        ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]
        if bold else ["C:/Windows/Fonts/arial.ttf"]
    ) + (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()

with Image.open(SOURCE) as logo:
    logo = logo.convert("RGBA")
    logo.thumbnail((112, 112), Image.Resampling.LANCZOS)
    image.paste(logo, ((W - logo.width) // 2, 42), logo)

title_font = font(31, True)
subtitle_font = font(11, True)
label_font = font(10, True)

def centered(text: str, y: int, selected_font, fill: str):
    bounds = draw.textbbox((0, 0), text, font=selected_font)
    draw.text(((W - (bounds[2] - bounds[0])) // 2, y), text,
              font=selected_font, fill=fill)

centered("SOUNWD //", 174, title_font, "#D8DADD")
centered("UNDERGROUND AUDIO DIVISION  •  NO COMFORT ZONE",
         218, subtitle_font, "#858B93")

# The bootloader updates the live status text below this animated-looking track
# as it extracts bundled files; the track itself stays neutral and unobtrusive.
draw.rounded_rectangle((105, 264, 455, 272), radius=4, fill="#242424")
for x in range(110, 450, 24):
    draw.rounded_rectangle((x, 265, x + 12, 271), radius=2, fill="#790018")
centered("INITIALIZING AUDIO ENGINE", 289, label_font, "#B5BAC0")

image.save(TARGET, optimize=True)
print(f"Generated {TARGET}")
