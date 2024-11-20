"""
Contains a file importer: FileImporter.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.uix.button import MDFabButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list.list import MDListItem
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

if TYPE_CHECKING:
    from ._typing import ImportType
    from .core import MainApp

__all__ = ["FileImporter"]


class FileImportItem(MDListItem):
    """Base class for folders and files icons."""


class FileImportManager(MDFileManager):
    """Implements a file manager."""

    def show(self, path: str) -> None:
        """Forms the body of a directory tree."""

        self.current_path = path
        self.selection = []
        dirs, files = self.get_content()
        items = []

        if dirs == [] and files == []:  # selected directory
            pass
        elif not dirs and not files:  # directory is unavailable
            return

        sort_files: Callable[[list[str]], list[str]] = getattr(
            self, "_MDFileManager__sort_files"
        )
        for name in sort_files(dirs):
            _path = os.path.join(path, name)
            access_string = self.get_access_string(_path)
            if "r" not in access_string:
                icon = "folder-lock"
            else:
                icon = "folder"

            items.append(
                {
                    "viewclass": "FileImportItem",
                    "path": _path,
                    "icon": icon,
                    "dir_or_file_name": name,
                    "events_callback": self.select_dir_or_file,
                    "icon_color": (
                        self.theme_cls.primaryColor
                        if not self.icon_color
                        else self.icon_color
                    ),
                    "_selected": False,
                }
            )
        for name in sort_files(files):
            if self.ext and os.path.splitext(name)[1] not in self.ext:
                continue

            items.append(
                {
                    "viewclass": "FileImportItem",
                    "path": name,
                    "icon": "file-outline",
                    "dir_or_file_name": os.path.split(name)[1],
                    "events_callback": self.select_dir_or_file,
                    "icon_color": (
                        self.theme_cls.primaryColor
                        if not self.icon_color
                        else self.icon_color
                    ),
                    "_selected": False,
                }
            )

        self.ids.rv.data = items
        self.selection_button.md_bg_color = self.theme_cls.surfaceContainerColor
        self._show()

    def _create_selection_button(self, *args):
        if (
            self.selector == "any"
            or self.selector == "multi"
            or self.selector == "folder"
        ):
            self.selection_button = MDFabButton(
                on_release=self.select_directory_on_press_button,
                theme_bg_color="Custom",
                md_bg_color=(
                    self.theme_cls.primaryColor
                    if not self.background_color_selection_button
                    else self.background_color_selection_button
                ),
                icon=self.icon_selection_button,
                pos_hint={"right": 0.99},
                y=dp(12),
            )
            self.add_widget(self.selection_button)


class FakeModalView:
    """A fake view."""

    def open(self):
        """Open?"""

    def dismiss(self):
        """Dismiss?"""


class FileImporter:
    """Implements a file importer."""

    def __init__(self, app: "MainApp") -> None:
        self.app = app
        self.imptype = ""
        self.activated = False
        self.prev_snackbar: MDSnackbar | None = None
        self.filemanager = FileImportManager(
            exit_manager=self.close, select_path=self.select_path
        )
        setattr(self.filemanager, "_window_manager", FakeModalView())

    def open(self, imptype: "ImportType" = "book") -> None:
        """Open filemanager."""
        self.imptype = imptype
        self.app.open_nav_drawer("nav_import")
        if not self.activated:
            self.app.root.ids.nav_import.children[0].add_widget(self.filemanager)
            self.activated = True
        self.filemanager.show(os.path.expanduser("~\\DeskTop"))

    def close(self, *_):
        """Called when the user reaches the root of the directory tree."""
        self.filemanager.close()

    def select_path(self, path: str):
        """
        It will be called when you click on the file name or the catalog
        selection button.

        """
        self.close()
        match self.imptype:
            case "book":
                self.import_book(path)
            case "bgim":
                self.import_bgim(path)

    def import_book(self, path: str) -> None:
        """Importing book."""
        if checked := self.app.bookmanager.check_is_book(p := Path(path)):
            snack = "已导入新书: " + path
        else:
            snack = f"无法解析文件{"夹" if p.is_dir() else ""}: " + path

        # open snackbar
        if self.prev_snackbar:
            self.prev_snackbar.dismiss()
        fs, role = "NavText", "medium"
        self.prev_snackbar = MDSnackbar(
            MDSnackbarText(
                text=self.app.font.gettextmaster(fs, role).shorten(
                    snack, Window.width / 2 - 20
                ),
                font_style=fs,
                role=role,
            ),
            y=dp(40),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
        )
        self.prev_snackbar.open()

        if checked:
            self.app.cards.insert(book := self.app.bookmanager.add_book(p))
            self.app.cards.prepare_book(book)

    def import_bgim(self, path: str) -> None:
        """Importing background image."""
        p = Path(path)
        if checked := p.is_file() and p.suffix in {".png", ".jpg", ".jpeg"}:
            snack = "已应用背景图片: " + path
        else:
            snack = "无背景图片"

        # open snackbar
        if self.prev_snackbar:
            self.prev_snackbar.dismiss()
        fs, role = "NavText", "medium"
        self.prev_snackbar = MDSnackbar(
            MDSnackbarText(
                text=self.app.font.gettextmaster(fs, role).shorten(
                    snack, Window.width / 2 - 20
                ),
                font_style=fs,
                role=role,
            ),
            y=dp(40),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
        )
        self.prev_snackbar.open()

        if checked:
            self.app.set_bgim(path)
        else:
            self.app.set_bgim()
