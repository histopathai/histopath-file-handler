import os
from histopath_handler.histopath_handler import HistopathHandler
from histopath_handler._core.models import Region
import zipfile

OUTPUT_DIR = "output_results"

os.makedirs(OUTPUT_DIR, exist_ok=True)


INPUT_IMAGE= "temp.tiff"



with HistopathHandler(INPUT_IMAGE) as handler:

    print("--- Image Info ---")
    info = handler.get_image_info()
    print(f"Size: {info.width_l0}x{info.height_l0}, Levels: {info.level_count}, MPP: {info.get_mpp()}")


   
    print("\n --- Thumbnail ---")
    thumb_path = os.path.join(OUTPUT_DIR, "thumb.jpg")
    handler.get_thumbnail(max_width=400).write_to_file(thumb_path)

    print("\n--- Patch (256x256, level 0, rotated) ---")
    patch_path = os.path.join(OUTPUT_DIR, "patch.png")
    patch_region = handler.create_region(left=100, top=100, width=256, height=256, level=0)
    handler.extract_patch(patch_region, patch_path, output_format='png', rotate=90)
    
    import time

    start = time.time()

    output_dir = os.path.join(OUTPUT_DIR)

    print("\n --- Extract HPZ ---")

    handler.build_hpz_archive(
        output_dir,
        tile_size=256,
        overlap=1,
        suffix=".jpg",
        quality=90,
        angle=0,
        background=None,
        meta_data={"description": "HPZ archive for histopathology image"},
        centre=False,
        thumbnail=True
    )

    end = time.time()
    print(f"HPZ archive created in {end - start:.2f} seconds at {output_dir}")