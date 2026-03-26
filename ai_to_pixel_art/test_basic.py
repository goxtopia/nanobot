import os
from PIL import Image
from pixel_art_converter.converter import load_image, save_image, scale_image, reduce_palette

def main():
    print("Testing basic image processing...")
    # Create a simple test image
    test_img_path = "test_input.png"
    img = Image.new("RGB", (100, 100), color="blue")

    # Add some variation to the image
    for x in range(50, 100):
        for y in range(50, 100):
            img.putpixel((x, y), (255, 0, 0))
    for x in range(0, 50):
        for y in range(50, 100):
            img.putpixel((x, y), (0, 255, 0))
    for x in range(50, 100):
        for y in range(0, 50):
            img.putpixel((x, y), (0, 0, 255))

    img.save(test_img_path)

    # Test loading
    loaded_img = load_image(test_img_path)
    print("Image loaded:", loaded_img.size, loaded_img.mode)

    # Test scaling
    scaled_img = scale_image(loaded_img, 10)
    print("Image scaled:", scaled_img.size, scaled_img.mode)

    # Test palette reduction
    reduced_img = reduce_palette(scaled_img, 16)
    print("Image palette reduced:", reduced_img.size, reduced_img.mode)

    # Test saving
    test_out_path = "test_output.png"
    save_image(reduced_img, test_out_path)
    print("Image saved:", os.path.exists(test_out_path))

    # Clean up
    os.remove(test_img_path)
    os.remove(test_out_path)
    print("Test finished successfully.")

if __name__ == "__main__":
    main()
