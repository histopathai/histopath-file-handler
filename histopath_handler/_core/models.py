from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from .utils import calculate_scaled_coords, calculate_scaled_dimensions
from .constants import METADATA_PROPERTY_MPP_X, METADATA_PROPERTY_MPP_Y


@dataclass
class Region:
    left: int
    top: int
    width: int
    height: int
    level: int = 0


    def get_scaled_region_at_level(self, target_level: int) -> 'Region':
        if target_level < 0:
            raise ValueError("Target level must be a non-negative integer.")
        
        scaled_left, scaled_top = calculate_scaled_coords(self.left, self.top, target_level)
        scaled_width, scaled_height = calculate_scaled_dimensions(self.width, self.height, target_level)

        return Region(
            left=scaled_left,
            top=scaled_top,
            width=scaled_width,
            height=scaled_height,
            level=target_level
        )
    
    def __str__(self):
        return (f"Region(L={self.left}, T={self.top}, W={self.width}, H={self.height}, "
                f"Level={self.level})")
    

@dataclass
class ImageInfo:
    file_path: str
    width_l0: int
    height_l0: int
    level_count: int
    level_dimensions: List[Tuple[int, int]] = field(default_factory=list)
    mpp_x : Optional[float] = None
    mpp_y : Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_dimensions_at_level(self, level: int) -> Tuple[int, int]:
        if not (0 <= level < self.level_count):
            raise IndexError(f"Level {level} is out of bounds for this image.")
        return self.level_dimensions[level]
    def get_mpp(self) -> Dict[str, Optional[float]]:
        return {METADATA_PROPERTY_MPP_X: self.mpp_x, METADATA_PROPERTY_MPP_Y: self.mpp_y}


@dataclass
class Patch:
    data: Any
    region: Region
    format: str
    metadata: Dict[str, Any] = field(default_factory=dict)