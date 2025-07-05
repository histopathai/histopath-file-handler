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

    print("\n--- DeepZoom (ZIP) ---")
    dz_zip_path = os.path.join(OUTPUT_DIR, "deepzoom.zip")
    handler.build_deepzoom_pyramid(dz_zip_path, container='zip', suffix='.jpg', quality=88)

    print("\n--- HPZ Archive ---")
    hpz_path = os.path.join(OUTPUT_DIR, "packed.hp")
    temp_dz_path = os.path.join(OUTPUT_DIR, "deepzoom_fs")
    handler.build_deepzoom_pyramid(temp_dz_path, container='fs', suffix='.jpg', quality=85)
    handler.build_hpz_pyramid(
        deepzoom_output_base_path=temp_dz_path,
        output_hpz_path=hpz_path,
        meta_data={"origin": "example", "desc": "API-generated archive"},
        compression_level_zip=zipfile.ZIP_DEFLATED,
    )

    print("Done.")