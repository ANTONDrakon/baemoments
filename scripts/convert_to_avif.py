"""
convert_to_avif.py — Конвертация оставшихся JPEG в AVIF

Находит все JPEG-изображения (master и варианты), для которых нет
соответствующей AVIF-версии, и конвертирует их в AVIF с quality 35.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from PIL import Image


QUALITY_AVIF = 35
INPUT_DIR = Path(__file__).resolve().parent.parent / "images"


def get_size_kb(path: str | Path) -> float:
    """Возвращает размер файла в КБ."""
    return os.path.getsize(path) / 1024


def find_jpegs_without_avif(images_dir: Path) -> list[Path]:
    """
    Находит все JPEG-файлы, для которых нет соответствующей AVIF-версии.

    Returns:
        Список путей к JPEG-файлам без AVIF
    """
    jpegs_without_avif: list[Path] = []

    for f in sorted(images_dir.iterdir()):
        if not f.is_file():
            continue
        if not f.suffix.lower() in (".jpg", ".jpeg"):
            continue

        # Соответствующий AVIF-файл
        avif_path = f.with_suffix(".avif")
        if not avif_path.exists():
            jpegs_without_avif.append(f)

    return jpegs_without_avif


def convert_to_avif(jpeg_path: Path) -> dict:
    """
    Конвертирует JPEG в AVIF.

    Returns:
        dict со статистикой: original_kb, new_kb, success
    """
    result: dict = {"original_kb": 0.0, "new_kb": 0.0, "success": False}

    original_kb = get_size_kb(jpeg_path)
    result["original_kb"] = original_kb

    try:
        img = Image.open(jpeg_path)

        # Конвертируем в RGB если нужно
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        avif_path = jpeg_path.with_suffix(".avif")
        img.save(avif_path, format="AVIF", quality=QUALITY_AVIF)

        new_kb = get_size_kb(avif_path)
        result["new_kb"] = new_kb
        result["success"] = True

    except Exception as e:
        print(f"  ОШИБКА: {e}")
        result["success"] = False

    return result


def main() -> int:
    print("=" * 70)
    print("  КОНВЕРТАЦИЯ JPEG > AVIF")
    print(f"  AVIF quality: {QUALITY_AVIF}")
    print("=" * 70)

    if not INPUT_DIR.exists():
        print(f"ОШИБКА: Директория не найдена: {INPUT_DIR}")
        return 1

    # Находим JPEG без AVIF
    jpegs = find_jpegs_without_avif(INPUT_DIR)

    if not jpegs:
        print("\n  Все JPEG уже имеют AVIF-версии. Конвертация не требуется.")
        return 0

    print(f"\n  Найдено JPEG без AVIF: {len(jpegs)}")

    total_original = 0.0
    total_new = 0.0
    converted = 0
    errors = 0

    start_time = time.time()

    for i, jpeg_path in enumerate(jpegs, 1):
        print(f"\n[{i:3d}/{len(jpegs)}] {jpeg_path.name}", end="")

        result = convert_to_avif(jpeg_path)

        if result["success"]:
            saving = ((result["original_kb"] - result["new_kb"]) / result["original_kb"]) * 100
            print(f"\n       JPEG: {result['original_kb']:>8.1f} KB")
            print(f"       AVIF: {result['new_kb']:>8.1f} KB")
            print(f"       Экономия: {saving:>6.1f}%")

            total_original += result["original_kb"]
            total_new += result["new_kb"]
            converted += 1
        else:
            print(" — ОШИБКА")
            errors += 1

    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("  ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    print(f"  Конвертировано:         {converted}")
    print(f"  Ошибок:                 {errors}")
    print(f"  Общий размер JPEG:      {total_original:>8.1f} KB ({total_original/1024:.2f} MB)")
    print(f"  Общий размер AVIF:      {total_new:>8.1f} KB ({total_new/1024:.2f} MB)")
    if total_original > 0:
        saving_pct = ((total_original - total_new) / total_original) * 100
        saved_bytes = (total_original - total_new) * 1024
        print(f"  Экономия:               {saving_pct:>6.1f}%")
        print(f"  Сэкономлено:            {saved_bytes/1024:.2f} KB ({saved_bytes/1024/1024:.2f} MB)")
    print(f"  Время выполнения:       {elapsed:.1f} сек")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
