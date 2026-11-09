"""Verify platform icon derivatives are reproducible from the canonical PNG."""
from pathlib import Path
from PIL import Image, ImageChops
import runpy

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "assets" / "build_brand_assets.py"), run_name="__main__")
master = Image.open(ROOT / "assets" / "sounwd.png").convert("RGBA")
generated = ROOT / "assets" / "generated"
for size in (16,24,32,48,64,96,128,192,256,512):
    image = Image.open(generated / "linux" / f"{size}x{size}" / "sounwd.png").convert("RGBA")
    assert image.size == (size,size), (size,image.size)
    expected = master.resize((size,size), Image.Resampling.LANCZOS)
    assert ImageChops.difference(image, expected).getbbox() is None, size
ico = Image.open(ROOT / "assets" / "sounwd.ico")
assert ico.format == "ICO"
android = ROOT / "android" / "assets" / "generated" / "android"
for name in ("icon.png","foreground.png","background.png","brand.png"):
    assert (android / name).is_file(), name
assert Image.open(android / "brand.png").convert("RGBA").size == master.size
assert Image.open(android / "icon.png").size == (512,512)
spec = (ROOT / "android" / "buildozer.spec").read_text(encoding="utf-8")
for setting in (
    "icon.filename = assets/generated/android/icon.png",
    "icon.adaptive_foreground.filename = assets/generated/android/foreground.png",
    "icon.adaptive_background.filename = assets/generated/android/background.png",
):
    assert setting in spec, setting
main = (ROOT / "android" / "main.py").read_text(encoding="utf-8")
assert 'self.label("◖♪"' not in main
assert 'generated" / "android" / "brand.png' in main
assert "BG=(9/255,9/255,11/255,1)" in main
assert "LAVENDER=(178/255,15/255,50/255,1)" in main
print("SOUNWD brand assets verified: ICO, Linux PNG set, Android launcher/adaptive and in-app logo.")
