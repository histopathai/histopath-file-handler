import os 
import json
import math
from typing import Dict, Any, Tuple


def validate_file_path(file_path: str):
    if not isinstance(file_path, str):
        raise FileNotFoundError(f"File not found or invalid path: {file_path}")
    
def read_json_file(file_path: str) -> Dict[str, Any]:
    validate_file_path(file_path)
    with open(file_path, 'r') as file:
        return json.load(file)
    
def calculate_scaled_dimensions(width_l0: int, height_l0: int, level: int) -> Tuple[int, int]:
    if level < 0:
        raise ValueError("Level must be a non-negative integer.")
    
    scale_factor = 2 ** level
    
    return width_l0 // scale_factor, height_l0 // scale_factor

def calculate_scaled_coords(left_l0: int, top_l0: int, level: int) -> Tuple[int, int]:
    if level < 0:
        raise ValueError("Level must be a non-negative integer.")
    
    scale_factor = 2 ** level
    
    return left_l0 // scale_factor, top_l0 // scale_factor

def get_basename_without_extension(file_path: str) -> str:
    validate_file_path(file_path)
    return os.path.splitext(os.path.basename(file_path))[0]

def get_file_extension(file_path: str) -> str:
    validate_file_path(file_path)
    return os.path.splitext(file_path)[1].lower()

def microns_to_pixels(microns: float, mpp: float) -> int:
    if mpp <= 0:
        raise ValueError("MPP must be a positive value.")
    return int(round(microns / mpp))

def pixels_to_microns(pixels: int, mpp: float) -> float:
    if mpp <= 0:
        raise ValueError("MPP must be a positive value.")
    return pixels * mpp

def write_json_file(file_path: str, data: Dict[str, Any]):
    validate_file_path(file_path)
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)