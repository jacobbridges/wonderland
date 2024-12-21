from pathlib import Path


class Settings:
    # +-----------------------------------------------------------------------+
    # |                                C O R E                                |
    # +-----------------------------------------------------------------------+
    NAME = "wonderland"
    VERSION = "0.1.0"
    BASE_DIR = Path(__file__).resolve().parent.parent
    SRC_DIR = BASE_DIR.parent
