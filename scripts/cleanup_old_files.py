#!/usr/bin/env python3
"""Remove files older than a configurable age from one or more directories.

By default each directory is scanned once.  Pass ``--live`` to repeat the
scan every hour::

    python scripts/cleanup_old_files.py /tmp/uploads /tmp/results
    python scripts/cleanup_old_files.py --live /tmp/uploads /tmp/results
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Iterable


# Keep these values together so they can be changed without touching the
# cleanup logic.
FILE_AGE_HOURS = 12
CHECK_INTERVAL_HOURS = 1


def cleanup_directory(directory: Path, *, now: float | None = None) -> int:
    """Delete old files below *directory* and return the number deleted.

    Subdirectories are scanned recursively, but directories themselves are
    never removed.  A file that disappears or becomes inaccessible while the
    scan is running is reported and does not stop cleanup of other files.
    """

    if not directory.exists():
        print(f"Ошибка: директория не существует: {directory}")
        return 0
    if not directory.is_dir():
        print(f"Ошибка: это не директория: {directory}")
        return 0

    cutoff = (time.time() if now is None else now) - FILE_AGE_HOURS * 60 * 60
    deleted = 0

    try:
        entries: Iterable[Path] = directory.rglob("*")
        for path in entries:
            try:
                if not path.is_file() or path.stat().st_mtime >= cutoff:
                    continue
                path.unlink()
                deleted += 1
                print(f"Удалён файл: {path}")
            except OSError as error:
                print(f"Ошибка обработки {path}: {error}")
    except OSError as error:
        print(f"Ошибка чтения директории {directory}: {error}")

    return deleted


def cleanup_directories(directories: Iterable[Path]) -> int:
    """Clean all supplied directories and return the total number deleted."""

    return sum(cleanup_directory(directory) for directory in directories)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            f"Удаляет файлы старше {FILE_AGE_HOURS} часов "
            "из указанных директорий."
        )
    )
    parser.add_argument(
        "directories",
        metavar="DIRECTORY",
        nargs="+",
        type=Path,
        help="директории для очистки (включая вложенные директории)",
    )
    parser.add_argument(
        "--live",
        "-l",
        action="store_true",
        help=f"повторять проверку каждые {CHECK_INTERVAL_HOURS} час",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        while True:
            deleted = cleanup_directories(args.directories)
            print(f"Очистка завершена: удалено файлов — {deleted}")
            if not args.live:
                return

            print(
                f"Следующая проверка через {CHECK_INTERVAL_HOURS} час. "
                "Для остановки нажмите Ctrl+C."
            )
            time.sleep(CHECK_INTERVAL_HOURS * 60 * 60)
    except KeyboardInterrupt:
        print("Очистка остановлена.")


if __name__ == "__main__":
    main()
