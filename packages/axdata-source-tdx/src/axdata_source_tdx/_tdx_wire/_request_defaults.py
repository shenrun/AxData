"""Provider-owned TDX request defaults kept outside protocol runtimes."""

DEFAULT_CODE_PAGE_SIZE = 1600
DEFAULT_QUOTE_BATCH_SIZE = 80
DEFAULT_FILE_CHUNK_SIZE = 30000

__all__ = [
    "DEFAULT_CODE_PAGE_SIZE",
    "DEFAULT_FILE_CHUNK_SIZE",
    "DEFAULT_QUOTE_BATCH_SIZE",
]
