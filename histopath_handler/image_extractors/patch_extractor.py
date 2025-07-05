import pyvips
import os
from typing import Any

from histopath_handler._core.interfaces import IImageExtractor
from histopath_handler._core.models import Region, Patch
from histopath_handler._core.exceptions import ExtractionError, InvalidRegionError
from histopath_handler._core.constants import DEFAULT_JPEG_QUALITY, DEFAULT_PATCH_OUTPUT_FORMAT
from .base_extractor import BaseImageExtractor


class PatchExtractor(BaseImageExtractor, IImageExtractor):
    """
    Extracts small, typically square image pacthes from a whole slide image 
    at a specified pyramid level. Ideal for machine learning dataset preparation
    """


    def extract_region(self,
                       image_object: Any,
                       region: Region,
                       output_path:str,
                       output_format:str = DEFAULT_PATCH_OUTPUT_FORMAT,
                       quality: int = DEFAULT_JPEG_QUALITY,
                       rotate: int = 0) -> Patch:
        
        print(f"Extracting patch {region} at level {region.level} to {output_path}.{output_format}...")

        scaled_region = region.get_scaled_region_at_level(region.level)

        try:
            extracted_vips_patch = image_object.extract_area(
                scaled_region.left, scaled_region.top, scaled_region.width, scaled_region.height
            )

            rotated_vips_patch = self._apply_rotation(extracted_vips_patch, rotate)

            saved_file_path = self._save_vips_image(rotated_vips_patch, output_path, output_format, quality)

            return Patch(
                data = saved_file_path,
                region= region,
                format= output_format,
                metadata={
                    'rotation': rotate,
                    'quality': quality,
                }
            )
        
        except InvalidRegionError as e:
            raise ExtractionError(f"Invalid region: {e}")
        except Exception as e:
            raise ExtractionError(f"Failed to extract patch: {e}")
        
