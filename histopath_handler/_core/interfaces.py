from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional
import pyvips
import openslide
from histopath_handler._core.models import Region, ImageInfo, Patch
from histopath_handler._core.exceptions import UnsupportedOperationError


class IFileLoader(ABC):
    @abstractmethod
    def load_image(self, file_path: str) -> Any:
        pass

    @abstractmethod
    def get_image_info(self, file_path:str, image_object:Any) -> ImageInfo:
        pass

    @abstractmethod
    def get_thumbnail(self, image_object: Any, max_width: int) -> pyvips.Image:
        pass

    @abstractmethod
    def close_image(self, image_object: Any):
        pass

    @abstractmethod
    def get_dimensions(self, image_object: Any) -> Tuple[int, int]:
        """Get the dimensions of the image object."""
        pass



class IImageExtractor(ABC):
    @abstractmethod
    def extract_region(self, 
                       image_object: Any,
                       region: Region,
                       output_path: str,
                       output_format: str,
                       quality: int = 90,
                       rotate: int = 0) -> Patch:
        pass


class IPyramidBuilder(ABC):
    @abstractmethod
    def build_deepzoom_pyramid(self,
                               image_object: str,
                               tile_size: int,
                               overlap: int,
                               suffix: str,
                               quality: int,
                               container: str,
                               compression_method: int,
                               background: Optional[Tuple[float, ...]] = None,
                               centre: bool = False) -> str:
        
        pass

   
class IMetadataParser(ABC):
    @abstractmethod
    def parse_metadata(self, image_object: Any) -> Dict[str, Any]:
        """Parse metadata from the image object."""
        pass


class IViewer(ABC):
    @abstractmethod
    def show_preview(self, image_object: Any, region: Optional[Region] = None) -> None:
        """Display a preview of the image or a specific region."""
        pass

    @abstractmethod
    def select_region_interactivcely(self, image_object: Any) -> Region:
        """Allow the user to select a region interactively."""
        pass

