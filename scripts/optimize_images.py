from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re

from PIL import Image


MASTER_JPG_RE = re.compile(r"^dress-\d{2}\.jpg$", re.IGNORECASE)


@dataclass(frozen=True)
class EncodeSettings:
    jpeg_quality: int = 80
    webp_quality: int = 75
    avif_quality: int = 45
    widths: tuple[int, ...] = (320, 640, 960, 1024)


def _resize_to_width(img: Image.Image, target_width: int) -> Image.Image | None:
    if img.width == target_width:
        return img
    if img.width < target_width:
        return None
    target_height = round(img.height * (target_width / img.width))
    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def _save_jpeg(img: Image.Image, out_path: Path, quality: int) -> None:
    # JPEG doesn't support alpha; ensure RGB.
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(
        out_path,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        subsampling="4:2:0",
    )


def _save_webp(img: Image.Image, out_path: Path, quality: int) -> None:
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    img.save(
        out_path,
        format="WEBP",
        quality=quality,
        method=6,
    )


def _save_avif(img: Image.Image, out_path: Path, quality: int) -> None:
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    img.save(out_path, format="AVIF", quality=quality)


def optimize_folder(images_dir: Path, settings: EncodeSettings) -> None:
    # Only process "master" images (dress-01.jpg .. dress-56.jpg).
    # Otherwise repeated runs would re-process generated variants and explode output.
    for jpg_path in sorted(images_dir.glob("dress-*.jpg")):
        if not jpg_path.is_file():
            continue
        if not MASTER_JPG_RE.match(jpg_path.name):
            continue

        base_img = Image.open(jpg_path)

        # Re-encode master JPEG in place (often huge savings for camera-originated JPGs)
        _save_jpeg(base_img, jpg_path, settings.jpeg_quality)

        stem = jpg_path.with_suffix("").name  # dress-01

        # Always generate master next-gen formats for the original dimensions.
        _save_webp(base_img, images_dir / f"{stem}.webp", settings.webp_quality)
        _save_avif(base_img, images_dir / f"{stem}.avif", settings.avif_quality)

        # Produce multiple widths so mobile can download a smaller asset (fixes PSI "image bigger than container")
        for width in settings.widths:
            if width >= base_img.width:
                continue
            resized = _resize_to_width(base_img, width)
            if resized is None:
                continue
            suffix = f"-{resized.width}"

            _save_jpeg(resized, images_dir / f"{stem}{suffix}.jpg", settings.jpeg_quality)
            _save_webp(resized, images_dir / f"{stem}{suffix}.webp", settings.webp_quality)
            _save_avif(resized, images_dir / f"{stem}{suffix}.avif", settings.avif_quality)


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize dress images for web.")
    parser.add_argument(
        "--images-dir",
        default="images",
        help="Path to images directory (default: images)",
    )
    parser.add_argument("--jpeg-quality", type=int, default=80)
    parser.add_argument("--webp-quality", type=int, default=75)
    parser.add_argument("--avif-quality", type=int, default=45)
    parser.add_argument(
        "--widths",
        default="320,640,960,1024",
        help="Comma-separated widths to generate (default: 320,640,960,1024)",
    )
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    if not images_dir.exists():
        raise SystemExit(f"Images directory not found: {images_dir}")

    optimize_folder(
        images_dir,
        EncodeSettings(
            jpeg_quality=args.jpeg_quality,
            webp_quality=args.webp_quality,
            avif_quality=args.avif_quality,
            widths=tuple(int(w.strip()) for w in args.widths.split(",") if w.strip()),
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
