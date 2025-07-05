import openslide
import numpy as np
import pyvips # For converting OpenSlide thumbnail to pyvips.Image

from typing import Any, Tuple, Optional, List, Dict
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
        

    
    def get_image_info(self, file_path: str, loaded_image_object: openslide.OpenSlide) -> ImageInfo:
        width_l0, height_l0 = loaded_image_object.dimensions

        level_count = loaded_image_object.level_count
        level_dimensions= loaded_image_object.level_dimensions

        mpp_x, mpp_y = self._get_mpp_from_openslide_metadata(loaded_image_object.properties)
        

        metadata = dict(loaded_image_object.properties)

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
    
    def get_thumbnail(self, loaded_image_object: Any, max_width: int) -> pyvips.Image:
        width_l0, height_l0 = self.get_dimensions(loaded_image_object)
        thumbnail_height = int( height_l0 *max_width / width_l0)
        thumbnail_pil = loaded_image_object.get_thumbnail((max_width, thumbnail_height))

        np_img = np.array(thumbnail_pil)
        bands = np_img.shape[2] if len(np_img.shape) == 3 else 1

        return pyvips.Image.new_from_memory(
            np_img.tobytes(),
            width=np_img.shape[1],
            height=np_img.shape[0],
            bands=bands,
            format='uchar'
        )
    
    def close_image(self, loaded_image_object: Any):
        if loaded_image_object:
            loaded_image_object.close()

            