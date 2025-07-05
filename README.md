# histopath-file-handler

**histopath-file-handler** is a high-performance Python library for working with whole-slide histopathology images (e.g., SVS, TIFF, NDPI, MRXS). It allows you to extract metadata, generate thumbnails and patches, build DeepZoom pyramids, and package results into `.hp` archive files.

Powered by [`libvips`](https://libvips.github.io/libvips/) for efficient, lazy-loading and regional processing of gigapixel images.

---

## ✨ Features

- **Multi-format support**: SVS, TIFF, NDPI, MRXS
- **Image metadata**: dimensions, levels, MPP, etc.
- **Thumbnail generation**
- **Patch/region extraction** with rotation and format support
- **DeepZoom pyramid generation** as folder or `.zip`
- **HPZ archive creation**: packages `.dzi`, tiles, and metadata into `.hp` files
- **Python API and CLI**
- **High performance** via `libvips`
- **Clean, modular OOP design**

---

## 🔧 Installation

### 1. System Dependencies

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install libvips libvips-tools
sudo apt install openslide-tools libopenslide-dev  # Optional
```

**macOS (Homebrew):**

```bash
brew install vips
brew install openslide
```

**Windows:**

- Download binaries:
  - [libvips](https://github.com/libvips/libvips/releases)
  - [OpenSlide](https://openslide.org/download/)
- Extract and add their `bin/` folders to your `PATH`.

---

### 2. Python Setup

```bash
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .
```

---

## 🐍 Python API Example

A complete example is available in: [`examples/example.py`](examples/example.py)

It demonstrates:

- Loading a slide
- Extracting a patch
- Generating a DeepZoom pyramid
- Creating a `.hp` archive from tiles

---

## 🧰 CLI Usage

```bash
# Show help
python -m histopath_handler --help

# Get image metadata
python -m histopath_handler path/to/image.tif info

# Generate thumbnail
python -m histopath_handler path/to/image.tif thumbnail -o output/thumb.jpg -w 300

# Extract patch (256x256 from level 0)
python -m histopath_handler path/to/image.tif extract-patch --left 100 --top 100 --width 256 --height 256 --level 0 -o output/patch.png -f png

# Extract region (level 1, rotated, JPEG format)
python -m histopath_handler path/to/image.tif extract-region --left 500 --top 500 --width 1024 --height 768 --level 1 -o output/region.jpg -f jpg -q 80 -r 180

# Build DeepZoom pyramid (as folder)
python -m histopath_handler path/to/image.tif build-deepzoom -o output/deepzoom_fs -c fs --suffix .jpg -q 85

# Build DeepZoom pyramid (as zip)
python -m histopath_handler path/to/image.tif build-deepzoom -o output/deepzoom.zip -c zip --suffix .png

# Pack HPZ archive from folder
python -m histopath_handler path/to/image.tif pack-hpz --source-deepzoom-base-path output/deepzoom_fs -o output/final.hp -m metadata.json --zip-compression 9
```
