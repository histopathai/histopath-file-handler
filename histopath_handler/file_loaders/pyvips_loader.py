import math
import pyvips
import os 
from typing import Any, Tuple, Dict, List, Optional

from histopath_handler._core.interfaces import IFileLoader
from histopath_handler._core.models import ImageInfo
from histopath_handler._core.exceptions import ImageLoadingError
from histopath_handler._core.constants import METADATA_PROPERTY_MPP_X, METADATA_PROPERTY_MPP_Y
from histopath_handler._core.utils import calculate_scaled_dimensions


class PyVipsLoader(IFileLoader):
    def load_image(self, file_path: str) -> pyvips.Image:

        try:
            return pyvips.Image.new_from_file(file_path)
        except pyvips.Error as e:
            raise ImageLoadingError(f"Failed to load image from {file_path}: {str(e)}")
        
    
    def get_image_info(self, file_path: str, loaded_image_object: pyvips.Image) -> ImageInfo:
        
        width_l0, height_l0 = loaded_image_object.width, loaded_image_object.height

        level_count = int(math.ceil(math.log2(max(width_l0, height_l0)))) + 1

        level_dimensions: List[Tuple[int, int]] = []

        for level in range(level_count):
            level_dimensions.w, level_dimensions.h = calculate_scaled_dimensions(width_l0, height_l0, level)
            level_dimensions.append((level_dimensions.w, level_dimensions.h))

        mpp_x, mpp_y = self._get_mpp_from_vips_metadata(loaded_image_object)

        metadata = {}

        try:

            for key in ["bands", "format", "xres", "yres", "resolution_unit", "vips-loader"]:
                if loaded_image_object.get_typeof(key) != 0:
                    metadata[key] = loaded_image_object.get(key)

        except pyvips.Error as e:
            pass

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
            y_res = image_object.get("yres")
            res_unit = image_object.get("resolution_unit") #"cm" "inch"

            if xres and y_res and res_unit:
                if res_unit == "cm":
                    mpp_x = (1 / xres) * 10000 # 1 cm = 10,000 microns
                    mpp_y = (1 / y_res) * 10000
                elif res_unit == "inch":
                    mpp_x = (1 / xres) * 25400 # 1 inch = 25,400 microns
                    mpp_y = (1 / y_res) * 25400

        except pyvips.Error as e:
            pass
        return mpp_x, mpp_y
    

    def get_thumbnail(self, loaded_image_object: pyvips.Image, max_width: int) -> pyvips.Image:

        return loaded_image_object.thumbnail_image(max_width)
    

    def close_image(self, loaded_image_object: pyvips.Image):

        """ Pyvips handles memorry automatically, so no explicit close is needed. """
        pass