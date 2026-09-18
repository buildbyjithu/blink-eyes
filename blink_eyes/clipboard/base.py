from abc import ABC, abstractmethod

from PIL import Image


class ClipboardBackend(ABC):
    @abstractmethod
    def copy_image(self, image: Image.Image) -> None:
        """Copy a PIL image to the system clipboard as image data."""
        raise NotImplementedError
