import io

from PIL import Image

from .base import ClipboardBackend


class WindowsClipboard(ClipboardBackend):
    def copy_image(self, image: Image.Image) -> None:
        import win32clipboard

        if image.mode != "RGB":
            image = image.convert("RGB")

        buf = io.BytesIO()
        image.save(buf, format="BMP")
        # The Windows clipboard's CF_DIB format wants just the DIB payload,
        # not the 14-byte BITMAPFILEHEADER that PIL's BMP writer prepends.
        dib_data = buf.getvalue()[14:]

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib_data)
        finally:
            win32clipboard.CloseClipboard()
