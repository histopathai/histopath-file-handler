import math
import pyvips
import os 
from typing import Any, Tuple, Dict, List, Optional

from histopath_handler._core.interfaces import IFileLoader
from histopath_handler._core.models import ImageInfo
from histopath_handler._core.exceptions import ImageLoadingError
from histopath_handler._core.constants import METADATA_PROPERTY_MPP_X, METADATA_PROPERTY_MPP_Y
from histopath_handler._core.utils import calculate_scaled_dimensions
from histopath_handler._core.utils import get_file_extension
from .openslide_loader import OpenSlideLoader

class PyVipsLoader(IFileLoader):
    def load_image(self, file_path: str) -> pyvips.Image:
        try:
            return pyvips.Image.new_from_file(file_path)
        except pyvips.Error as e:
            raise ImageLoadingError(f"Failed to load image from {file_path}: {str(e)}")
        
    
    def get_image_info(self, file_path: str, image_object: pyvips.Image) -> ImageInfo:
        
        width_l0, height_l0 = image_object.width, image_object.height


        level_count = int(math.ceil(math.log2(max(width_l0, height_l0)))) + 1
        level_dimensions: List[Tuple[int, int]] = []
        
        for level in range(level_count):
            lvl_width, lvl_height = calculate_scaled_dimensions(width_l0, height_l0, level)
            level_dimensions.append((lvl_width, lvl_height))

        mpp_x, mpp_y = self._get_mpp_from_vips_metadata(image_object)

        # Attempt to gather other relevant metadata directly from pyvips
        metadata = {}
        try:
            for key in ["bands", "format", "xres", "yres", "resolution-unit", "vips-loader"]:
                # Check if property exists before trying to get it
                if image_object.get_typeof(key) != 0:
                    metadata[key] = image_object.get(key)
        
        except pyvips.Error:
            pass # Ignore if metadata key not found

        return ImageInfo(
            file_path=file_path,
            width_l0=width_l0,
            height_l0=height_l0,
            level_count=level_count,
            level_dimensions=level_dimensions,
            mpp_x=mpp_x,
            mpp_y=mpp_y,
            metadata=metadata
        )
    
    def _get_mpp_from_vips_metadata(self, image_object: pyvips.Image) -> Tuple[Optional[float],Optional[float]]:

        mpp_x, mpp_y = None, None
        try:
            xres = image_object.get("xres")
            yres = image_object.get("yres")
            res_unit = image_object.get("resolution-unit") # e.g., "cm", "inch"

            if xres and yres and res_unit:
                # Convert pixels per unit to microns per pixel
                if res_unit == "cm":
                    mpp_x = (1 / xres) * 10000 # 1 cm = 10000 microns
                    mpp_y = (1 / yres) * 10000
                elif res_unit == "inch":
                    mpp_x = (1 / xres) * 25400 # 1 inch = 25400 microns
                    mpp_y = (1 / yres) * 25400
        except pyvips.Error:
            print("Warning: Failed to retrieve MPP from image metadata. Using default values.")
            ## print metadata keys
            try:
                print("Available metadata keys:", image_object.get_fields())
            except pyvips.Error:
                pass
            pass # Metadata might not exist or be in an unexpected format
        return mpp_x, mpp_y

    def get_thumbnail(self, image_object: pyvips.Image, max_width: int) -> pyvips.Image:

        return image_object.thumbnail_image(max_width)
    
    def get_dimensions(self, image_object: pyvips.Image) -> Tuple[int, int]:
        return image_object.width, image_object.height

    def close_image(self, image_object: pyvips.Image):

        pass