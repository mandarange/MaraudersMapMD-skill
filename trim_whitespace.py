#!/usr/bin/env python3
"""Auto-crop whitespace borders from PNG images.

Usage:
    python trim_whitespace.py <image.png> [--padding 4] [--threshold 250] [--dry-run]

Requires: Pillow (pip install Pillow)
"""

import argparse
import sys

try:
    from PIL import Image, ImageChops
except ImportError:
    print(
        "Error: Pillow is required. Install with: pip install Pillow",
        file=sys.stderr,
    )
    raise SystemExit(1)


def find_content_bbox(img, threshold=250):
    """Bounding box of non-background pixels. bg = all channels >= threshold."""
    if img.mode == "RGBA":
        r, g, b, a = img.split()
        bg = Image.new("L", img.size, threshold)
        # bg-channel subtract: positive where pixel is darker than threshold (=content)
        diff_r = ImageChops.subtract(bg, r)
        diff_g = ImageChops.subtract(bg, g)
        diff_b = ImageChops.subtract(bg, b)
        merged = ImageChops.add(diff_r, ImageChops.add(diff_g, diff_b))
        # transparent pixels → treat as background
        merged.paste(Image.new("L", img.size, 0), mask=ImageChops.invert(a))
        return merged.getbbox()

    rgb = img.convert("RGB")
    bg = Image.new("RGB", img.size, (threshold, threshold, threshold))
    diff = ImageChops.subtract(bg, rgb)
    return diff.convert("L").getbbox()


def trim(img, padding=4, threshold=250):
    bbox = find_content_bbox(img, threshold=threshold)
    if bbox is None:
        return None

    left, upper, right, lower = bbox
    w, h = img.size

    if (
        left <= padding
        and upper <= padding
        and (w - right) <= padding
        and (h - lower) <= padding
    ):
        return None

    crop_left = max(0, left - padding)
    crop_upper = max(0, upper - padding)
    crop_right = min(w, right + padding)
    crop_lower = min(h, lower + padding)

    cropped = img.crop((crop_left, crop_upper, crop_right, crop_lower))
    return cropped, (w, h), cropped.size


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Auto-crop whitespace borders from PNG images."
    )
    parser.add_argument("images", nargs="+", help="PNG file path(s) to trim.")
    parser.add_argument(
        "--padding",
        type=int,
        default=4,
        help="Pixels of padding to keep around content (default: 4).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=250,
        help="Channel value >= this is treated as background (default: 250).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without modifying files.",
    )
    args = parser.parse_args(argv)

    trimmed_count = 0
    for path in args.images:
        try:
            img = Image.open(path)
        except Exception as e:
            print(f"SKIP {path}: {e}", file=sys.stderr)
            continue

        result = trim(img, padding=args.padding, threshold=args.threshold)
        if result is None:
            print(f"OK   {path} (no trim needed)")
            continue

        cropped, orig_size, new_size = result
        pct = 100 * (1 - (new_size[0] * new_size[1]) / (orig_size[0] * orig_size[1]))
        label = "WOULD TRIM" if args.dry_run else "TRIMMED"
        print(
            f"{label} {path}: {orig_size[0]}x{orig_size[1]} -> {new_size[0]}x{new_size[1]} ({pct:.1f}% smaller)"
        )
        if not args.dry_run:
            cropped.save(path)
        trimmed_count += 1

    return 0 if trimmed_count >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
