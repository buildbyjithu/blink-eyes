"""System tray icon: Pause/Resume detection + Quit."""

import threading
import time
from typing import Callable, Optional

import pystray
from PIL import Image, ImageDraw


def _make_icon_image(color: str) -> Image.Image:
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = 8
    draw.ellipse((margin, margin, size - margin, size - margin), fill=color)
    return image


ICON_ACTIVE = _make_icon_image("#2ecc71")  # green: watching for blinks
ICON_PAUSED = _make_icon_image("#95a5a6")  # grey: paused
ICON_TRIGGERED = _make_icon_image("#3498db")  # blue: just fired


def build_tray_icon(
    paused: threading.Event,
    stop_event: threading.Event,
    on_quit: Optional[Callable[[], None]] = None,
) -> pystray.Icon:
    def toggle_pause(icon, item):
        if paused.is_set():
            paused.clear()
        else:
            paused.set()
        icon.icon = ICON_PAUSED if paused.is_set() else ICON_ACTIVE

    def is_paused(item) -> bool:
        return paused.is_set()

    def quit_app(icon, item):
        stop_event.set()
        if on_quit is not None:
            on_quit()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Pause detection", toggle_pause, checked=is_paused),
        pystray.MenuItem("Quit", quit_app),
    )

    return pystray.Icon("blink-eyes", ICON_ACTIVE, "blink-eyes", menu)


def flash_icon(icon: pystray.Icon, paused: threading.Event, duration: float = 0.3) -> None:
    """Briefly change the tray icon to confirm a trigger fired, then revert."""

    def _flash():
        icon.icon = ICON_TRIGGERED
        time.sleep(duration)
        icon.icon = ICON_PAUSED if paused.is_set() else ICON_ACTIVE

    threading.Thread(target=_flash, daemon=True).start()
