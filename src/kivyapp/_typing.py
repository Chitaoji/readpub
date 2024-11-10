"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional

from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar

from ..bookmanager import BookManager
from .font import KivyFont

if TYPE_CHECKING:
    from ..bookmanager._typing import Book
    from .bookcard import BookCard

logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)

UploadType = Literal["book", "bgim"]


# pylint: disable=unused-argument
class BasicApp(MDApp):
    """Basic App."""

    def __init__(self, **kwargs) -> None:
        self.bookmanager = BookManager(Path(""))
        self.fontmanager = KivyFont(Path(""), self)
        self.filemanager = MDFileManager()
        self.main_theme_style: str
        self.main_theme_palette: str
        self.reader_theme_style: str
        self.reader_theme_palette: str

        self.current_sort_rule: list[str]
        self.current_category: str

        self.has_filemanager: bool
        self.has_bgim: bool

        self.test_bookcard: "BookCard | None"
        self.prev_snackbar: MDSnackbar | None
        self.prev_input_menu: MDDropdownMenu | None

        self.upload_type: UploadType

        self.reader_disabled: bool
        self.book: "Book | None"

        super().__init__(**kwargs)

    def open_nav_drawer(self, name: str) -> None:
        """Open the nav-drawer."""

    def switch_theme(self) -> None:
        """Switch the theme-style."""

    def set_card(self, book: "Book") -> "BookCard":
        """Set a new book card."""
        if TYPE_CHECKING:
            return BookCard()

    def check_cards(self) -> None:
        """Check the bookcards."""

    def prepare_book(self, book: "Book") -> None:
        """Extract and picklize the book."""

    def open_menu(
        self,
        menu: MDDropdownMenu,
        caller: Any,
        relx: float = 0.0,
        rely: float = 0.0,
        absx: Optional[float] = None,
        absy: Optional[float] = None,
        on_left: bool = False,
        on_bottom: bool = False,
        check_ver_growth: bool = False,
        show_duration_x: Optional[float] = None,
    ) -> None:
        """Open the menu object."""

    def trans_color(self, color: list[str], transparency: float = 0.4) -> str:
        """Adjust the color according to the transparency."""
        if TYPE_CHECKING:
            return ""

    def trans_color_topbar(self, color: list[str], transparency: float = 0.0) -> str:
        """Adjust the color of topbars according to the transparency."""

    def set_bgim(self, image: str | None = None) -> None:
        """Set a background image."""
