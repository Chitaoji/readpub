"""
Contains an input method: FileImporter.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from typing import TYPE_CHECKING, Any

from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list.list import MDListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from ..bookmanager import TextMaster

if TYPE_CHECKING:
    from ._typing import BasicApp
else:
    from kivymd.app import MDApp as BasicApp

__all__ = ["InputMethod"]


class InputMethod(BasicApp):
    """Implements an input method."""

    def open_input_menu(self, button: Any, text: str) -> None:
        """Open an input menu."""
        if self.prev_input_menu:
            self.prev_input_menu.dismiss()
        menu = MDDropdownMenu(
            caller=button,
            items=[
                {
                    "viewclass": "MDLabel",
                    "text": text,
                    "padding": dp(4),
                    "height": dp(30),
                    "adaptive_width": True,
                },
            ],
            show_duration=0.0,
            hide_duration=0.0,
            hor_growth="right",
            ver_growth="up",
            radius=[dp(1), dp(1), dp(1), dp(1)],
            shadow_radius=[0, 0, 0, 0],
            width=dp(160),
            theme_shadow_softness="Custom",
            shadow_softness=8,
        )
        self.prev_input_menu = menu
        self.open_menu(menu, button, on_left=True)
