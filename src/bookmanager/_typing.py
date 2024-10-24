"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from typing import Literal, NotRequired, Optional, TypedDict

logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)

StatusHint = Literal["normal", "deleted", "pinned"]


class MetaData(TypedDict):
    """Dictionary of metadata."""

    title: NotRequired[Optional[str]]
    author: NotRequired[Optional[str]]
    filepath: NotRequired[Optional[str]]
    coverpath: NotRequired[Optional[str]]
    uploader: NotRequired[Optional[str]]
    uploadtime: NotRequired[Optional[str]]
    status: NotRequired[Optional[StatusHint]]
    progress: NotRequired[Optional[tuple[float, float]]]
