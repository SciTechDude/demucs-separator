#!/usr/bin/env python3
"""CLI tool for audio source separation using Facebook's Demucs model."""

import argparse
import os
import sys
import subprocess
import shutil
from pathlib import Path


VALID_STEMS = {"vocals", "drums", "bass", "other"}
VALID_MODELS = {"htdemucs", "htdemucs_ft", "mdx_extra"}


def parse_args(args=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Separate audio into stems using Facebook's Demucs model.",
        epilog="Examples:\n"
        "  python separate.py input.wav --stems vocals,drums\n"
        "  python separate.py input.mp3 --vocals-only --output ./output/\n"
        "  python separate.py input.flac --model htdemucs_ft\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input",
        type=str,
        help="Path to the input audio file (supports wav, mp3, flac, m4a, and other ffmpeg formats)",
    )

    stem_group = parser.add_mutually_exclusive_group()
    stem_group.add_argument(
        "--stems",
        type=str,
        default=None,
        help="Comma-separated list of stems to extract (vocals, drums, bass, other)",
    )
    stem_group.add_argument(
        "--vocals-only",
        action="store_true",
        help="Shortcut to extract only vocals and other (accompaniment)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./output",
        help="Output directory for separated stems (default: ./output/)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="htdemucs",
        choices=sorted(VALID_MODELS),
        help="Demucs model to use (default: htdemucs)",
    )

    return parser.parse_args(args)


def validate_args(args):
    """Validate parsed arguments."""
    # Check input file exists
    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Parse and validate stems
    if args.vocals_only:
        args.selected_stems = ["vocals", "other"]
    elif args.stems:
        stems = [s.strip().lower() for s in args.stems.split(",")]
        invalid = set(stems) - VALID_STEMS
        if invalid:
            print(
                f"Error: Invalid stem(s): {', '.join(invalid)}. "
                f"Valid stems are: {', '.join(sorted(VALID_STEMS))}",
                file=sys.stderr,
            )
            sys.exit(1)
        args.selected_stems = stems
    else:
        args.selected_stems = sorted(VALID_STEMS)

    return args


def separate(input_path, output_dir, model, selected_stems):
    """Run Demucs separation and copy selected stems to output directory.

    Args:
        input_path: Path to the input audio file.
        output_dir: Directory to write output stems.
        model: Demucs model name.
        selected_stems: List of stem names to extract.

    Returns:
        List of output file paths.
    """
    input_path = os.path.abspath(input_path)
    output_dir = os.path.abspath(output_dir)

    # Create a temporary directory for demucs output
    tmp_dir = os.path.join(output_dir, ".demucs_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    # Build demucs command
    cmd = [
        sys.executable,
        "-m",
        "demucs",
        "--name", model,
        "--out", tmp_dir,
        input_path,
    ]

    print(f"Separating audio with model '{model}'...")
    print(f"Input: {input_path}")
    print(f"Stems: {', '.join(selected_stems)}")
    print()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running demucs: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(
            "Error: demucs not found. Install it with: pip install demucs",
            file=sys.stderr,
        )
        sys.exit(1)

    # Find separated stems in demucs output
    input_name = Path(input_path).stem
    stems_dir = os.path.join(tmp_dir, model, input_name)

    if not os.path.isdir(stems_dir):
        print(f"Error: Expected output directory not found: {stems_dir}", file=sys.stderr)
        sys.exit(1)

    # Copy selected stems to output directory
    os.makedirs(output_dir, exist_ok=True)
    output_files = []

    for stem in selected_stems:
        stem_file = os.path.join(stems_dir, f"{stem}.wav")
        if os.path.isfile(stem_file):
            dest = os.path.join(output_dir, f"{stem}.wav")
            shutil.copy2(stem_file, dest)
            output_files.append(dest)
            print(f"  -> {dest}")
        else:
            print(f"  Warning: Stem '{stem}' not found in output", file=sys.stderr)

    # Clean up temporary directory
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\nDone! {len(output_files)} stem(s) saved to: {output_dir}")
    return output_files


def main():
    """Main entry point."""
    args = parse_args()
    args = validate_args(args)
    separate(args.input, args.output, args.model, args.selected_stems)


if __name__ == "__main__":
    main()
