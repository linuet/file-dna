from __future__ import annotations

from pathlib import Path

from .fingerprint import (
    byte_entropy,
    looks_like_text,
    printable_ratio,
    sha256_bytes,
    simhash64,
    text_metrics,
)
from .models import FileRecord

IGNORED_DIRS = {
    ".git", ".idea", ".vscode", "__pycache__", "node_modules",
    ".venv", "venv", "dist", "build", "coverage",
}


def scan_directory(
    root: Path,
    *,
    max_file_bytes: int = 8 * 1024 * 1024,
    include_hidden: bool = False,
) -> list[FileRecord]:
    root = root.resolve()
    records: list[FileRecord] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        parts = path.relative_to(root).parts

        if any(part in IGNORED_DIRS for part in parts):
            continue
        if not include_hidden and any(part.startswith(".") for part in parts):
            continue

        try:
            size = path.stat().st_size
            if size > max_file_bytes:
                continue
            data = path.read_bytes()
        except OSError:
            continue

        is_text = looks_like_text(data)

        record = FileRecord(
            path=path.relative_to(root).as_posix(),
            extension=path.suffix.lower() or "(none)",
            size=size,
            sha256=sha256_bytes(data),
            is_text=is_text,
            entropy=round(byte_entropy(data), 4),
            printable_ratio=round(printable_ratio(data), 4),
        )

        if is_text:
            text = data.decode("utf-8", errors="replace")
            lines, words, average = text_metrics(text)
            record.lines = lines
            record.words = words
            record.avg_line_length = round(average, 2)
            record.simhash = simhash64(text)

        records.append(record)

    return records
