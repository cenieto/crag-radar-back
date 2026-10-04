#!/usr/bin/env python3
"""
Tile a large image into a Deep Zoom (DZI) pyramid for OpenSeadragon.

The tiling is done with libvips (through ``pyvips``) by default. libvips
streams the image instead of loading it fully into memory, so it can handle
images with billions of pixels quickly.

Output:
    <output>/<name>.dzi               XML descriptor
    <output>/<name>_files/N/C_R.ext   tiles (N = level, C = column, R = row)

Usage:
    tile-image map.tif -o out
    tile-image map.tif -o out --tile-size 512 --overlap 1 --format jpg --quality 90 
    python -m tilers.openseadragon.cli map.tif -o out

Requirements:
    pip install pyvips[binary]     # default backend (bundles libvips)
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

import pyvips

logger = logging.getLogger(__name__)


DZI_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Image xmlns="http://schemas.microsoft.com/deepzoom/2008" '
    'Format="{fmt}" Overlap="{overlap}" TileSize="{tile_size}">\n'
    '  <Size Width="{width}" Height="{height}"/>\n'
    "</Image>\n"
)


class BackendError(RuntimeError):
    """Raised when a tiling backend is unavailable or fails."""


def parse_args(argv=None):
    """Parse and validate the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Tile a large image into a Deep Zoom (DZI) pyramid for OpenSeadragon.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Path to the input image.")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("tiles"),
        help="Output directory.",
    )
    parser.add_argument(
        "-n", "--name", default=None,
        help="Base name of the output (defaults to the input file name without extension).",
    )
    parser.add_argument(
        "-t", "--tile-size", type=int, default=254,
        help="Tile size in pixels (not counting the overlap).",
    )
    parser.add_argument(
        "--overlap", type=int, default=1,
        help="Overlap in pixels between adjacent tiles.",
    )
    parser.add_argument(
        "-f", "--format", dest="fmt", choices=["jpg", "png", "webp"], default="jpg",
        help="Tile format.",
    )
    parser.add_argument(
        "-q", "--quality", type=int, default=85,
        help="Quality for jpg/webp tiles (1-100).",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Allow overwriting an existing output.",
    )

    args = parser.parse_args(argv)

    if not args.input.is_file():
        parser.error(f"Input file not found: {args.input}")
    if args.tile_size < 1:
        parser.error("--tile-size must be >= 1")
    if args.overlap < 0 or args.overlap >= args.tile_size:
        parser.error("--overlap must be between 0 and tile-size - 1")
    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100")
    if args.name is None:
        args.name = args.input.stem

    return args


def _vips_needs_rotation(image):
    """Return True if the EXIF orientation tag requires rotating/flipping the image."""
    if image.get_typeof("orientation") == 0:
        return False
    return image.get("orientation") > 1


def _vips_suffix(fmt, quality):
    """Build the libvips save suffix, e.g. '.jpg[Q=85]'."""
    if fmt == "png":
        return ".png"
    return f".{fmt}[Q={quality}]"


def tile_with_vips(args, out_dir, files_dir):
    """Tile the image with libvips' dzsave. Returns the number of tiles written."""
    try:
        # Sequential access lets libvips stream the image with minimal memory.
        image = pyvips.Image.new_from_file(str(args.input), access="sequential")

        # Applying the EXIF orientation needs random access, so only reload if required.
        if _vips_needs_rotation(image):
            image = pyvips.Image.new_from_file(str(args.input), access="random").autorot()

        # Normalize to an 8-bit colour space that web browsers can display.
        if image.interpretation == "grey16":
            image = image.colourspace("b-w")
        elif image.interpretation in ("rgb16", "cmyk"):
            image = image.colourspace("srgb")

        # JPEG has no alpha channel: flatten transparency onto a white background.
        if args.fmt == "jpg" and image.hasalpha():
            image = image.flatten(background=[255, 255, 255])

        # dzsave writes <basename>.dzi and <basename>_files/ by itself.
        image.dzsave(
            str(out_dir / args.name),
            tile_size=args.tile_size,
            overlap=args.overlap,
            suffix=_vips_suffix(args.fmt, args.quality),
        )
    except pyvips.Error as exc:
        raise BackendError(f"libvips failed: {exc}") from exc

    return sum(1 for path in files_dir.rglob("*") if path.is_file())


def main(argv=None):
    """Run the tiler. Returns a process exit code."""
    args = parse_args(argv)

    out_dir = args.output
    files_dir = out_dir / f"{args.name}_files"
    dzi_path = out_dir / f"{args.name}.dzi"

    if files_dir.exists() or dzi_path.exists():
        if not args.overwrite:
            logger.error(
                f"Error: output for '{args.name}' already exists in {out_dir}. "
                "Use --overwrite to replace it."
            )
            return 1
        # Remove stale tiles so old and new pyramids are never mixed.
        shutil.rmtree(files_dir, ignore_errors=True)
        dzi_path.unlink(missing_ok=True)

    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Tiling {args.input} ...")
    try:
        total = tile_with_vips(args, out_dir, files_dir)
    except BackendError as exc:
        logger.error(f"Error: {exc}", file=sys.stderr)
        return 1

    logger.info(f"Done: {total} tiles written to {out_dir}")
    logger.info(f'tileSources for OpenSeadragon: "{args.name}.dzi"')
    return 0


if __name__ == "__main__":
    sys.exit(main())