import os
from typing import Any, Dict, Optional, Tuple
import zipfile

from histopath_handler._core.interfaces import ImageInfo, Region, Patch
from histopath_handler._core.exceptions import ImageLoadingError, InvalidRegionError, ExtractionError
from histopath_handler._core.constants import (
    DEFAULT_TILE_SIZE, DEFAULT_TILE_OVERLAP, DEFAULT_JPEG_QUALITY,
    DEFAULT_VIPS_COMPRESSION_METHOD, DEFAULT_DEEPZOOM_TILE_SUFFIX,
    DEFAULT_PATCH_OUTPUT_FORMAT, ROTATION_ANGLES, HPZ_FILE_EXTENSION
)

from histopath_handler.file_loaders.loader_factory import FileLoaderFactory
from histopath_handler._core.interfaces import IFileLoader, IPyramidBuilder, IImageExtractor # Arayüzler
from histopath_handler.pyramid_builders.deepzoom_builder import DeepZoomBuilder
from histopath_handler.pyramid_builders.hpz_builder import HPZBuilder
from histopath_handler.image_extractors.patch_extractor import PatchExtractor
from histopath_handler.image_extractors.region_extractor import RegionExtractor


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
                 hpz_builder: Optional[IPyramidBuilder] = None,
                 patch_extractor: Optional[IImageExtractor] = None,
                 region_extractor: Optional[IImageExtractor] = None):


        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self._file_path = file_path
        self._load_image_object = None
        self._image_info: Optional[ImageInfo] = None

        self._loader = loader if loader else FileLoaderFactory.get_loader(file_path)
        self._deepzoom_builder = deepzoom_builder if deepzoom_builder else DeepZoomBuilder()
        self._hpz_builder = hpz_builder if hpz_builder else HPZBuilder()
        self._patch_extractor = patch_extractor if patch_extractor else PatchExtractor()
        self._region_extractor = region_extractor if region_extractor else RegionExtractor()

        try:
            self._load_image_object = self._loader.load(file_path)
            self._image_info = self._loader.get_image_info(self._load_image_object)
            print(f"[{self._file_path}] Image loaded and info retrieved.")
        except ImageLoadingError as e:
            raise ImageLoadingError(f"Failed to load image from {file_path}: {e}")
        
    def get_image_info(self) -> ImageInfo:
        if not self._image_info:

            self._image_info = self._loader.get_image_info(self._file_path, self._loaded_image_object)
        return self._image_info
    

    def get_thumbnail(self, max_width: int = 500) -> Any:
        if not self._loaded_image_object:
            raise ImageLoadingError("No image is currently loaded.")
        return self._loader.get_thumbnail(self._loaded_image_object, max_width)


    def create_region(self,
                      left: int,
                      top: int,
                      width: int,
                      height: int,
                      level: int = 0) -> Region:
        if not self._image_info:
            raise RuntimeError("Image information not available.")
        
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
                               output_base_path: str,
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

        return self._deepzoom_builder.build_deepzoom_pyramid(
            self._loaded_image_object,
            output_base_path,
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
    
    def build_hpz_pyramid(self,
                          deepzoom_base_output: str,
                          output_hpz_path: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          compression_level_zip: int = zipfile.ZIP_DEFLATED
                          ) -> str:
        if not self._loaded_image_object:
            raise ImageLoadingError("No image is currently loaded to build an HPZ archive.")
        
        return self._hpz_builder.build_hpz_archive(
            deepzoom_base_output,
            output_hpz_path,
            metadata,
            compression_level_zip
        )
    

    def close(self):
        if self._load_image_object:
            self._loader.close_image(self._load_image_object)
            self._load_image_object = None
            self._image_info = None
            print(f"[{self._file_path}] Image closed and resources released.")


    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


    def __del__ (self):
        self.close()

