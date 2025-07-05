import openslide
import numpy as np
import pyvips # For converting OpenSlide thumbnail to pyvips.Image

from typing import Any, Tuple, Optional, Dict
from histopath_handler._core.interfaces import IFileLoader
from histopath_handler._core.models import ImageInfo
from histopath_handler._core.exceptions import ImageLoadingError
from histopath_handler._core.constants import METADATA_PROPERTY_MPP_X, METADATA_PROPERTY_MPP_Y



class OpenSlideLoader(IFileLoader):

    def load_image(self, file_path:str) -> Any:
        try:
            return openslide.OpenSlide(file_path)
        except openslide.OpenSlideError as e:
            raise ImageLoadingError(f"Failed to load image from {file_path}: {str(e)}")
        except Exception as e:
            raise ImageLoadingError(f"An unexpected error occurred while loading image: {str(e)}")
        

    
    def get_image_info(self, file_path: str, image_object: openslide.OpenSlide) -> ImageInfo:
        width_l0, height_l0 = image_object.dimensions

        level_count = image_object.level_count
        level_dimensions= image_object.level_dimensions

        mpp_x, mpp_y = self._get_mpp_from_openslide_properties(image_object.properties)
        

        metadata = dict(image_object.properties)

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
    
    def _get_mpp_from_openslide_properties(self, properties: Dict[str, str]) -> Tuple[Optional[float], Optional[float]]:
        mpp_x, mpp_y = None, None
        if openslide.PROPERTY_NAME_MPP_X in properties:
            mpp_x = float(properties[openslide.PROPERTY_NAME_MPP_X])
        if openslide.PROPERTY_NAME_MPP_Y in properties:
            mpp_y = float(properties[openslide.PROPERTY_NAME_MPP_Y])
        return mpp_x, mpp_y
    
    def get_dimensions(self, image_object: Any) -> Tuple[int, int]:
        if isinstance(image_object, openslide.OpenSlide):
            return image_object.dimensions
        else:
            raise TypeError("Expected an OpenSlide object to get dimensions.")

    def get_thumbnail(self, image_object: Any, max_width: int) -> pyvips.Image:
        
        width_l0, height_l0 = self.get_dimensions(image_object)
        if width_l0 <= max_width:
            size = (width_l0, height_l0)
        else:
            scale = max_width / width_l0
            size = (max_width, int(height_l0 * scale))

        thumbnail = image_object.get_thumbnail(size)
        # Convert OpenSlide thumbnail (PIL Image) to pyvips.Image
        thumbnail_np = np.array(thumbnail)
        thumbnail_vips = pyvips.Image.new_from_array(thumbnail_np)
        return thumbnail_vips
    
    def close_image(self, image_object: Any):
        if image_object:
            image_object.close()

            