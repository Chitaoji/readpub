"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

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


# pylint: disable=unused-argument
class BasicApp(MDApp):
    """Basic App."""

    def __init__(self, **kwargs) -> None:
        self.bookmanager = BookManager(Path(""))
        self.fontmanager = KivyFont(Path(""), self)
        self.filemanager = MDFileManager()

        self.current_sort_rule: list[str]
        self.category_status: str

        self.has_filemanager: bool
        self.test_bookcard: "BookCard | None"
        self.prev_snackbar: MDSnackbar | None

        self.reader_disabled: bool
        self.book: "Book | None"

        super().__init__(**kwargs)

    def open_nav_drawer(self, name: str) -> None:
        """Open the nav-drawer."""

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
        on_left: bool = False,
        on_bottom: bool = False,
        check_ver_growth: bool = False,
        show_duration_x: Optional[float] = None,
    ) -> None:
        """Open the menu object."""
