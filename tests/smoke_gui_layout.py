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

    app.update()
    top_spacer = app.content.grid_bbox(0, 0)[3]
    bottom_spacer = app.content.grid_bbox(0, 11)[3]
    print({
        "canvas_height": app.page._parent_canvas.winfo_height(),
        "scroll_frame_height": app.page._parent_frame.winfo_height(),
        "content_height": app.content.winfo_height(),
        "content_reqheight": app.content.winfo_reqheight(),
        "window_height": app.page._parent_canvas.itemcget(app.page._create_window_id, "height"),
        "top_spacer": top_spacer,
        "bottom_spacer": bottom_spacer,
        "content_grid_size": app.content.grid_size(),
    })
    if top_spacer < 1 or bottom_spacer < 1:
        raise AssertionError(
            f"Centering spacers are missing: top={top_spacer}, bottom={bottom_spacer}"
        )
    if abs(top_spacer - bottom_spacer) > 4:
        raise AssertionError(
            f"Main content is not vertically centered: top={top_spacer}, bottom={bottom_spacer}"
        )
finally:
    app.destroy()
