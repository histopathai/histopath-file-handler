import pyvips
import zipfile
import os
import shutil
from typing import Any, Tuple, Optional, Dict
from histopath_handler._core.interfaces import IPyramidBuilder
from histopath_handler._core.models import Region
from histopath_handler._core.exceptions import ExtractionError, UnsupportedOperationError
from histopath_handler._core.constants import (
    DEFAULT_TILE_SIZE,
    DEFAULT_TILE_OVERLAP,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_VIPS_COMPRESSION_METHOD,
    DEFAULT_DEEPZOOM_TILE_SUFFIX,
    HPZ_FILE_EXTENSION,
    HPZ_META_JSON_FILENAME,
    HPZ_DZI_BASE_NAME
)

from histopath_handler._core.utils import write_json_file, get_basename_without_extension


class HPZBuilder(IPyramidBuilder):

    def build_deepzoom_pyramid(self, *args, **kwargs) -> str:
        raise UnsupportedOperationError(
            "HPZBuilder specializes in .hp archive creation. "
            "Use DeepZoomBuilder for standard DeepZoom pyramid creation."
        )
    

    def build_hpz_archive(self,
                          deepzoom_base_output: str,
                          output_hpz_path: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          compression_level_zip: int = zipfile.ZIP_DEFLATED
                        ) -> str:
         
        if not output_hpz_path.endswith(HPZ_FILE_EXTENSION):
             output_hpz_path += HPZ_FILE_EXTENSION

        dzi_xml_source_path = f"{deepzoom_base_output}.dzi"
        dzi_tiles_source_folder = f"{deepzoom_base_output}_files"
         
        if not os.path.exists(dzi_xml_source_path):
            raise ExtractionError(f"DZI XML file not found: {dzi_xml_source_path}")
        
        if not os.path.exists(dzi_tiles_source_folder):
            raise ExtractionError(f"DZI tiles folder not found: {dzi_tiles_source_folder}")
        
        temp_meta_dir = None
        meta_json_temp_path = None
        if metadata is not None:
            temp_meta_dir_suffix = get_basename_without_extension(output_hpz_path)
            temp_meta_dir = os.path.join(os.path.dirname(output_hpz_path) or '.', f"temp_meta_{temp_meta_dir_suffix}")
            os.makedirs(temp_meta_dir, exist_ok=True)
            meta_json_temp_path = os.path.join(temp_meta_dir, HPZ_META_JSON_FILENAME)

        try:
            print(f"Creating HPZ archive at: {output_hpz_path} from existing DeepZoom output: {deepzoom_base_output}...")

            with zipfile.ZipFile(output_hpz_path, 'w', compression=compression_level_zip) as hpz_archive:

                hpz_archive.write(dzi_xml_source_path, arcname=f"{HPZ_DZI_BASE_NAME}.dzi")
                print(f"Added {dzi_xml_source_path} as {HPZ_DZI_BASE_NAME}.dzi to archive.")

                for root, _, files in os.walk(dzi_tiles_source_folder):
                    for file in files:
                        file_path = os.path.join(root, file)

                        arcname = os.path.relpath(file_path, dzi_tiles_source_folder)
                        arcname = os.path.join(f"{HPZ_DZI_BASE_NAME}_files", arcname)

                        hpz_archive.write(file_path, arcname=arcname)

                print(f"Added {dzi_tiles_source_folder} contents to archive.")

                if metadata is not None:
                    write_json_file(metadata, meta_json_temp_path)
                    hpz_archive.write(meta_json_temp_path, arcname=HPZ_META_JSON_FILENAME)
                    print(f"Added metadata to archive at {HPZ_META_JSON_FILENAME}.")
            
            print(f"HPZ archive created successfully at: {output_hpz_path}")
            return output_hpz_path
        except zipfile.BadZipFile as e:
            raise ExtractionError(f"Failed to create HPZ archive: {str(e)}") from e
        except Exception as e:
            raise ExtractionError(f"An unexpected error occurred while creating HPZ archive: {str(e)}") from e
        finally:
            if temp_meta_dir and os.path.exists(temp_meta_dir):
                shutil.rmtree(temp_meta_dir)
                print(f"Temporary metadata directory {temp_meta_dir} cleaned up.")

        