"""
Contains a kivy app: FileImportApp.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list.list import MDListItem
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

if TYPE_CHECKING:
    from ._typing import BasicApp, UploadType
else:
    from kivymd.app import MDApp as BasicApp

__all__ = ["FileImportApp"]


class FileImportItem(MDListItem):
    """Base class for folders and files icons."""


class FileImportManager(MDFileManager):
    """Implements a file manager."""

    def show(self, path: str) -> None:
        """Forms the body of a directory tree."""

        self.current_path = path
        self.selection = []
        dirs, files = self.get_content()
        manager_list = []

        if dirs == [] and files == []:  # selected directory
            pass
        elif not dirs and not files:  # directory is unavailable
            return

        for name in self._MDFileManager__sort_files(dirs):
            _path = os.path.join(path, name)
            access_string = self.get_access_string(_path)
            if "r" not in access_string:
                icon = "folder-lock"
            else:
                icon = "folder"

            manager_list.append(
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
        for name in self._MDFileManager__sort_files(files):
            if self.ext and os.path.splitext(name)[1] not in self.ext:
                continue

            manager_list.append(
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

        self.ids.rv.data = manager_list
        self.selection_button.md_bg_color = self.theme_cls.surfaceContainerColor
        self._show()


class FakeModalView:
    """A fake view."""

    def open(self):
        """Open?"""

    def dismiss(self):
        """Dismiss?"""


class FileImportApp(BasicApp):
    """Implements a file importer app."""

    def filemanager_open(self, upload_type: "UploadType" = "book") -> None:
        """Open filemanager."""
        self.upload_type = upload_type
        self.open_nav_drawer("nav_upload")
        if not self.has_filemanager:
            self.root.ids.nav_upload.children[0].add_widget(self.filemanager)
            self.has_filemanager = True
        self.filemanager.show(os.path.expanduser("~\\DeskTop"))

    def filemanager_select_path(self, path: str):
        """
        It will be called when you click on the file name
        or the catalog selection button.

        """
        self.filemanager_exit()
        match self.upload_type:
            case "book":
                self.upload_book(path)
            case "bgim":
                self.upload_bgim(path)

    def upload_book(self, path: str) -> None:
        """Uploading book."""
        if checked := self.bookmanager.check_book(p := Path(path)):
            snack = "已导入新书: " + path
        else:
            snack = f"无法解析文件{"夹" if p.is_dir() else ""}: " + path

        # open snackbar
        if self.prev_snackbar:
            self.prev_snackbar.dismiss()
        fs, role = "NavText", "medium"
        self.prev_snackbar = MDSnackbar(
            MDSnackbarText(
                text=self.fontmanager.gettextmaster(fs, role).shorten(
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
            self.set_card(book := self.bookmanager.add_book(p))
            self.prepare_book(book)

    def upload_bgim(self, path: str) -> None:
        """Uploading background image."""
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
                text=self.fontmanager.gettextmaster(fs, role).shorten(
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
            self.set_bgim(path)
        else:
            self.set_bgim()

    def filemanager_exit(self, *_):
        """Called when the user reaches the root of the directory tree."""
        self.filemanager.close()
