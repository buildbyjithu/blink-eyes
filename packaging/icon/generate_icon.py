"""Generates the app icon for both the macOS app bundle (.icns) and the
Windows build (.ico).

Run with: python3 packaging/icon/generate_icon.py
The .icns step requires macOS's built-in `iconutil`; the .ico step is pure
PIL and works on any platform (so it can be regenerated here even though the
Windows build itself has to happen on Windows).
"""

import os
import platform
import subprocess

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ICONSET_DIR = os.path.join(HERE, "AppIcon.iconset")
ICNS_PATH = os.path.join(HERE, "AppIcon.icns")
ICO_PATH = os.path.join(HERE, "AppIcon.ico")

BG_COLOR = (30, 41, 59)  # slate
EYE_COLOR = (255, 255, 255)
PUPIL_COLOR = (46, 204, 113)  # matches the tray "active" green


def draw_master_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    corner_radius = int(size * 0.22)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=corner_radius, fill=BG_COLOR)

    # Almond-shaped eye: intersection of two circles.
    cx, cy = size / 2, size / 2
    eye_w = size * 0.62
    eye_h = size * 0.32
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    r = eye_w * 0.62
    mask_draw.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 1.45], fill=255)
    mask_draw.ellipse([cx - r, cy - r * 1.45, cx + r, cy + r * 0.55], fill=0)
    eye_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(eye_layer).ellipse(
        [cx - eye_w / 2, cy - eye_h / 2, cx + eye_w / 2, cy + eye_h / 2], fill=EYE_COLOR
    )
    image.paste(eye_layer, (0, 0), eye_layer)

    pupil_r = size * 0.11
    draw.ellipse([cx - pupil_r, cy - pupil_r, cx + pupil_r, cy + pupil_r], fill=PUPIL_COLOR)

    return image


def main() -> None:
    os.makedirs(ICONSET_DIR, exist_ok=True)
    master = draw_master_icon(1024)

    sizes = [16, 32, 128, 256, 512]
    for size in sizes:
        master.resize((size, size), Image.LANCZOS).save(
            os.path.join(ICONSET_DIR, f"icon_{size}x{size}.png")
        )
        master.resize((size * 2, size * 2), Image.LANCZOS).save(
            os.path.join(ICONSET_DIR, f"icon_{size}x{size}@2x.png")
        )

    ico_sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    master.save(ICO_PATH, format="ICO", sizes=ico_sizes)
    print(f"Wrote {ICO_PATH}")

    if platform.system() == "Darwin":
        subprocess.run(["iconutil", "-c", "icns", ICONSET_DIR, "-o", ICNS_PATH], check=True)
        print(f"Wrote {ICNS_PATH}")
    else:
        print("Skipping .icns (requires macOS's iconutil)")


if __name__ == "__main__":
    main()
