from abc import ABC
import pyvips 
import os
from typing import Any, Tuple
import numpy as np

from histopath_handler._core.interfaces import IImageExtractor
from histopath_handler._core.models import Region, Patch
from histopath_handler._core.exceptions import ExtractionError, InvalidRegionError
from histopath_handler._core.constants import ROTATION_ANGLES
from histopath_handler._core.utils import calculate_scaled_coords, calculate_scaled_dimensions

class BaseImageExtractor(IImageExtractor, ABC):

    def _validate_region(self, image_object: Any, region: Region) -> None:
        
        if not hasattr(image_object, 'width') or not hasattr(image_object, 'height'):
            raise ExtractionError("Invalid image object provided.")
        
        scaled_region = region.get_scaled_region_at_level(region.level)

        img_width_at_level, img_height_at_level = image_object.width, image_object.height # Assuming this is the current image object's level

        if (scaled_region.left < 0 or
            scaled_region.top < 0 or
            scaled_region.left + scaled_region.width > img_width_at_level or
            scaled_region.top + scaled_region.height > img_height_at_level):
            raise InvalidRegionError(
                f"Requested region {scaled_region} is out of bounds for image "
                f"dimensions {img_width_at_level}x{img_height_at_level} at level {region.level}."
            )
        

    def _apply_rotation(self, vips_image: pyvips.Image, rotate: int) -> pyvips.Image:
        if rotate not in ROTATION_ANGLES:
            raise ValueError(f"Invalid rotation angle: {rotate}. Must be one of {ROTATION_ANGLES}.")

        if rotate == 90:
            return vips_image.rot90()
        elif rotate == 180:
            return vips_image.rot180()
        elif rotate == 270:
            return vips_image.rot270()
        
        return vips_image
    

    def _save_vips_image(self,
                         vips_image: pyvips.Image,
                         output_path: str,
                         output_format: str,
                         quality: int) -> str:
        save_options = {}
        output_path_with_ext = f"{os.path.splitext(output_path)[0]}.{output_format.lower()}"

        if output_format.lower() == 'jpg':
            save_options['Q'] = quality

        elif output_format.lower() == 'png':
            pass
        elif output_format.lower() == 'tiff' or output_format.lower() == 'tif':
            ## Tıff specific options can be added here
            pass
        else:
            raise ValueError(f"Unsupported output format: {output_format}. Supported formats are: jpg, png, tiff.")
        
        try:
            vips_image.write_to_file(output_path_with_ext, **save_options)
            return output_path_with_ext
        except Exception as e:
            raise ExtractionError(f"Failed to save image to {output_path_with_ext}: {str(e)}")
        