import io

from PIL import Image

from .base import ClipboardBackend


class MacClipboard(ClipboardBackend):
    def copy_image(self, image: Image.Image) -> None:
        from AppKit import NSPasteboard, NSImage
        from Foundation import NSData

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        ns_data = NSData.dataWithBytes_length_(buf.getvalue(), len(buf.getvalue()))
        ns_image = NSImage.alloc().initWithData_(ns_data)
        if ns_image is None:
            raise RuntimeError("Failed to build NSImage from screenshot data")

        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        ok = pasteboard.writeObjects_([ns_image])
        if not ok:
            raise RuntimeError("Failed to write image to macOS pasteboard")
