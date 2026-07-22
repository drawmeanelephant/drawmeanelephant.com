#!/usr/bin/env python3
"""Import referenced WordPress uploads into Boris page-local asset folders."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

UPLOAD_URL = "https://www.drawmeanelephant.com/wp-content/uploads/"
UPLOAD_PATTERN = re.compile(
    r"(?:https://www\.drawmeanelephant\.com/wp-content/uploads/|/assets/uploads/)([^)\" ]+)"
)


def source_lookup(upload_root: Path) -> dict[str, Path]:
    return {path.name: path for path in upload_root.rglob("*") if path.is_file()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", type=Path, default=Path("content"))
    parser.add_argument("--uploads", type=Path, default=Path("uploads"))
    args = parser.parse_args()

    lookup = source_lookup(args.uploads)
    rewritten = 0
    copied: set[Path] = set()
    missing: set[str] = set()

    for page in args.content.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        page_assets = page.with_suffix(".assets")

        def replace(match: re.Match[str]) -> str:
            nonlocal rewritten
            requested_name = Path(match.group(1)).name
            source = lookup.get(requested_name)
            if source is None and requested_name == "2019-07-19-0001-COLOR-ME-1.jpg":
                source = lookup.get("2019-07-19-0001-COLOR-ME.jpg")
            if source is None:
                missing.add(requested_name)
                return match.group(0)

            page_assets.mkdir(parents=True, exist_ok=True)
            destination = page_assets / requested_name
            if not destination.exists():
                shutil.copy2(source, destination)
                copied.add(destination)
            rewritten += 1
            return f"{page_assets.name}/{requested_name}"

        updated = UPLOAD_PATTERN.sub(replace, text)
        if updated != text:
            page.write_text(updated, encoding="utf-8")

    if missing:
        print("Missing upload sources:")
        for name in sorted(missing):
            print(f"- {name}")
        return 1

    print(f"rewritten references: {rewritten}")
    print(f"copied page-local assets: {len(copied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
