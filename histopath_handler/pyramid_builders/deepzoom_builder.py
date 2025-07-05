import pyvips
import os
from typing import Any, Tuple, Optional

from histopath_handler._core.interfaces import IPyramidBuilder
from histopath_handler._core.exceptions import ExtractionError, UnsupportedOperationError
from histopath_handler._core.constants import (
    DEFAULT_TILE_SIZE,
    DEFAULT_TILE_OVERLAP,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_VIPS_COMPRESSION_METHOD,
    DEFAULT_DEEPZOOM_TILE_SUFFIX
)

class DeepZoomBuilder(IPyramidBuilder):

    def build_deepzoom_pyramid(self,
                               image_object: pyvips.Image, # Expects a pyvips.Image object
                               output_path: str,     # e.g., "output/my_image" or "output/my_image.zip"
                               tile_size: int = DEFAULT_TILE_SIZE,
                               overlap: int = DEFAULT_TILE_OVERLAP,
                               suffix: str = DEFAULT_DEEPZOOM_TILE_SUFFIX,
                               quality: int = DEFAULT_JPEG_QUALITY,
                               angle: int = 0,
                               container: str = 'fs',     # 'fs' for filesystem, 'zip' for single zip file
                               compression_method: int = DEFAULT_VIPS_COMPRESSION_METHOD,
                               background: Optional[Tuple[float, ...]] = None,
                               centre: bool = False
                               ) -> str:
        

        print(f"Building DeepZoom pyramid to: {output_path} (container: {container})...")


        try:
            dzsave_options = {
                 'tile_size': tile_size,
                 'overlap': overlap,
                 'angle': angle,
                 'compression': compression_method,
                 'centre': centre,
                 'container': container,
             }

            if suffix.lower() == '.jpg' or suffix.lower() == '.jpeg':
                dzsave_options['suffix'] = f'.jpg[Q={quality}]'
            else:
                dzsave_options['suffix'] = suffix

            
            if background is not None:
                dzsave_options['background'] = list(background)

            print(output_path)
            image_object.dzsave(output_path, **dzsave_options)

        except UnsupportedOperationError as e:
            raise ExtractionError(f"Unsupported operation for DeepZoom pyramid: {str(e)}") from e        
        except pyvips.Error as e:
            raise ExtractionError(f"Failed to build DeepZoom pyramid: {str(e)}") from e
        except Exception as e:
            raise ExtractionError(f"An unexpected error occurred while building DeepZoom pyramid: {str(e)}") from e
        