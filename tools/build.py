"""Rebuild the self-contained pages from their sources.

    python tools/build.py

Each src.html carries a placeholder that is filled with pixel data derived
from the original photo (the photo itself is not in this repository).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
jobs = [
    (ROOT / "ten-thousand-mouths", "__AVATAR__", "avatar.b64"),
    (ROOT / "digital-guy", "__PORTRAIT__", "portrait.txt"),
]
for folder, marker, data in jobs:
    src = (folder / "src.html").read_text(encoding="utf-8")
    value = (folder / data).read_text(encoding="utf-8").strip()
    (folder / "index.html").write_text(src.replace(marker, value), encoding="utf-8")
    print("built", folder.name)
