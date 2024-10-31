"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from typing import TYPE_CHECKING, Literal, NotRequired, Optional, TypedDict, TypeVar

if TYPE_CHECKING:
    from .textmaster import FakeParagraph


logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)


T = TypeVar("T")

TitleLevel = Literal["h1", "h2", "h3", "h4", "h5", "h6"]
TextMeasureType = Literal["plain", "cached", "same-sized"]
StatusHint = Literal["normal", "deleted", "pinned"]
MetaDataKey = Literal[
    "title",
    "author",
    "filepath",
    "coverpath",
    "uploader",
    "uploadtime",
    "status",
    "progress",
]


class MetaData(TypedDict):
    """Dictionary of metadata."""

    title: NotRequired[Optional[str]]
    author: NotRequired[Optional[str]]
    filepath: NotRequired[Optional[str]]
    coverpath: NotRequired[Optional[str]]
    uploader: NotRequired[Optional[str]]
    uploadtime: NotRequired[Optional[str]]
    status: NotRequired[Optional[StatusHint]]
    extracted: NotRequired[Optional[bool]]
    progress: NotRequired[Optional[tuple[float, float, float]]]
    content: NotRequired[Optional[list[str]]]


if TYPE_CHECKING:
    para = list[T] | FakeParagraph

    Paragraph = para[str]
    Page = list[para[str]]
    Chapter = list[list[para[str]]]
