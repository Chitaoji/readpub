"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from typing import TYPE_CHECKING, Literal, NotRequired, Optional, TypedDict, TypeVar

if TYPE_CHECKING:
    from .book import Book
    from .textmaster import BookImage, BookIndex, BookTitle


logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)


T = TypeVar("T")

TitleLevel = int
TextMeasureMethod = Literal["plain", "same-sized", "cached", "mixed"]
StatusHint = Literal["normal", "deleted", "pinned"]
MetaDataKey = Literal[
    "title",
    "author",
    "filepath",
    "coverpath",
    "uploader",
    "uploadtime",
    "status",
    "pagenow",
    "pagemax",
    "is_ready",
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
    pagenow: NotRequired[Optional[float]]
    pagemax: NotRequired[Optional[float]]
    is_ready: NotRequired[Optional[bool]]


if TYPE_CHECKING:
    para = list[T] | BookIndex | BookTitle | BookImage

    RawParagraph = str | BookIndex | BookTitle | BookImage
    Paragraph = para[str]
    Page = list[para[str]]
    Chapter = list[list[para[str]]]
