class HistopathFileHandlerError(Exception):
    """Base class for all exceptions raised by the histopath file handler."""
    pass

class ImageLoadingError(HistopathFileHandlerError):
    """Raised when an image cannot be loaded."""
    pass

class InvalidRegionError(HistopathFileHandlerError):
    """Raised when an invalid region is specified."""
    pass

class MetadataParsingError(HistopathFileHandlerError):
    """Raised when metadata cannot be parsed."""
    pass

class UnsupportedFileFormatError(HistopathFileHandlerError):
    """Raised when an unsupported file format is encountered."""
    pass

class UnsupportedOperationError(HistopathFileHandlerError):
    """Raised when an unsupported operation is attempted."""
    pass

class ExtractionError(HistopathFileHandlerError):
    """Raised when an error occurs during data extraction."""
    pass