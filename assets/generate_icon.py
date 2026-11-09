"""Build the Windows ICO from the canonical PNG committed in this directory."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
png_path = ROOT / "sounwd.png"
ico_path = ROOT / "sounwd.ico"
if not png_path.is_file():
    raise FileNotFoundError(f"Canonical brand image is missing: {png_path}")
with Image.open(png_path) as source:
    source.convert("RGBA").save(
        ico_path, format="ICO",
        sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
    )
print(f"Generated {ico_path} from {png_path}")
