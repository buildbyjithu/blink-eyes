from PIL import Image

from .base import ClipboardBackend


class LinuxClipboard(ClipboardBackend):
    """Not yet implemented.

    Future implementation sketch: save the PIL image to PNG bytes and pipe
    it to a subprocess: on X11, `xclip -selection clipboard -t image/png`
    (or `xsel`); on Wayland, `wl-copy` with the same PNG bytes on stdin.
    Which one to use must be detected at runtime (e.g. via the
    `WAYLAND_DISPLAY` environment variable) since the two display protocols
    require different clipboard tools.
    """

    def copy_image(self, image: Image.Image) -> None:
        raise NotImplementedError("Linux clipboard support is not implemented yet")
