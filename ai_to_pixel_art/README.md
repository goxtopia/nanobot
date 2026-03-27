# Pixel Art Converter

Batch convert AI-generated or standard images into authentic pixel art.

This Python package supports downscaling/upscaling for a pixelated look, color palette reduction, and various dithering algorithms. It is designed to be easily used as a command-line interface (CLI) or directly as a Python module.

## Features
- **Scaling**: Downscales and upscales using nearest neighbor to maintain crisp, blocky pixel edges.
- **Palette Reduction**: Reduces images to retro palettes of 16, 32, 64, or other limited sizes.
- **Dithering**: Includes standard Floyd-Steinberg dithering and a custom implementation of the Atkinson error diffusion algorithm (popular in early Macintosh UI).
- **Batch Processing**: Convert entire directories of images in parallel using multi-processing.
- **Easy Integration**: Use the flexible CLI or simply `import pixel_art_converter` into your Python projects.

## Installation

Ensure you have Python 3.8+ installed.

You can install this directly from source:
```bash
git clone <repository_url>
cd ai_to_pixel_art
pip install .
```

## CLI Usage

After installation, the `pixelart` command will be available in your terminal.

**Basic Usage:**
Convert a single image:
```bash
pixelart my_image.png my_output.png
```

Convert a whole directory of images (Batch processing):
```bash
pixelart ./input_images/ ./output_images/
```

**Advanced Options:**
You can specify the scaling factor, dithering algorithm, and number of colors:

```bash
pixelart ./input/ ./output/ --palette 32 --dither atkinson --pixel-size 6 --format PNG
```

### Options:
- `--palette`: Number of colors to use (Choices: 2, 4, 8, 16, 32, 64, 128, 256. Default: 16).
- `--dither`: The dithering method (`none`, `floyd-steinberg`, `atkinson`. Default: `floyd-steinberg`).
- `--pixel-size`: Block size/scaling factor (Integer or `"auto"`). Use `"auto"` to automatically calculate a target scaling factor based on your image's resolution to try and reach ~128 internal "pixels" across the shortest dimension. (Default: `"auto"`).
- `--format`: Set the output format explicitly (`PNG`, `JPEG`, etc.).
- `--workers`: Limit the number of parallel jobs for batch processing.

## Module Usage

You can easily integrate this directly into your Python scripts:

```python
from pixel_art_converter.converter import process_image, process_batch

# Convert a single image
process_image(
    input_path="my_image.png",
    output_path="pixel_art_output.png",
    palette_size=16,
    dither_method="atkinson",
    pixel_size="auto"
)

# Convert a batch of images in parallel
process_batch(
    input_dir="my_input_directory",
    output_dir="my_output_directory",
    palette_size=32,
    dither_method="floyd-steinberg",
    pixel_size=8
)
```
