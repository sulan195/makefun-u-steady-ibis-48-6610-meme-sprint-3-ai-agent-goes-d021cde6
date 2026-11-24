"""Entrypoint for the Meme Sprint 3 entry.

Your program writes one image to `/output/entry.png`.

Renders the chosen meme scene with the stdlib-only renderer in render.py
and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
Verifies the competition gates (PNG, <= 1,048,576 bytes, <= 1024x1024)
before reporting success, so a bad build fails loudly instead of
submitting an invalid file.

Usage:
    python3 main.py [--scene review|calendar] [--output-dir DIR]

The graded run uses the default scene ("review"); --scene exists only so
both variants can be rendered locally for the pre-submit comparison.
"""

import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import render  # noqa: E402

MAX_BYTES = 1_048_576
MAX_DIMENSION = 1024
DEFAULT_SCENE = "review"


def resolve_output_dir(env) -> str:
    """Output directory: $MAKEFUN_OUTPUT_DIR, or /output when unset/empty."""
    value = env.get("MAKEFUN_OUTPUT_DIR", "")
    return value if value else "/output"


def run(scene: str, output_dir: str) -> tuple[str, int, str]:
    """Render `scene` and write entry.png into `output_dir`.

    Returns (path, size_in_bytes, sha256_hex). Raises ValueError for an
    unknown scene, OSError when the directory cannot be created or written,
    and RuntimeError when a competition gate is violated.
    """
    canvas = render.render(scene)
    if render.WIDTH > MAX_DIMENSION or render.HEIGHT > MAX_DIMENSION:
        raise RuntimeError(
            f"dimensions {render.WIDTH}x{render.HEIGHT} exceed "
            f"{MAX_DIMENSION}x{MAX_DIMENSION}"
        )
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "entry.png")
    render.write_png(canvas, path)
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        raise RuntimeError(f"entry.png is {size} bytes, over the {MAX_BYTES} limit")
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return path, size, digest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render the meme entry image.")
    parser.add_argument(
        "--scene",
        default=os.environ.get("MEME_SCENE", DEFAULT_SCENE),
        choices=sorted(render.SCENES),
        help="meme scene to render (default: review)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="output directory (default: $MAKEFUN_OUTPUT_DIR or /output)",
    )
    args = parser.parse_args(argv)
    output_dir = args.output_dir or resolve_output_dir(os.environ)
    try:
        path, size, digest = run(args.scene, output_dir)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {path} ({size} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
