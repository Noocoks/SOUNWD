"""Desktop GUI regression test: visible controls, logo, centering and scrolling."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gui import SoundwApp


def settle(app):
    app.update_idletasks()
    app.update()
    app._center_content()
    app.update_idletasks()
    app.update()


app = SoundwApp()
try:
    app.geometry("900x820")
    settle(app)

    # The key widgets must exist, be mapped and have non-zero dimensions.
    required = {
        "logo": app.brand_mark,
        "URL input": app.url_entry,
        "download button": app.download_button,
        "status": app.status_label,
    }
    for name, widget in required.items():
        if not widget.winfo_exists() or not widget.winfo_ismapped():
            raise AssertionError(f"{name} is not visible/mapped")
        if widget.winfo_width() <= 1 or widget.winfo_height() <= 1:
            raise AssertionError(f"{name} has no visible dimensions")

    if app._window_icon is None:
        raise AssertionError("The shared icon PNG was not loaded")
    if str(app.brand_mark.cget("image")) != str(app._brand_image):
        raise AssertionError("The visible logo is not using the committed PNG PhotoImage")
    icon_path = ROOT / "assets" / "sounwd.png"
    if not icon_path.is_file() or icon_path.stat().st_size < 1000:
        raise AssertionError("The committed canonical brand PNG is missing or invalid")
    canvas = app.page._parent_canvas
    window_id = app.page._create_window_id
    viewport = canvas.winfo_height()
    natural_height = max(app.page.winfo_reqheight(), app.content.winfo_reqheight())
    expected_y = max(0, (viewport - natural_height) // 2)
    actual_y = int(round(canvas.coords(window_id)[1]))
    if abs(actual_y - expected_y) > 2:
        raise AssertionError(
            f"Vertical centering mismatch: y={actual_y}, expected={expected_y}, "
            f"viewport={viewport}, content={natural_height}"
        )
    if canvas.bbox(window_id) is None:
        raise AssertionError("The content window is not present in the scroll canvas")

    print(
        f"Visible GUI OK: logo={app.brand_mark.winfo_width()}x{app.brand_mark.winfo_height()}, "
        f"URL={app.url_entry.winfo_width()}x{app.url_entry.winfo_height()}, "
        f"download={app.download_button.winfo_width()}x{app.download_button.winfo_height()}"
    )
    print(f"Vertical placement OK: y={actual_y}px, viewport={viewport}px, content={natural_height}px")

    # Expand advanced controls: layout must remain visible and scrollable.
    app._toggle_advanced()
    settle(app)
    if not app.advanced.winfo_ismapped():
        raise AssertionError("Advanced options did not become visible")
    if canvas.bbox(window_id) is None:
        raise AssertionError("Expanded content disappeared from the scroll canvas")
    print("Advanced layout OK")

    # On a compact window the content starts at the top and remains in scrollregion.
    app.geometry("560x520")
    settle(app)
    actual_y = int(round(canvas.coords(window_id)[1]))
    if actual_y != 0:
        raise AssertionError(f"Compact layout should start at y=0, got y={actual_y}")
    region = canvas.cget("scrollregion")
    if not region:
        raise AssertionError("Compact layout has no scroll region")
    print(f"Compact scroll layout OK: y={actual_y}, scrollregion={region}")
finally:
    app.destroy()
