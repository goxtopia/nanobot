import os
import concurrent.futures
from pathlib import Path
from typing import Optional
from PIL import Image

def load_image(filepath: str) -> Image.Image:
    """Load an image from the specified filepath."""
    return Image.open(filepath).convert("RGB")

def save_image(img: Image.Image, filepath: str, format: str = None) -> None:
    """Save an image to the specified filepath."""
    if format is None:
        # Infer format from extension or default to PNG
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ('.jpg', '.jpeg'):
            format = 'JPEG'
        else:
            format = 'PNG'
    img.save(filepath, format=format)

def scale_image(img: Image.Image, pixel_size: int) -> Image.Image:
    """
    Scale the image down and then back up to create a pixelated effect.
    """
    if pixel_size <= 1:
        return img

    width, height = img.size
    new_width = width // pixel_size
    new_height = height // pixel_size

    # Scale down
    small_img = img.resize((new_width, new_height), Image.Resampling.BILINEAR)

    # Scale back up using nearest neighbor to keep it blocky
    pixelated_img = small_img.resize((width, height), Image.Resampling.NEAREST)
    return pixelated_img

def reduce_palette(img: Image.Image, num_colors: int) -> Image.Image:
    """
    Reduce the image to a specific number of colors using a palette.
    Note: We separate dithering into its own step so we can implement custom dithering algorithms.
    """
    # Pillow's quantize function can reduce colors without dithering
    # Note: quantize returns an image in "P" mode (palette based)
    quantized_img = img.quantize(colors=num_colors, dither=Image.Dither.NONE)
    return quantized_img

def apply_floyd_steinberg(img: Image.Image, palette_img: Image.Image) -> Image.Image:
    """
    Apply Floyd-Steinberg dithering using the palette from `palette_img`.
    """
    # quantize with Floyd-Steinberg (Pillow's default FLOYDSTEINBERG)
    # The quantize function will apply dithering to `img` using the palette of `palette_img`
    # if we don't pass an explicit palette, we can use the `palette_img` directly.
    return img.quantize(palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG).convert("RGB")

def apply_atkinson(img: Image.Image, palette_img: Image.Image) -> Image.Image:
    """
    Apply Atkinson dithering to `img` using the palette from `palette_img`.
    Atkinson dithering error diffusion:
    x 1 1
    1 1 1
      1
    (divisor = 8)
    """
    img = img.convert("RGB")
    width, height = img.size

    # Use getdata() if get_flattened_data is not available (for older Pillow versions)
    if hasattr(img, 'get_flattened_data'):
        pixels = list(img.get_flattened_data())
    else:
        pixels = list(img.getdata())

    # Get palette colors from the palette image
    palette = palette_img.getpalette()
    if palette is None:
         # Fallback if no palette is found
         return img

    # Reconstruct RGB tuples from the palette
    num_colors = len(palette) // 3
    colors = []
    for i in range(num_colors):
        colors.append((palette[i*3], palette[i*3+1], palette[i*3+2]))

    def find_closest_color(pixel, colors):
        r, g, b = pixel
        min_dist = float('inf')
        closest = colors[0]
        for cr, cg, cb in colors:
            dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
            if dist < min_dist:
                min_dist = dist
                closest = (cr, cg, cb)
        return closest

    # Create a mutable copy of the image data to propagate errors
    img_data = [[list(pixels[y * width + x]) for x in range(width)] for y in range(height)]

    for y in range(height):
        for x in range(width):
            old_pixel = tuple(img_data[y][x])
            new_pixel = find_closest_color(old_pixel, colors)
            img_data[y][x] = list(new_pixel)

            # Calculate quantization error
            err_r = old_pixel[0] - new_pixel[0]
            err_g = old_pixel[1] - new_pixel[1]
            err_b = old_pixel[2] - new_pixel[2]

            # Atkinson matrix:
            #   X  1/8 1/8
            # 1/8 1/8 1/8
            #    1/8

            error_multiplier = 1.0 / 8.0

            offsets = [
                (1, 0), (2, 0),
                (-1, 1), (0, 1), (1, 1),
                (0, 2)
            ]

            for dx, dy in offsets:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    img_data[ny][nx][0] = int(img_data[ny][nx][0] + err_r * error_multiplier)
                    img_data[ny][nx][1] = int(img_data[ny][nx][1] + err_g * error_multiplier)
                    img_data[ny][nx][2] = int(img_data[ny][nx][2] + err_b * error_multiplier)

                    # Clamp to 0-255
                    for i in range(3):
                        if img_data[ny][nx][i] < 0:
                            img_data[ny][nx][i] = 0
                        elif img_data[ny][nx][i] > 255:
                            img_data[ny][nx][i] = 255

    # Flatten and put data back
    flat_data = [tuple(p) for row in img_data for p in row]
    out_img = Image.new("RGB", (width, height))
    out_img.putdata(flat_data)
    return out_img

from typing import Optional, Union

def calculate_auto_pixel_size(img: Image.Image, target_pixels: int = 128) -> int:
    """
    Calculate an appropriate pixel-size scaling factor based on the shortest side
    of the image to achieve roughly `target_pixels` across that dimension.
    """
    width, height = img.size
    shortest_side = min(width, height)

    if shortest_side <= target_pixels:
        return 1

    # Calculate the scaling factor
    return max(1, shortest_side // target_pixels)

def process_image(
    input_path: str,
    output_path: str,
    palette_size: int = 16,
    dither_method: str = "floyd-steinberg",
    pixel_size: Union[int, str] = "auto",
    output_format: Optional[str] = None
) -> str:
    """
    Process a single image to pixel art.
    """
    try:
        img = load_image(input_path)

        # Calculate auto pixel size if requested
        actual_pixel_size = pixel_size
        if str(pixel_size).lower() == "auto":
            actual_pixel_size = calculate_auto_pixel_size(img)
        else:
            try:
                actual_pixel_size = int(pixel_size)
            except ValueError:
                return f"Error processing {input_path}: Invalid pixel_size '{pixel_size}'"

        # 1. Scale image to create pixelated effect
        pixelated = scale_image(img, actual_pixel_size)

        # 2. Get a target palette (no dithering yet)
        palette_img = reduce_palette(pixelated, palette_size)

        # 3. Apply dithering
        if dither_method == "none":
            final_img = palette_img.convert("RGB")
        elif dither_method == "floyd-steinberg":
            final_img = apply_floyd_steinberg(pixelated, palette_img)
        elif dither_method == "atkinson":
            final_img = apply_atkinson(pixelated, palette_img)
        else:
            raise ValueError(f"Unknown dither method: {dither_method}")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Save image
        save_image(final_img, output_path, format=output_format)
        return f"Success: {input_path} -> {output_path}"
    except Exception as e:
        return f"Error processing {input_path}: {e}"

def process_batch(
    input_dir: str,
    output_dir: str,
    palette_size: int = 16,
    dither_method: str = "floyd-steinberg",
    pixel_size: Union[int, str] = "auto",
    output_format: Optional[str] = None,
    max_workers: Optional[int] = None
):
    """
    Process a directory of images in parallel.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input directory {input_dir} does not exist or is not a directory.")
        return

    output_path.mkdir(parents=True, exist_ok=True)

    # Collect all image files
    valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
    image_files = []
    for file in input_path.iterdir():
        if file.is_file() and file.suffix.lower() in valid_extensions:
            image_files.append(file)

    if not image_files:
        print(f"No image files found in {input_dir}.")
        return

    print(f"Found {len(image_files)} images. Starting batch processing...")

    # Prepare arguments for parallel execution
    tasks = []
    for img_file in image_files:
        out_file = output_path / img_file.name
        if output_format:
            # Change extension if format is specified
            ext = f".{output_format.lower()}"
            if output_format.lower() == 'jpeg':
                ext = '.jpg'
            out_file = out_file.with_suffix(ext)

        tasks.append((
            str(img_file),
            str(out_file),
            palette_size,
            dither_method,
            pixel_size,
            output_format
        ))

    # Run in parallel
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_image, *task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # Print results
    success_count = 0
    for res in results:
        print(res)
        if res.startswith("Success"):
            success_count += 1

    print(f"\nBatch processing complete. Successfully processed {success_count}/{len(image_files)} images.")
