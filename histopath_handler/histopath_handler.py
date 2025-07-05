import os
from typing import Any, Dict, Optional, Tuple
import shutil
import zipfile

# _core
from histopath_handler._core.models import ImageInfo, Region, Patch
from histopath_handler._core.exceptions import ImageLoadingError, InvalidRegionError, ExtractionError
from histopath_handler._core.constants import (
    DEFAULT_TILE_SIZE, DEFAULT_TILE_OVERLAP, DEFAULT_JPEG_QUALITY,
    DEFAULT_VIPS_COMPRESSION_METHOD, DEFAULT_DEEPZOOM_TILE_SUFFIX,
    DEFAULT_PATCH_OUTPUT_FORMAT, ROTATION_ANGLES, HPZ_FILE_EXTENSION,

)

from histopath_handler.file_loaders.loader_factory import FileLoaderFactory, OpenSlideLoader
from histopath_handler._core.interfaces import IFileLoader, IPyramidBuilder, IImageExtractor # Arayüzler
from histopath_handler.pyramid_builders.deepzoom_builder import DeepZoomBuilder
from histopath_handler.image_extractors.patch_extractor import PatchExtractor
from histopath_handler.image_extractors.region_extractor import RegionExtractor
from histopath_handler._core.utils import get_file_extension, get_basename_without_extension, write_json_file, zip_directory


class HistopathHandler:
    """
    The main facade class for the histopathology file handler library.
    Provides a high-level api to load, get information, extract patches/regions,
    and build pyramids from histopathology images.
    """
    def __init__(self,
                 file_path: str,
                 loader: Optional[IFileLoader] = None,
                 deepzoom_builder: Optional[IPyramidBuilder] = None,
                 patch_extractor: Optional[IImageExtractor] = None,
                 region_extractor: Optional[IImageExtractor] = None):


        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found at: {file_path}")

        self._file_path = file_path
        self._loaded_image_object = None # The underlying pyvips.Image or openslide.OpenSlide object
        self._image_info: Optional[ImageInfo] = None # Cached image information

        # Dependency Injection: Use provided implementations or default ones
        self._loader = loader if loader else FileLoaderFactory.get_loader(file_path)
        ext = get_file_extension(file_path)

        if ext in [".svs"]:
            self._info_loader = OpenSlideLoader()
        else:
            self._info_loader = self._loader



        self._deepzoom_builder = deepzoom_builder if deepzoom_builder else DeepZoomBuilder()
        self._patch_extractor = patch_extractor if patch_extractor else PatchExtractor()
        self._region_extractor = region_extractor if region_extractor else RegionExtractor()

        # Load the image upon initialization
        try:
            self._loaded_image_object = self._loader.load_image(file_path)
            self._info_loaded_image_object = self._info_loader.load_image(file_path)
            # Cache image info after successful load
            self._image_info = self._info_loader.get_image_info(file_path, self._info_loaded_image_object)
            print(f"[{self._file_path}] Image loaded and info retrieved.")
        except Exception as e:
            raise ImageLoadingError(f"Failed to load image '{file_path}': {e}")
           

    def get_image_info(self) -> ImageInfo:
        if not self._image_info:
            # Should ideally be set during init, but as a safeguard
            self._image_info = self._info_loader.get_image_info(self._file_path, self._info_loaded_image_object)
        return self._image_info
    

    def get_thumbnail(self, max_width: int = 500) -> Any:
        if not self._loaded_image_object:
            raise ImageLoadingError("No image is currently loaded.")
        return self._info_loader.get_thumbnail(self._info_loaded_image_object, max_width)


    def create_region(self,
                      left: int,
                      top: int,
                      width: int,
                      height: int,
                      level: int = 0) -> Region:
        
        if not self._image_info:
            raise RuntimeError("Image information not available.")

        # Basic validation: ensure region is within L0 bounds
        if (left < 0 or top < 0 or
            left + width > self._image_info.width_l0 or
            top + height > self._image_info.height_l0):
            raise InvalidRegionError(
                f"Requested region (L:{left}, T:{top}, W:{width}, H:{height}) "
                f"is out of image bounds ({self._image_info.width_l0}x{self._image_info.height_l0}) at level 0."
            )
        return Region(left, top, width, height, level)


    def extract_patch(self,
                      region: Region,
                      output_path: str,
                      output_format: str = DEFAULT_PATCH_OUTPUT_FORMAT,
                      quality: int = DEFAULT_JPEG_QUALITY,
                      rotate: int = 0
                      ) -> Patch:
        if not self._loaded_image_object:
            raise ImageLoadingError("No image is currently loaded for extraction.")

        # Pass the original loaded image object (likely pyvips.Image) to the extractor
        # The extractor will handle scaling the region to the correct dimensions for extraction.
        return self._patch_extractor.extract_region(
            self._loaded_image_object,
            region,
            output_path,
            output_format,
            quality,
            rotate
        )
    
    def extract_region(self,
                       region: Region,
                       output_path: str,
                       output_format: str = DEFAULT_PATCH_OUTPUT_FORMAT,
                       quality: int = DEFAULT_JPEG_QUALITY,
                       rotate: int = 0
                       ) -> Patch:
        
        if not self._loaded_image_object:
            raise ImageLoadingError("No image is currently loaded for extraction.")

        return self._region_extractor.extract_region(
            self._loaded_image_object,
            region,
            output_path,
            output_format,
            quality,
            rotate
        )
    

    def build_deepzoom_pyramid(self,
                               output_dir: str,
                               tile_size: int = DEFAULT_TILE_SIZE,
                               overlap: int = DEFAULT_TILE_OVERLAP,
                               suffix: str = DEFAULT_DEEPZOOM_TILE_SUFFIX,
                               quality: int = DEFAULT_JPEG_QUALITY,
                               angle: int = 0,
                               container: str = 'fs', # 'fs' for filesystem, 'zip' for single zip file
                               compression_method: int = DEFAULT_VIPS_COMPRESSION_METHOD,
                               background: Optional[Tuple[float, ...]] = None,
                               centre: bool = False
                               ) -> str:

        if not self._loaded_image_object:
            raise ImageLoadingError("No image is currently loaded to build a DeepZoom pyramid.")

        filename = get_basename_without_extension(self._image_info.get_filename())

        output_dir = os.path.join(output_dir, filename)

        # Ensure output_dir exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, filename)
        return self._deepzoom_builder.build_deepzoom_pyramid(
            self._loaded_image_object,
            output_path,
            tile_size,
            overlap,
            suffix,
            quality,
            angle,
            container,
            compression_method,
            background,
            centre
        )


    def build_hpz_archive(self,
                          output_dir: str,
                          tile_size: int = DEFAULT_TILE_SIZE,
                          overlap: int = DEFAULT_TILE_OVERLAP,
                          suffix: str = DEFAULT_DEEPZOOM_TILE_SUFFIX,
                          quality: int = DEFAULT_JPEG_QUALITY,
                          angle: int = 0,
                          background: Optional[Tuple[float, ...]] = None,
                          centre: bool = False,
                          meta_data: Optional[Dict[str, Any]] = None,
                          thumbnail = True
                          ) -> str:
        

        if not self._loaded_image_object:
            raise ImageLoadingError("No image is currently loaded to build a DeepZoom pyramid.")

        filename = get_basename_without_extension(self._image_info.get_filename())

        dzi_dir = os.path.join(output_dir, filename)
        # Ensure dzi_dir exists
        if not os.path.exists(dzi_dir):
            os.makedirs(dzi_dir, exist_ok=True)

        dzi_output_path = os.path.join(dzi_dir, filename)
        # Build the DeepZoom pyramid first
        self._deepzoom_builder.build_deepzoom_pyramid(
            image_object=self._loaded_image_object,
            output_path=dzi_output_path,
            tile_size=tile_size,
            overlap=overlap,
            suffix=suffix,
            quality=quality,
            angle=angle,
            container="fs",  # Always use filesystem for HPZ
            compression_method=DEFAULT_VIPS_COMPRESSION_METHOD,
            background=background,
            centre=centre
        )
            

        ## Create thumbnail if needed
        if thumbnail:
            thumb_path = os.path.join(dzi_dir, f"{filename}_thumb.jpg")
            self.get_thumbnail(max_width=400).write_to_file(thumb_path)
            
        if meta_data is None:
            meta_data = {}
            meta_data["from_name"] = filename
        else:
            if "from_name" not in meta_data:
                meta_data["from_name"] = filename

        # Write metadata JSON to a temporary file
        meta_json_temp_path = os.path.join(dzi_dir, "meta.json")
        write_json_file(meta_json_temp_path, meta_data)

        
        # Zip the DeepZoom directory into a single HPZ archive
        # This will include the DZI XML, tiles, and metadata JSON and thumbnail if created
        
        try:
            zip_directory(dzi_dir, os.path.join(output_dir, f"{filename}{HPZ_FILE_EXTENSION}"))
        except Exception as e:
            raise ExtractionError(f"Failed to create HPZ archive: {e}")
        finally:
            if (dzi_dir and os.path.exists(dzi_dir)):
                shutil.rmtree(dzi_dir)
        

    def close(self):
        if self._loaded_image_object: 
            self._loader.close_image(self._loaded_image_object)
            self._loaded_image_object = None
            if self._info_loaded_image_object:
                self._info_loader.close_image(self._info_loaded_image_object)
                self._info_loaded_image_object = None            
            self._image_info = None
            print(f"[{self._file_path}] Image closed and resources released.")


    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


    def __del__ (self):
        self.close()

