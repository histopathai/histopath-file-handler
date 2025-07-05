from typing import Type, Dict
from histopath_handler._core.interfaces import IFileLoader
from histopath_handler._core.exceptions import UnsupportedFileFormatError
from histopath_handler._core.utils import get_file_extension
from .pyvips_loader import PyVipsLoader
from .openslide_loader import OpenSlideLoader


class FileLoaderFactory:

    _loaders: Dict[str, Type[IFileLoader]] = {}

    @classmethod
    def register_loader(cls, file_extension: str, loader_class: Type[IFileLoader]):

        cls._loaders[file_extension.lower()] = loader_class

    @classmethod
    def get_loader(cls, file_path: str) -> IFileLoader:

        file_ext = get_file_extension(file_path)

        if not cls._loaders:
            cls.register_loader(".tiff", PyVipsLoader)
            cls.register_loader(".tif", PyVipsLoader)
            cls.register_loader(".svs", PyVipsLoader)
            cls.register_loader(".png", PyVipsLoader)
            cls.register_loader(".jpg", PyVipsLoader)
            cls.register_loader(".jpeg", PyVipsLoader)

        loader_class =None


        if file_ext in [".svs"] and file_ext in cls._loaders:
            loader_class = cls._loaders[file_ext]
        elif file_ext in [".tiff", ".tif", ".png", ".jpg", ".jpeg"] and file_ext in cls._loaders:
            loader_class = cls._loaders[file_ext]
        else:
            print(f"No specific loader found for {file_ext}, using default PyVipsLoader")
            loader_class = PyVipsLoader
        if loader_class:
            return loader_class() 
        
        else:
            raise UnsupportedFileFormatError(f"No suitable loader found for file type: {file_ext}")
        

    

# Register default loaders
FileLoaderFactory.register_loader(".tiff", PyVipsLoader)
FileLoaderFactory.register_loader(".tif", PyVipsLoader)
FileLoaderFactory.register_loader(".svs", PyVipsLoader)
FileLoaderFactory.register_loader(".png", PyVipsLoader)
FileLoaderFactory.register_loader(".jpg", PyVipsLoader)
FileLoaderFactory.register_loader(".jpeg", PyVipsLoader)

        
"""
real 278.91
user 2109.01
sys 5890.37"""