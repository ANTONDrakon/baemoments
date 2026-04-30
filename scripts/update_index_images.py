from __future__ import annotations

import re
from pathlib import Path


# Добавлен размер 160w для мобильных устройств (slow 4G)
SIZES = "(max-width: 360px) 100vw, (max-width: 480px) 100vw, (max-width: 768px) 50vw, 260px"

WRAPPER_RE = re.compile(
    r'(<div class="product-image-wrapper">)'
    r'(?P<picture><picture class="product-picture">.*?</picture>)',
    re.IGNORECASE | re.DOTALL,
)

# Ищем img с src="images/dress-XX.jpg" или src="images/dress-XX-640.jpg" (уже обработанные)
IMG_RE = re.compile(
    r'(?P<img><img\s+[^>]*?src="images/(?P<name>dress-\d{2})(?:-\d+)?\.jpg"[^>]*?>)',
    re.IGNORECASE,
)


def _ensure_attr(tag: str, attr: str, value: str | None = None) -> str:
    # If attribute already exists, leave it as-is.
    if re.search(rf"\s{re.escape(attr)}\s*=", tag, flags=re.IGNORECASE):
        return tag
    if re.search(rf"\s{re.escape(attr)}(\s|>)", tag, flags=re.IGNORECASE):
        return tag
    insert = f' {attr}' if value is None else f' {attr}="{value}"'
    return tag[:-1] + insert + ">"


def _set_attr(tag: str, attr: str, value: str) -> str:
    if re.search(rf"\s{re.escape(attr)}\s*=", tag, flags=re.IGNORECASE):
        return re.sub(
            rf'(\s{re.escape(attr)}\s*=\s*")[^"]*(")',
            rf'\1{value}\2',
            tag,
            flags=re.IGNORECASE,
        )
    return tag[:-1] + f' {attr}="{value}">'


def _wrap_img(name: str, img_tag: str) -> str:
    images_dir = Path("images")

    def build_srcset(ext: str) -> str:
        candidates: list[tuple[int, str]] = []
        for w in (160, 320, 640, 960):
            p = images_dir / f"{name}-{w}.{ext}"
            if p.exists():
                candidates.append((w, f"images/{name}-{w}.{ext} {w}w"))
        # Add master as the largest option if present
        master = images_dir / f"{name}.{ext}"
        if master.exists():
            # Width is not encoded; assume 1024 for our masters, but allow smaller.
            width = 1024
            if name in ("dress-35", "dress-37"):
                width = 450
            candidates.append((width, f"images/{name}.{ext} {width}w"))

        candidates.sort(key=lambda x: x[0])
        return ", ".join([c[1] for c in candidates])

    # Make JPEG fallback point to a mid-size by default if available.
    jpg_src = f"images/{name}-640.jpg"
    if not (images_dir / f"{name}-640.jpg").exists():
        jpg_src = f"images/{name}.jpg"

    img_tag = _set_attr(img_tag, "src", jpg_src)
    img_tag = _set_attr(img_tag, "srcset", build_srcset("jpg"))
    img_tag = _set_attr(img_tag, "sizes", SIZES)

    avif_srcset = build_srcset("avif")
    webp_srcset = build_srcset("webp")

    return (
        '<picture class="product-picture">'
        f'<source type="image/avif" srcset="{avif_srcset}" sizes="{SIZES}">'
        f'<source type="image/webp" srcset="{webp_srcset}" sizes="{SIZES}">'
        f"{img_tag}"
        "</picture>"
    )


def update_index(index_path: Path) -> None:
    html = index_path.read_text(encoding="utf-8")

    first = True

    def repl_picture(match: re.Match[str]) -> str:
        nonlocal first

        wrapper_start = match.group(1)
        picture_html = match.group("picture")

        img_match = IMG_RE.search(picture_html)
        if not img_match:
            return match.group(0)

        img_tag = img_match.group("img")
        name = img_match.group("name")

        img_tag = _ensure_attr(img_tag, "decoding", "async")

        # The first visible product image is typically LCP on mobile.
        if first:
            img_tag = _set_attr(img_tag, "loading", "eager")
            img_tag = _ensure_attr(img_tag, "fetchpriority", "high")
            first = False
        else:
            img_tag = _set_attr(img_tag, "loading", "lazy")
            img_tag = _ensure_attr(img_tag, "fetchpriority", "low")

        return wrapper_start + _wrap_img(name, img_tag)

    new_html, count = WRAPPER_RE.subn(repl_picture, html)
    if count == 0:
        raise SystemExit("No product picture blocks found to update.")

    index_path.write_text(new_html, encoding="utf-8")


def main() -> int:
    update_index(Path("index.html"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
