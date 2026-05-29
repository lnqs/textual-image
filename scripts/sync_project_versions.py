#!/usr/bin/env python3
"""Set the textual-image package version in uv.lock to match [project].version."""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

PYPROJECT = Path("pyproject.toml")
UV_LOCK = Path("uv.lock")
PACKAGE_VERSION_RE = re.compile(
    r'\[\[package\]\]\nname = "textual-image"\nversion = "([^"]+)"',
)
PACKAGE_VERSION_SUB = re.compile(
    r'(\[\[package\]\]\nname = "textual-image"\nversion = ")[^"]+(")',
)


def main() -> int:
    project_version = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]

    lock_text = UV_LOCK.read_text(encoding="utf-8")
    match = PACKAGE_VERSION_RE.search(lock_text)
    if match is None:
        print("Could not find textual-image package in uv.lock", file=sys.stderr)
        return 1

    if match.group(1) == project_version:
        print(f"uv.lock already lists textual-image {project_version}")
    else:
        lock_text = PACKAGE_VERSION_SUB.sub(rf"\g<1>{project_version}\g<2>", lock_text, count=1)
        UV_LOCK.write_text(lock_text, encoding="utf-8")
        print(f"Set textual-image version in uv.lock to {project_version}")

    check = subprocess.run(["uv", "lock", "--check"], capture_output=True, text=True)
    if check.returncode != 0:
        print(check.stdout, file=sys.stderr)
        print(check.stderr, file=sys.stderr)
        print(
            "uv.lock is out of sync beyond the package version; run `uv lock` locally",
            file=sys.stderr,
        )
        return check.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
