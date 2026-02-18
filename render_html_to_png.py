#!/usr/bin/env python3
"""
Render a local HTML file to PNG using Playwright CLI.

This utility intentionally uses `npx playwright screenshot` so the repository
does not need a permanent JavaScript runtime dependency in project files.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def _try_screenshot(
    html_path: Path,
    output_path: Path,
    browser: str,
    viewport_width: int,
    viewport_height: int,
    wait_ms: int,
) -> subprocess.CompletedProcess[str]:
    file_url = html_path.resolve().as_uri()
    return _run(
        [
            "npx",
            "playwright",
            "screenshot",
            "-b",
            browser,
            "--full-page",
            "--viewport-size",
            f"{viewport_width},{viewport_height}",
            "--wait-for-timeout",
            str(wait_ms),
            file_url,
            str(output_path),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture PNG from local HTML using Playwright CLI."
    )
    parser.add_argument(
        "--html",
        required=True,
        help="Path to source HTML file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output PNG file.",
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "webkit", "firefox"],
        default="chromium",
        help="Browser engine to use.",
    )
    parser.add_argument(
        "--viewport-width",
        type=int,
        default=1200,
        help="Viewport width in pixels.",
    )
    parser.add_argument(
        "--viewport-height",
        type=int,
        default=900,
        help="Viewport height in pixels.",
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=400,
        help="Wait time before capture in milliseconds.",
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Install browser binary and retry once on first failure.",
    )
    args = parser.parse_args()

    html_path = Path(args.html)
    output_path = Path(args.output)

    if not html_path.is_file():
        print(f"HTML file not found: {html_path}", file=sys.stderr)
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = _try_screenshot(
        html_path=html_path,
        output_path=output_path,
        browser=args.browser,
        viewport_width=args.viewport_width,
        viewport_height=args.viewport_height,
        wait_ms=args.wait_ms,
    )

    if result.returncode != 0 and args.auto_install:
        install = _run(["npx", "playwright", "install", args.browser])
        if install.returncode != 0:
            print("Failed to install Playwright browser runtime.", file=sys.stderr)
            if install.stdout:
                print(install.stdout, file=sys.stderr)
            if install.stderr:
                print(install.stderr, file=sys.stderr)
            return 3
        result = _try_screenshot(
            html_path=html_path,
            output_path=output_path,
            browser=args.browser,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            wait_ms=args.wait_ms,
        )

    if result.returncode != 0:
        print("Screenshot capture failed.", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return 1

    if not output_path.is_file() or output_path.stat().st_size == 0:
        print(f"PNG output missing or empty: {output_path}", file=sys.stderr)
        return 4

    print(f"Wrote PNG: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
