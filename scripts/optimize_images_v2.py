"""
optimize_images_v2.py — Улучшенная оптимизация изображений для baemoments
- Более агрессивное сжатие (JPEG 65, WebP 65, AVIF 35)
- Дополнительный размер 160px для мобильных
- Пропуск уже оптимизированных файлов
- Детальная статистика экономии
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from PIL import Image


# ── Конфигурация ──────────────────────────────────────────────────────────
QUALITY_JPEG = 65
QUALITY_WEBP = 65
QUALITY_AVIF = 35

SIZES = [160, 320, 640, 960, 1024]  # Добавлен 160px

INPUT_DIR = Path(__file__).resolve().parent.parent / "images"

# Ожидаемые минимальные размеры файлов (КБ) для пропуска уже оптимизированных
# Ключ: (ширина, формат) -> минимальный КБ
# Если файл меньше этого размера — считаем его уже оптимизированным и пропускаем
EXPECTED_MIN_KB: dict[tuple[int, str], float] = {
    # 160px — очень маленькие
    (160, "jpg"):  6.0,
    (160, "webp"): 4.0,
    (160, "avif"): 3.0,
    # 320px
    (320, "jpg"):  12.0,
    (320, "webp"): 8.0,
    (320, "avif"): 5.0,
    # 640px
    (640, "jpg"):  25.0,
    (640, "webp"): 18.0,
    (640, "avif"): 12.0,
    # 960px
    (960, "jpg"):  40.0,
    (960, "webp"): 28.0,
    (960, "avif"): 18.0,
    # 1024px
    (1024, "jpg"): 50.0,
    (1024, "webp"): 35.0,
    (1024, "avif"): 22.0,
    # master (оригинальный размер)
    ("master", "jpg"):  60.0,
    ("master", "webp"): 40.0,
    ("master", "avif"): 25.0,
}

# Паттерн для определения master-файлов (dress-XX.jpg без суффикса размера)
MASTER_SUFFIXES = tuple(f"-{s}" for s in SIZES)


# ── Вспомогательные функции ────────────────────────────────────────────────

def get_size_kb(path: str | Path) -> float:
    """Возвращает размер файла в КБ."""
    return os.path.getsize(path) / 1024


def is_master_jpg(filename: str) -> bool:
    """Проверяет, является ли файл master JPEG (dress-XX.jpg)."""
    if not filename.lower().endswith(".jpg"):
        return False
    # Отбрасываем варианты с размерами
    for suffix in MASTER_SUFFIXES:
        if suffix in filename:
            return False
    # Проверяем паттерн dress-XX.jpg
    base = filename[:-4]  # убираем .jpg
    parts = base.split("-")
    if len(parts) == 2 and parts[0] == "dress" and parts[1].isdigit():
        return True
    return False


def expected_min_kb(size_key: int | str, fmt: str) -> float:
    """Возвращает ожидаемый минимальный размер в КБ для пропуска файла."""
    return EXPECTED_MIN_KB.get((size_key, fmt), 10.0)


def should_skip(filepath: Path, size_key: int | str, fmt: str) -> bool:
    """Проверяет, нужно ли пропустить файл (уже оптимизирован)."""
    if not filepath.exists():
        return False
    current_kb = get_size_kb(filepath)
    min_kb = expected_min_kb(size_key, fmt)
    return current_kb < min_kb


# ── Функции сохранения ─────────────────────────────────────────────────────

def _save_jpeg(img: Image.Image, out_path: Path, quality: int) -> None:
    """Сохраняет изображение в JPEG с MozJPEG-подобными настройками."""
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(
        out_path,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        subsampling=2,  # 4:2:0
    )


def _save_webp(img: Image.Image, out_path: Path, quality: int) -> None:
    """Сохраняет изображение в WebP с максимальным сжатием."""
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    img.save(
        out_path,
        format="WEBP",
        quality=quality,
        method=6,  # максимальный метод сжатия
    )


def _save_avif(img: Image.Image, out_path: Path, quality: int) -> None:
    """Сохраняет изображение в AVIF."""
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    img.save(out_path, format="AVIF", quality=quality)


# ── Основная логика ────────────────────────────────────────────────────────

def optimize_image(master_path: Path, basename: str) -> dict:
    """
    Оптимизирует master-изображение и генерирует все варианты размеров.

    Returns:
        dict со статистикой: original, new, count, skipped
    """
    stats: dict = {"original": 0.0, "new": 0.0, "count": 0, "skipped": 0}

    img = Image.open(master_path)
    original_size = get_size_kb(master_path)
    stats["original"] = original_size

    # Конвертируем в RGB если нужно
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Пересохраняем master JPEG с новым качеством
    if not should_skip(master_path, "master", "jpg"):
        _save_jpeg(img, master_path, QUALITY_JPEG)
        stats["new"] += get_size_kb(master_path)
        stats["count"] += 1
    else:
        stats["skipped"] += 1

    # Master WebP
    master_webp = master_path.with_suffix(".webp")
    if not should_skip(master_webp, "master", "webp"):
        _save_webp(img, master_webp, QUALITY_WEBP)
        stats["new"] += get_size_kb(master_webp)
        stats["count"] += 1
    else:
        stats["skipped"] += 1

    # Master AVIF
    master_avif = master_path.with_suffix(".avif")
    if not should_skip(master_avif, "master", "avif"):
        _save_avif(img, master_avif, QUALITY_AVIF)
        stats["new"] += get_size_kb(master_avif)
        stats["count"] += 1
    else:
        stats["skipped"] += 1

    # Генерируем варианты для каждого размера
    for size in SIZES:
        if size >= img.width:
            continue

        # Ресайз
        target_height = round(img.height * (size / img.width))
        resized = img.resize((size, target_height), Image.Resampling.LANCZOS)

        # JPEG вариант
        jpeg_path = master_path.with_name(f"{basename}-{size}.jpg")
        if not should_skip(jpeg_path, size, "jpg"):
            _save_jpeg(resized, jpeg_path, QUALITY_JPEG)
            stats["new"] += get_size_kb(jpeg_path)
            stats["count"] += 1
        else:
            stats["skipped"] += 1

        # WebP вариант
        webp_path = master_path.with_name(f"{basename}-{size}.webp")
        if not should_skip(webp_path, size, "webp"):
            _save_webp(resized, webp_path, QUALITY_WEBP)
            stats["new"] += get_size_kb(webp_path)
            stats["count"] += 1
        else:
            stats["skipped"] += 1

        # AVIF вариант
        avif_path = master_path.with_name(f"{basename}-{size}.avif")
        if not should_skip(avif_path, size, "avif"):
            _save_avif(resized, avif_path, QUALITY_AVIF)
            stats["new"] += get_size_kb(avif_path)
            stats["count"] += 1
        else:
            stats["skipped"] += 1

    return stats


def main() -> int:
    print("=" * 70)
    print("  ОПТИМИЗАЦИЯ ИЗОБРАЖЕНИЙ BAEMOMENTS v2")
    print("  JPEG: quality=65 | WebP: quality=65 | AVIF: quality=35")
    print(f"  Размеры: {SIZES}")
    print("=" * 70)

    if not INPUT_DIR.exists():
        print(f"ОШИБКА: Директория не найдена: {INPUT_DIR}")
        return 1

    total_original = 0.0
    total_new = 0.0
    total_count = 0
    total_skipped = 0
    processed_files = 0

    start_time = time.time()

    # Находим все master JPEG
    for f in sorted(os.listdir(INPUT_DIR)):
        if not is_master_jpg(f):
            continue

        basename = f.replace(".jpg", "")
        master_path = INPUT_DIR / f

        processed_files += 1
        print(f"\n[{processed_files:2d}/56] {basename}")

        stats = optimize_image(master_path, basename)

        if stats["original"] > 0:
            saving = ((stats["original"] - stats["new"]) / stats["original"]) * 100
            print(f"     Original: {stats['original']:>8.1f} KB")
            print(f"     New:      {stats['new']:>8.1f} KB")
            print(f"     Saving:   {saving:>7.1f}%")
            print(f"     Files:    {stats['count']} created, {stats['skipped']} skipped")

            total_original += stats["original"]
            total_new += stats["new"]
            total_count += stats["count"]
            total_skipped += stats["skipped"]

    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("  ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    print(f"  Обработано изображений:  {processed_files}")
    print(f"  Создано файлов:          {total_count}")
    print(f"  Пропущено (уже оптим.):  {total_skipped}")
    print(f"  Общий размер ДО:         {total_original:>10.1f} KB ({total_original/1024:.2f} MB)")
    print(f"  Общий размер ПОСЛЕ:      {total_new:>10.1f} KB ({total_new/1024:.2f} MB)")
    if total_original > 0:
        saving_pct = ((total_original - total_new) / total_original) * 100
        saved_bytes = (total_original - total_new) * 1024
        print(f"  Экономия:                {saving_pct:>7.1f}%")
        print(f"  Сэкономлено:             {saved_bytes/1024:.2f} KB ({saved_bytes/1024/1024:.2f} MB)")
    print(f"  Время выполнения:        {elapsed:.1f} сек")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
