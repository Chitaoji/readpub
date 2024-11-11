"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from typing import TYPE_CHECKING, Any, Literal

from kivymd.app import MDApp

from ..bookmanager import BookManager
from .font import KivyFont

if TYPE_CHECKING:
    from .bookcard import BookCardContainer
    from .importer import FileImporter
    from .input import InputMethod
    from .reader import Reader

logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)

ImportType = Literal["book", "bgim"]


# pylint: disable=unused-argument
class BasicApp(MDApp):
    """Basic App."""

    def __init__(self, **kwargs) -> None:
        self.bookmanager: BookManager
        self.importer: FileImporter
        self.font: KivyFont
        self.input: InputMethod
        self.cards: BookCardContainer
        self.reader: Reader

        self.main_theme_style: str
        self.main_theme_palette: str
        self.reader_theme_style: str
        self.reader_theme_palette: str

        self.has_bgim: bool
        self.nav_now: Any

        super().__init__(**kwargs)
