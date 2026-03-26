import os
import shutil
import pytest
from PIL import Image
from unittest.mock import patch
from pixel_art_converter.converter import (
    load_image, save_image, scale_image, reduce_palette,
    apply_floyd_steinberg, apply_atkinson, process_image, process_batch
)
from pixel_art_converter.cli import main as cli_main

@pytest.fixture
def temp_dir(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    # Create test image
    img = Image.new("RGB", (100, 100), color="blue")
    img_path = input_dir / "test.png"
    img.save(img_path)

    return input_dir, output_dir, img_path

def test_load_save_image(temp_dir):
    _, output_dir, img_path = temp_dir
    img = load_image(str(img_path))
    assert img.size == (100, 100)
    assert img.mode == "RGB"

    save_path = output_dir / "out.png"
    save_image(img, str(save_path))
    assert save_path.exists()

def test_scale_image(temp_dir):
    _, _, img_path = temp_dir
    img = load_image(str(img_path))
    scaled = scale_image(img, 10)
    assert scaled.size == (100, 100)
    assert scaled.mode == "RGB"

def test_reduce_palette(temp_dir):
    _, _, img_path = temp_dir
    img = load_image(str(img_path))
    palette_img = reduce_palette(img, 16)
    assert palette_img.mode == "P"
    assert len(palette_img.getpalette()) > 0

def test_apply_floyd_steinberg(temp_dir):
    _, _, img_path = temp_dir
    img = load_image(str(img_path))
    palette_img = reduce_palette(img, 16)
    fs_img = apply_floyd_steinberg(img, palette_img)
    assert fs_img.mode == "RGB"

def test_apply_atkinson(temp_dir):
    _, _, img_path = temp_dir
    img = load_image(str(img_path))
    palette_img = reduce_palette(img, 16)
    atk_img = apply_atkinson(img, palette_img)
    assert atk_img.mode == "RGB"

def test_process_image(temp_dir):
    _, output_dir, img_path = temp_dir
    out_path = output_dir / "proc.png"
    res = process_image(str(img_path), str(out_path), palette_size=16, dither_method="none", pixel_size=2)
    assert res.startswith("Success")
    assert out_path.exists()

def test_process_batch(temp_dir):
    input_dir, output_dir, _ = temp_dir
    # Create another image
    img = Image.new("RGB", (50, 50), color="red")
    img.save(input_dir / "test2.jpg")

    process_batch(str(input_dir), str(output_dir), palette_size=16, dither_method="floyd-steinberg", pixel_size=4)

    out_files = list(output_dir.iterdir())
    assert len(out_files) == 2

@patch("sys.argv", ["pixelart", "fake_input", "fake_output"])
@patch("pixel_art_converter.cli.process_image")
@patch("os.path.exists")
@patch("os.path.isfile")
def test_cli_single_image(mock_isfile, mock_exists, mock_process_image):
    mock_exists.return_value = True
    mock_isfile.return_value = True
    mock_process_image.return_value = "Success"

    cli_main()
    mock_process_image.assert_called_once()

@patch("sys.argv", ["pixelart", "fake_input", "fake_output", "--palette", "32"])
@patch("pixel_art_converter.cli.process_batch")
@patch("os.path.exists")
@patch("os.path.isdir")
def test_cli_batch(mock_isdir, mock_exists, mock_process_batch):
    mock_exists.return_value = True
    mock_isdir.return_value = True

    cli_main()
    mock_process_batch.assert_called_once()
