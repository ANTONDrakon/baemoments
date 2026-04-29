from __future__ import annotations

import re
from pathlib import Path


IMG_RE = re.compile(
    r'(?P<prefix><div class="product-image-wrapper">)\s*'
    r'(?P<img><img\s+[^>]*?src="images/(?P<name>dress-\d{2})\.jpg"[^>]*?>)',
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
    return (
        '<picture class="product-picture">'
        f'<source type="image/avif" srcset="images/{name}.avif">'
        f'<source type="image/webp" srcset="images/{name}.webp">'
        f"{img_tag}"
        "</picture>"
    )


def update_index(index_path: Path) -> None:
    html = index_path.read_text(encoding="utf-8")

    first = True

    def repl(match: re.Match[str]) -> str:
        nonlocal first

        prefix = match.group("prefix")
        img_tag = match.group("img")
        name = match.group("name")

        img_tag = _ensure_attr(img_tag, "decoding", "async")

        # The first visible product image is typically LCP on mobile.
        if first:
            img_tag = _set_attr(img_tag, "loading", "eager")
            img_tag = _ensure_attr(img_tag, "fetchpriority", "high")
            first = False
        else:
            img_tag = _set_attr(img_tag, "loading", "lazy")
            img_tag = _ensure_attr(img_tag, "fetchpriority", "low")

        return prefix + _wrap_img(name, img_tag)

    new_html, count = IMG_RE.subn(repl, html)
    if count == 0:
        raise SystemExit("No product images found to update.")

    index_path.write_text(new_html, encoding="utf-8")


def main() -> int:
    update_index(Path("index.html"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

