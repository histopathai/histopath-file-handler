import argparse
import os
import sys
import pyvips
import zipfile
import json

from histopath_handler.histopath_handler import HistopathHandler
from histopath_handler._core.models import Region
from histopath_handler._core.exceptions import (
    ImageLoadingError,
    InvalidRegionError,
    UnsupportedOperationError,
    ExtractionError,
)

from histopath_handler._core.constants import (
    DEFAULT_TILE_SIZE,
    DEFAULT_TILE_OVERLAP,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_VIPS_COMPRESSION_METHOD,
    DEFAULT_DEEPZOOM_TILE_SUFFIX,
    DEFAULT_PATCH_OUTPUT_FORMAT,
    ROTATION_ANGLES,
    HPZ_FILE_EXTENSION
)

def main():
    parser = argparse.ArgumentParser(
        description = "Histopathology Image Handler CLI Tool",
        formatter_class = argparse.RawTextHelpFormatter
    )

    parser.add_argument("image_path", help="Path to the histopathology image file.")

    subparsers = parser.add_subparsers(dest="command", help= "Available commands")

    info_parser = subparsers.add_parser("info", help="Get detailed information about the image.")

    # --- thumbnail commands ---
    thumbnail_parser = subparsers.add_parser("thumbnail", help="Generate a thumbnail of the image.")
    thumbnail_parser.add_argument("-o", "--output", required=True,
                                  help="Output path for the thumbnail (e.g., thumbnail.jpg).")
    thumbnail_parser.add_argument("-w", "--max-width", type=int, default=500,
                                  help="Maximum width of the thumbnail (default: 500).")


    # --- extract-patch commands ---
    extract_patch_parser = subparsers.add_parser("extract-patch", help="Extract a patch from the image.")
    extract_patch_parser.add_argument("--left", type=int, required=True, help="X-coordinate (level 0) of the top-left corner.")
    extract_patch_parser.add_argument("--top", type=int, required=True, help="Y-coordinate (level 0) of the top-left corner.")
    extract_patch_parser.add_argument("--width", type=int, required=True, help="Width of the patch.")
    extract_patch_parser.add_argument("--height", type=int, required=True, help="Height of the patch.")
    extract_patch_parser.add_argument("--level", type=int, default=0, help="Pyramid level for extraction (default: 0).")
    extract_patch_parser.add_argument("-o", "--output", required=True, help="Output path for the patch (e.g., patch.png).")
    extract_patch_parser.add_argument("-f", "--format", default=DEFAULT_PATCH_OUTPUT_FORMAT,
                                      choices=['png', 'jpg', 'tif'], help="Output format (default: png).")
    extract_patch_parser.add_argument("-q", "--quality", type=int, default=DEFAULT_JPEG_QUALITY,
                                      help="JPEG quality (1-100) for JPG format (default: 90).")
    extract_patch_parser.add_argument("-r", "--rotate", type=int, default=0,
                                      choices=ROTATION_ANGLES, help="Rotation angle (0, 90, 180, 270 degrees).")


    # --- extract-region commands (similar to extract-patch) ---
    extract_region_parser = subparsers.add_parser("extract-region", help="Extract a general rectangular region from the image.")
    extract_region_parser.add_argument("--left", type=int, required=True, help="X-coordinate (level 0) of the top-left corner.")
    extract_region_parser.add_argument("--top", type=int, required=True, help="Y-coordinate (level 0) of the top-left corner.")
    extract_region_parser.add_argument("--width", type=int, required=True, help="Width of the region (level 0).")
    extract_region_parser.add_argument("--height", type=int, required=True, help="Height of the region (level 0).")
    extract_region_parser.add_argument("--level", type=int, default=0, help="Pyramid level for extraction (default: 0).")
    extract_region_parser.add_argument("-o", "--output", required=True, help="Output path for the region (e.g., region.tif).")
    extract_region_parser.add_argument("-f", "--format", default=DEFAULT_PATCH_OUTPUT_FORMAT,
                                      choices=['png', 'jpg', 'tif'], help="Output format (default: png).")
    extract_region_parser.add_argument("-q", "--quality", type=int, default=DEFAULT_JPEG_QUALITY,
                                      help="JPEG quality (1-100) for JPG format (default: 90).")
    extract_region_parser.add_argument("-r", "--rotate", type=int, default=0,
                                      choices=ROTATION_ANGLES, help="Rotation angle (0, 90, 180, 270 degrees).")

    # --- build-deepzoom commands ---
    build_deepzoom_parser = subparsers.add_parser("build-deepzoom", help="Build a DeepZoom pyramid from the image.")
    build_deepzoom_parser.add_argument("-o", "--output-base-path", required=True,
                                       help="Base path for DeepZoom output (e.g., output/my_slide_dz). "
                                            "Will create my_slide_dz.dzi and my_slide_dz_files/ or my_slide_dz.zip.")
    build_deepzoom_parser.add_argument("-s", "--tile-size", type=int, default=DEFAULT_TILE_SIZE,
                                       help="Size of the tiles in pixels (default: 256).")
    build_deepzoom_parser.add_argument("--overlap", type=int, default=DEFAULT_TILE_OVERLAP,
                                       help="Overlap of tiles in pixels (default: 1).")
    build_deepzoom_parser.add_argument("--suffix", default=DEFAULT_DEEPZOOM_TILE_SUFFIX,
                                       help="Filename suffix for tiles (e.g., .jpg, .png) (default: .jpg).")
    build_deepzoom_parser.add_argument("-q", "--quality", type=int, default=DEFAULT_JPEG_QUALITY,
                                       help="JPEG quality (1-100) for JPG tiles (default: 90).")
    build_deepzoom_parser.add_argument("-a", "--angle", type=int, default=0,
                                       choices=ROTATION_ANGLES, help="Rotate image during save (0, 90, 180, 270 degrees).")
    build_deepzoom_parser.add_argument("-c", "--container", default='fs', choices=['fs', 'zip'],
                                       help="Pyramid container type: 'fs' for filesystem directories, 'zip' for single ZIP file (default: fs).")
    build_deepzoom_parser.add_argument("--vips-compression", type=int, default=DEFAULT_VIPS_COMPRESSION_METHOD,
                                       help="Vips internal compression level (0-9) for tiles (default: 0 - no compression).")
    build_deepzoom_parser.add_argument("--background", nargs=3, type=float,
                                       help="Background color as R G B values (e.g., 255 255 255 for white).")
    build_deepzoom_parser.add_argument("--centre", action="store_true",
                                       help="If set, center image in tile.")

    # --- pack-hpz commands ---
    pack_hpz_parser = subparsers.add_parser("pack-hpz", help="Pack an existing DeepZoom output into an HPZ archive.")
    pack_hpz_parser.add_argument("--source-deepzoom-base-path", required=True,
                                 help="Base path of the existing DeepZoom output (e.g., path/to/my_image_dz). "
                                      "Expects my_image_dz.dzi and my_image_dz_files/ to exist.")
    pack_hpz_parser.add_argument("-o", "--output-hpz-path", required=True,
                                 help="Full path for the output .hpz archive (e.g., output/my_packed_deepzoom.hp).")
    pack_hpz_parser.add_argument("-m", "--meta-data-json",
                                 help="Path to a JSON file containing metadata to include in the HPZ archive.")
    pack_hpz_parser.add_argument("--zip-compression", type=int, default=zipfile.ZIP_DEFLATED,
                                 choices=[zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED, zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA],
                                 help=f"ZIP compression method (default: {zipfile.ZIP_DEFLATED}). "
                                      f"Choices: {zipfile.ZIP_STORED} (no comp.), {zipfile.ZIP_DEFLATED} (default), "
                                      f"{zipfile.ZIP_BZIP2}, {zipfile.ZIP_LZMA}.")


    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)


    handler = None

    try:
        handler = HistopathHandler(args.image_path)

        if args.command == "info":
            image_info = handler.get_image_info()
            print("\n--- Image Information ---")
            print(f"File Path: {image_info.file_path}")
            print(f"Dimensions (L0): {image_info.width_l0}x{image_info.height_l0}")
            print(f"Pyramid Levels Count: {image_info.level_count}")
            print(f"All Dimensions: {image_info.all_dimensions}")
            print(f"MPP Info: {image_info.get_mpp()}")
            print(f"Metadata: {json.dumps(image_info.metadata, indent=2)}")


        elif args.command == "thumbnail":
            thumbnail_vips_image = handler.get_thumbnail(max_width=args.max_width)
            output_ext = os.path.splitext(args.output)[1].lower().lstrip('.')

            if output_ext not in ['jpg',  'jpeg', 'png', 'tif', 'tiff']:
                print(f"Error: Unsupported thumbnail output format '{output_ext} '. Supported formats are: jpg, png, tif.")
                sys.exit(1)
            
            thumbnail_vips_image.write_to_file(args.output)
            print(f"Thumbnail '{args.output}' created successfully.")

        elif args.command == "extract-patch":
            region = handler.create_region(args.left, args.top, args.width, args.height, args.level)
            extracted_patch_info = handler.extract_patch(
                region=region,
                output_path=args.output,
                output_format=args.format,
                quality=args.quality,
                rotate=args.rotate
            )
            print(f"Patch '{extracted_patch_info.data}' extracted successfully.")

        elif args.command == "extract-region":
            region = handler.create_region(args.left, args.top, args.width, args.height, args.level)
            extracted_region_info = handler.extract_region(
                region=region,
                output_path=args.output,
                output_format=args.format,
                quality=args.quality,
                rotate=args.rotate
            )
            print(f"Region '{extracted_region_info.data}' extracted successfully.")

        elif args.command == "build-deepzoom":
            output_path = handler.build_deepzoom_pyramid(
                output_base_path=args.output_base_path,
                tile_size=args.tile_size,
                overlap=args.overlap,
                suffix=args.suffix,
                quality=args.quality,
                angle=args.angle,
                container=args.container,
                compression_method=args.vips_compression,
                background=tuple(args.background) if args.background else None,
                centre=args.centre
            )

            print(f"DeepZoom pyramid created successfully at: {output_path}")

        elif args.command == "pack-hpz":
            meta_data = None
            if args.meta_data_json:
                if not os.path.exists(args.meta_data_json):
                    raise FileNotFoundError(f"Metadata JSON file not found: {args.meta_data_json}")
                with open(args.meta_data_json, 'r') as f:
                    meta_data = json.load(f)

            output_hpz_path = handler.build_hpz_archive(
                deepzoom_output_base_path=args.source_deepzoom_base_path,
                output_hpz_path=args.output_hpz_path,
                meta_data=meta_data,
                compression_level_zip=args.zip_compression
            )
            print(f"HPZ archive created successfully at: {output_hpz_path}")

            sys.exit(0)

    except (ImageLoadingError, InvalidRegionError, ExtractionError, UnsupportedOperationError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

    finally:
        if handler:
            handler.close_image()

if __name__ == "__main__":
    main()
