import os
from PIL import Image
from pixel_art_converter.converter import process_batch, process_image

def main():
    print("Testing dithering and batch processing...")

    # Setup test directories
    input_dir = "test_input_dir"
    output_dir = "test_output_dir"
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Create test images
    for i in range(3):
        img_path = os.path.join(input_dir, f"test_image_{i}.png")
        img = Image.new("RGB", (50, 50), color=(100, 150 + i * 20, 200))
        img.save(img_path)

    # Test single image processing with different dithering methods
    test_img = os.path.join(input_dir, "test_image_0.png")

    print("Testing single image (None dither)")
    res1 = process_image(test_img, os.path.join(output_dir, "out_none.png"), dither_method="none")
    print(res1)

    print("Testing single image (Floyd-Steinberg dither)")
    res2 = process_image(test_img, os.path.join(output_dir, "out_fs.png"), dither_method="floyd-steinberg")
    print(res2)

    print("Testing single image (Atkinson dither)")
    res3 = process_image(test_img, os.path.join(output_dir, "out_atk.png"), dither_method="atkinson")
    print(res3)

    # Test batch processing
    print("Testing batch processing...")
    process_batch(input_dir, output_dir, palette_size=16, dither_method="none", pixel_size=4)

    # Check outputs exist
    out_files = os.listdir(output_dir)
    print("Output files:", out_files)

    # Clean up
    for file in os.listdir(input_dir):
        os.remove(os.path.join(input_dir, file))
    for file in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, file))
    os.rmdir(input_dir)
    os.rmdir(output_dir)

    print("Test finished successfully.")

if __name__ == "__main__":
    main()
