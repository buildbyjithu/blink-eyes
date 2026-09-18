import platform

from .base import ClipboardBackend

__all__ = ["ClipboardBackend", "get_clipboard_backend"]


def get_clipboard_backend() -> ClipboardBackend:
    system = platform.system()
    if system == "Darwin":
        from .macos import MacClipboard

        return MacClipboard()
    elif system == "Windows":
        from .windows import WindowsClipboard

        return WindowsClipboard()
    elif system == "Linux":
        from .linux import LinuxClipboard

        return LinuxClipboard()
    raise RuntimeError(f"Unsupported platform: {system}")
