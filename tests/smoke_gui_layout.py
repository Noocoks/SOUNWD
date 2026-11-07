"""Desktop GUI layout smoke test: verify the main block is vertically centered."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gui import SoundwApp


app = SoundwApp()
try:
    app.geometry("900x820")
    app.update()
    app.update_idletasks()
    app.update()

    top_spacer = app.content.grid_bbox(0, 0)[3]
    bottom_spacer = app.content.grid_bbox(0, 11)[3]
    if top_spacer < 1 or bottom_spacer < 1:
        raise AssertionError(
            f"Centering spacers are missing: top={top_spacer}, bottom={bottom_spacer}; "
            f"content={app.content.winfo_reqheight()}px, "
            f"viewport={app.page._parent_canvas.winfo_height()}px"
        )
    if abs(top_spacer - bottom_spacer) > 4:
        raise AssertionError(
            f"Main content is not vertically centered: top={top_spacer}, bottom={bottom_spacer}"
        )
    print(
        f"Vertical centering OK: top spacer={top_spacer}px, "
        f"bottom spacer={bottom_spacer}px"
    )
finally:
    app.destroy()
