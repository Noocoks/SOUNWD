from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
S = 512
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

# Rounded charcoal app tile and restrained crimson ring.
d.rounded_rectangle((8, 8, 504, 504), radius=104, fill="#080808")
d.ellipse((38, 38, 474, 474), outline="#3D000D", width=12)

# Headphone band and ear cups.
d.arc((112, 70, 400, 365), 180, 360, fill="#858B93", width=25)
d.rounded_rectangle((82, 218, 163, 360), radius=25, fill="#790018", outline="#B5BAC0", width=9)
d.rounded_rectangle((349, 218, 430, 360), radius=25, fill="#790018", outline="#B5BAC0", width=9)

# Angular skull silhouette.
skull = [(171,183),(214,137),(254,164),(298,134),(346,178),(378,243),
         (361,317),(314,369),(300,417),(212,417),(197,369),(151,317),(134,243)]
d.polygon(skull, fill="#D8DADD")
d.line(skull + [skull[0]], fill="#B5BAC0", width=10, joint="curve")

# Deep red eye sockets, nasal cavity, and teeth.
d.polygon([(166,239),(232,212),(222,269),(174,278)], fill="#790018")
d.polygon([(280,212),(347,239),(339,278),(290,269)], fill="#790018")
d.polygon([(240,302),(272,302),(256,339)], fill="#3D000D")
d.line((205,369,307,369), fill="#3D000D", width=10)
for x in (222,245,268,291):
    d.line((x,369,x,397), fill="#3D000D", width=9)

# Small aggressive accents.
d.line((118,159,156,190), fill="#790018", width=13)
d.line((394,159,356,190), fill="#790018", width=13)
d.line((220,82,245,112), fill="#790018", width=13)
d.line((292,82,267,112), fill="#790018", width=13)

png = ROOT / "sounwd.png"
ico = ROOT / "sounwd.ico"
im.save(png)
im.convert("RGB").save(ico, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(f"Generated {png} and {ico}")
