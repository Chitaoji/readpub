"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from typing import Literal, TypedDict

logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)


class MetaData(TypedDict):
    """Dictionary of metadata."""

    title: str
    author: str
    filepath: str
    coverpath: str
    uploader: str
    uploadtime: str
    status: Literal["normal", "deleted", "pinned"]
    progress: tuple[float, float]
