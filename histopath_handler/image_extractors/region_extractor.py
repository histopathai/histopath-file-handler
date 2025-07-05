import pyvips
import os
from typing import Any

from histopath_handler._core.interfaces import IImageExtractor
from histopath_handler._core.models import Region, Patch
from histopath_handler._core.exceptions import ExtractionError, InvalidRegionError
from histopath_handler._core.constants import DEFAULT_JPEG_QUALITY, DEFAULT_PATCH_OUTPUT_FORMAT
from .base_extractor import BaseImageExtractor


class RegionExtractor(BaseImageExtractor):
    """
    Extracts a larger rectangular region from a whole slide image at a specified
    pyramid level. Similar to PatchExtractor but for more general-purpose region extraction.
    """
    def extract_region(self,
                       image_object: Any, # Expected to be pyvips.Image or similar (handled by loader)
                       region: Region,
                       output_path: str,
                       output_format: str = DEFAULT_PATCH_OUTPUT_FORMAT,
                       quality: int = DEFAULT_JPEG_QUALITY,
                       rotate: int = 0
                       ) -> Patch:
        
        print(f"Extracting region {region} at level {region.level} to {output_path}.{output_format}...")

        scaled_region = region.get_scaled_region_at_level(region.level)

        try:

            extract_vips_region = image_object.extract_area(
                scaled_region.left, scaled_region.top, scaled_region.width, scaled_region.height
            )

            ## Apply rotation if needed
            rotated_vips_region = self._apply_rotation(extract_vips_region, rotate)

            # Save the region image
            saved_file_path = self._save_vips_image(rotated_vips_region, output_path, output_format, quality)
            
            return Patch(data=saved_file_path, 
                         region=region, 
                         format=output_format, 
                         metadata={
                             "rotation": rotate,
                            "quality": quality
                             }
                             )

        except InvalidRegionError as e:
            raise e
        except Exception as e:
            raise ExtractionError(f"Failed to extract region: {e}")
        
        