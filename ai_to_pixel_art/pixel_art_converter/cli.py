import argparse
import sys
import os
from pixel_art_converter.converter import process_batch, process_image

def main():
    parser = argparse.ArgumentParser(
        description="Convert AI-generated images to authentic pixel art."
    )

    parser.add_argument(
        "input",
        type=str,
        help="Input image or directory of images."
    )

    parser.add_argument(
        "output",
        type=str,
        help="Output image or directory."
    )

    parser.add_argument(
        "--palette",
        type=int,
        default=16,
        choices=[2, 4, 8, 16, 32, 64, 128, 256],
        help="Number of colors in the reduced palette (default: 16)."
    )

    parser.add_argument(
        "--dither",
        type=str,
        default="floyd-steinberg",
        choices=["none", "floyd-steinberg", "atkinson"],
        help="Dithering method to use (default: floyd-steinberg)."
    )

    parser.add_argument(
        "--pixel-size",
        type=str,
        default="auto",
        help="Pixelation scaling factor as an integer, or 'auto' to automatically compute it based on image resolution (default: 'auto')."
    )

    parser.add_argument(
        "--format",
        type=str,
        default=None,
        choices=["PNG", "JPEG", "BMP", "WEBP"],
        help="Output format. If not specified, infers from extension or defaults to PNG."
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Maximum number of parallel workers for batch processing."
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input path '{args.input}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if os.path.isdir(args.input):
        # Batch processing mode
        print(f"Starting batch processing from {args.input} to {args.output}...")
        process_batch(
            input_dir=args.input,
            output_dir=args.output,
            palette_size=args.palette,
            dither_method=args.dither,
            pixel_size=args.pixel_size,
            output_format=args.format,
            max_workers=args.workers
        )
    elif os.path.isfile(args.input):
        # Single image processing
        print(f"Processing single image: {args.input} -> {args.output}")
        result = process_image(
            input_path=args.input,
            output_path=args.output,
            palette_size=args.palette,
            dither_method=args.dither,
            pixel_size=args.pixel_size,
            output_format=args.format
        )
        print(result)
        if result.startswith("Error"):
            sys.exit(1)
    else:
        print(f"Error: '{args.input}' is not a valid file or directory.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
