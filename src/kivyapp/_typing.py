"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from typing import TYPE_CHECKING, Any, Literal, Optional

from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu

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

        super().__init__(**kwargs)

    def open_nav_drawer(self, name: str) -> None:
        """Open the nav-drawer."""

    def switch_theme(self) -> None:
        """Switch the theme-style."""

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
