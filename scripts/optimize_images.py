from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class EncodeSettings:
    jpeg_quality: int = 80
    webp_quality: int = 75
    avif_quality: int = 45


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
    for jpg_path in sorted(images_dir.glob("dress-*.jpg")):
        if not jpg_path.is_file():
            continue

        img = Image.open(jpg_path)

        # Re-encode JPEG in place (often huge savings for camera-originated JPGs)
        _save_jpeg(img, jpg_path, settings.jpeg_quality)

        # Next-gen formats for modern browsers
        webp_path = jpg_path.with_suffix(".webp")
        avif_path = jpg_path.with_suffix(".avif")

        _save_webp(img, webp_path, settings.webp_quality)
        _save_avif(img, avif_path, settings.avif_quality)


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
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

