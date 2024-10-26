"""
Contains the core of kivyapp: KivyApp, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

try:
    from .config import kvconfig
except ImportError as e:
    raise e

import os
import time
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional

import asynckivy
from kivy.animation import Animation
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import StringProperty  # pylint: disable=no-name-in-module
from kivymd.app import MDApp
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.card import MDCard
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel
from kivymd.uix.list.list import MDListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.menu.menu import BaseDropdownItem
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from ..bookmanager import BookManager

if TYPE_CHECKING:
    from kivy.config import ConfigParser

    from ..bookmanager._typing import StatusHint


__all__ = ["MainApp"]

LabelBase.register(name="msyh", fn_regular=r"C:\Windows\Fonts\msyh.ttc")
LabelBase.register(name="msyhbd", fn_regular=r"C:\Windows\Fonts\msyhbd.ttc")
LabelBase.register(name="simhei", fn_regular=r"C:\Windows\Fonts\simhei.ttf")


theme_font_styles["BookCover"] = {
    "large": {
        "line-height": 1.28,
        "font-name": "msyhbd",
        "font-size": sp(21),
    },
    "medium": {
        "line-height": 1.24,
        "font-name": "msyh",
        "font-size": sp(18),
    },
    "small": {
        "line-height": 1.2,
        "font-name": "msyh",
        "font-size": sp(16),
    },
}
theme_font_styles["BookHint"] = {
    "large": {
        "line-height": 1.28,
        "font-name": "msyh",
        "font-size": sp(15),
    },
    "medium": {
        "line-height": 1.24,
        "font-name": "msyh",
        "font-size": sp(14),
    },
    "small": {
        "line-height": 1.2,
        "font-name": "msyh",
        "font-size": sp(13),
    },
}
theme_font_styles["NavText"] = {
    "large": {
        "line-height": 1.28,
        "font-name": "msyh",
        "font-size": sp(20),
    },
    "medium": {
        "line-height": 1.24,
        "font-name": "msyh",
        "font-size": sp(16),
    },
    "small": {
        "line-height": 1.2,
        "font-name": "msyh",
        "font-size": sp(12),
    },
}


def _on_key_up(key, *_):
    if key == 292:  # "F11"
        match Window.fullscreen:
            case "auto":
                Window.fullscreen = False
            case False:
                Window.fullscreen = "auto"


Window.on_key_up = _on_key_up
Window.maximize()


class BookCard(MDCard):
    """Implements a material card."""

    bookid: str = StringProperty()
    image: str = StringProperty()
    title: str = StringProperty()
    author: str = StringProperty()
    progress: str = StringProperty()
    status: "StatusHint" = StringProperty()

    def check_border(self) -> None:
        """
        Check whether the widget itself is out of border. If True,
        set disabled=True; otherwise, set disabled=False

        """
        self.disabled = self._is_out_of_border()

    def _is_out_of_border(self) -> bool:
        return (
            self.to_window(0, self.pos[1] + self.height)[1]
            > self.parent.parent.to_window(
                0, self.parent.parent.pos[1] + self.parent.parent.height
            )[1]
        )


class CoverDropdownTextItem(BaseDropdownItem):
    """Implements a menu item with text without leading and trailing icons."""


class CoverDeleteDropdownTextItem(CoverDropdownTextItem):
    """Implements a menu item with text without leading and trailing icons."""


class UploadFileManagerItem(MDListItem):
    """Base class for folders and files icons."""


class UploadFileManagerItemPreview(MDListItem):
    """Base class for folder icons and thumbnails images in `preview` mode."""


class UploadFileManager(MDFileManager):
    """File manger for uploading books."""

    def show(self, path: str) -> None:
        """
        Forms the body of a directory tree.

        :param path:
            The path to the directory that will be opened in the file manager.
        """

        self.current_path = path
        self.selection = []
        dirs, files = self.get_content()
        manager_list = []

        if dirs == [] and files == []:  # selected directory
            pass
        elif not dirs and not files:  # directory is unavailable
            return

        if self.preview:
            for name_dir in self._MDFileManager__sort_files(dirs):
                manager_list.append(
                    {
                        "viewclass": "UploadFileManagerItemPreview",
                        "path": self.icon_folder,
                        "realpath": os.path.join(path),
                        "type": "folder",
                        "name": name_dir,
                        "events_callback": self.select_dir_or_file,
                        "height": dp(150),
                        "_selected": False,
                    }
                )
            for name_file in self._MDFileManager__sort_files(files):
                if os.path.splitext(os.path.join(path, name_file))[1] in self.ext:
                    manager_list.append(
                        {
                            "viewclass": "UploadFileManagerItemPreview",
                            "path": os.path.join(path, name_file),
                            "name": name_file,
                            "type": "files",
                            "events_callback": self.select_dir_or_file,
                            "height": dp(150),
                            "_selected": False,
                        }
                    )
        else:
            for name in self._MDFileManager__sort_files(dirs):
                _path = os.path.join(path, name)
                access_string = self.get_access_string(_path)
                if "r" not in access_string:
                    icon = "folder-lock"
                else:
                    icon = "folder"

                manager_list.append(
                    {
                        "viewclass": "UploadFileManagerItem",
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
                        "viewclass": "UploadFileManagerItem",
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
        self._show()


class FakeModalView:
    """A fake view."""

    def open(self):
        """Open?"""

    def dismiss(self):
        """Dismiss?"""


class MainApp(MDApp):
    """Kivy-App for ReadPub."""

    bookmanager: BookManager
    filemanager: UploadFileManager
    current_sort_rule: list[str]
    current_category: str
    nav_width: int = 0
    has_filemanager: bool = False
    prev_snackbar: MDSnackbar | None = None

    def get_application_config(self, defaultpath="") -> str:
        return kvconfig.get_inipath(self).as_posix()

    def build_config(self, config: "ConfigParser") -> None:
        kvconfig.resgister(self, config)
        kvconfig[self].set_defaults(
            [
                ["theme-cls", "theme_style", "Light"],
                ["theme-cls", "primary_palette", "Blue"],
            ]
        )

    def build(self):
        self.title = "ReadPub"

        self.theme_cls.theme_style = kvconfig[self].get("theme-cls", "theme_style")
        self.theme_cls.primary_palette = kvconfig[self].get(
            "theme-cls", "primary_palette"
        )
        self.filemanager = UploadFileManager(
            exit_manager=self.filemanager_exit, select_path=self.filemanager_select_path
        )
        self.filemanager._window_manager = (  # pylint: disable=protected-access
            FakeModalView()
        )

    def filemanager_open(self):
        """Open filemanager."""
        self.open_nav_drawer("nav_files")
        if not self.has_filemanager:
            self.root.ids.nav_files.children[0].add_widget(self.filemanager)
            self.has_filemanager = True
        self.filemanager.show(os.path.expanduser(r"~\DeskTop"))

    def filemanager_select_path(self, path: str):
        """
        It will be called when you click on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        """

        self.filemanager_exit()
        if self.bookmanager.check_book(Path(path)):
            snack = "已上传电子书: " + path
        else:
            snack = "无法读取文件格式: " + path
        if self.prev_snackbar:
            self.prev_snackbar.dismiss()
        self.prev_snackbar = MDSnackbar(
            MDSnackbarText(
                text=snack,
                font_style="NavText",
                role="medium",
            ),
            y=dp(40),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
        )
        self.prev_snackbar.open()

    def filemanager_exit(self, *args):
        """Called when the user reaches the root of the directory tree."""
        self.filemanager.close()

    def on_start(self) -> None:
        m = BookManager(kvconfig.path.parent)
        self.current_sort_rule = ["status", "uploadtime"]

        async def set_cards(duration: Optional[float] = None):
            for bookid, book in (
                m.findnot(status="deleted").sort(*self.current_sort_rule).books.items()
            ):
                metadata = book.get_metadata()
                pagenow, pagemax = metadata["progress"]
                match pagenow / pagemax:
                    case 0.0:
                        progress = "待阅读"
                    case 1.0:
                        progress = "已读完√"
                    case _ as x:
                        progress = f"阅读到 {x:.2%}"
                widget = BookCard(
                    style="elevated",
                    bookid=bookid,
                    image=metadata["coverpath"],
                    title=metadata["title"],
                    author=metadata["author"],
                    progress=progress,
                    status=metadata["status"],
                )
                self.root.ids.grid.add_widget(widget)
                if duration is not None:
                    await asynckivy.sleep(duration)

        asynckivy.start(set_cards())
        self.bookmanager = m

    def switch_theme_style(self):
        """Switch the theme-style."""
        self.theme_cls.theme_style = (
            "Dark" if self.theme_cls.theme_style == "Light" else "Light"
        )

    def open_settings(self, *_) -> None: ...

    def open_cover_menu(self, button) -> None:
        """Open a menu on the book cover."""
        menu = MDDropdownMenu(
            caller=button,
            items=[],
            show_duration=0.1,
            hide_duration=0.1,
            hor_growth="right",
            radius=button.parent.parent.radius,
            shadow_radius=button.parent.parent.shadow_radius,
        )
        is_normal = button.parent.parent.status == "normal"
        menu_items = [
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "置顶" if is_normal else "取消置顶",
                "leading_icon": "pin" if is_normal else "pin-off",
                "height": dp(40),
                "on_release": (
                    partial(self.pin_bookcard, button, menu)
                    if is_normal
                    else partial(self.unpin_bookcard, button, menu)
                ),
            },
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "书籍信息",
                "leading_icon": "information-outline",
                "height": dp(40),
                "on_release": partial(self.get_bookcard_info, button, menu),
            },
            {
                "viewclass": "CoverDeleteDropdownTextItem",
                "text": "删除本书",
                "leading_icon": "delete",
                "leading_icon_color": self.theme_cls.errorColor,
                "text_color": self.theme_cls.errorColor,
                "height": dp(40),
                "on_release": partial(self.delete_bookcard, button, menu),
            },
        ]
        menu.items.extend(menu_items)
        menu.on_enter = menu.on_leave
        self._cover_menu_open(menu, button)

    def open_plus_menu(self, button) -> None:
        """Open the menu on releasing the plus button."""
        radius, shadow_radius = self.get_radius()
        menu = MDDropdownMenu(
            caller=button,
            items=[],
            show_duration=0.3,
            hide_duration=0.3,
            hor_growth="left",
            ver_growth="down",
            # position="bottom",
            radius=radius,
            shadow_radius=shadow_radius,
        )
        menu_items = [
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "上传新书",
                "leading_icon": "upload",
                "height": dp(50),
                "on_release": lambda: self.filemanager_open(),
            },
            {
                "viewclass": "CoverDeleteDropdownTextItem",
                "text": "回收站",
                "leading_icon": "trash-can",
                "height": dp(50),
            },
        ]
        menu.items.extend(menu_items)
        menu.on_enter = menu.on_leave
        self._plus_menu_open(menu, button)

    def pin_bookcard(self, button, menu=None) -> None:
        """Pin the bookcard containing the button."""
        book = self.bookmanager.books[button.parent.parent.bookid]
        book.update_metadata(status="pinned")
        button.parent.parent.status = "pinned"
        self.root.ids.grid.remove_widget(button.parent.parent)

        idx = self.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.root.ids.grid.add_widget(button.parent.parent, idx)
        if menu:
            menu.dismiss()
        book.save_metadata()

    def unpin_bookcard(self, button, menu=None) -> None:
        """Unpin the bookcard containing the button."""
        book = self.bookmanager.books[button.parent.parent.bookid]
        book.update_metadata(status="normal")
        button.parent.parent.status = "normal"
        self.root.ids.grid.remove_widget(button.parent.parent)

        idx = self.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.root.ids.grid.add_widget(button.parent.parent, idx)
        if menu:
            menu.dismiss()
        book.save_metadata()

    def get_bookcard_info(self, button, menu=None) -> None:
        """Pin the bookcard containing the button."""

    def delete_bookcard(self, button, menu=None) -> None:
        """Delete the bookcard."""
        book = self.bookmanager.books[button.parent.parent.bookid]
        book.update_metadata(status="deleted")
        self.root.ids.grid.remove_widget(button.parent.parent)
        if menu:
            menu.dismiss()
        book.save_metadata()

    def get_radius(
        self, root=None, nav: Optional[Literal["left", "right"]] = None
    ) -> tuple[list, list]:
        """Get the radius and the shadow-radius."""
        if root is None:
            root = self.root
        if len(children := root.ids.grid.children) > 0:
            bookcard = children[0]
        else:
            bookcard = BookCard(style="elevated")
        match nav:
            case "left":
                bookcard.radius[0] = 0
                bookcard.radius[3] = 0
            case "right":
                bookcard.radius[1] = 0
                bookcard.radius[2] = 0
        return bookcard.radius, bookcard.shadow_radius

    def open_nav_drawer(self, name: str = "nav_drawer") -> None:
        """Open the nav-drawer."""
        nav_drawer = getattr(self.root.ids, name)
        if self.nav_width == 0:
            self.nav_width = nav_drawer.width * 1.5
        nav_drawer.width = self.nav_width
        nav_drawer.set_state("toggle")

    def _cover_menu_open(self, menu: MDDropdownMenu, caller: Any) -> None:
        # pylint: disable=protected-access
        menu.set_menu_properties()

        # check ver_growth
        menu.ver_growth = "up"
        if menu.target_height > menu._start_coords[1] - menu.border_margin:
            menu.ver_growth = "up"
        elif (
            menu._start_coords[1]
            > Window.height - menu.border_margin - menu.target_height
        ):
            menu.ver_growth = "down"

        Window.add_widget(menu)
        menu.position = menu.adjust_position()

        menu.width = dp(160)

        menu.height = menu.target_height
        menu._tar_x, menu._tar_y = menu.get_target_pos()
        bookcard_pos = caller.parent.parent.to_window(*caller.parent.parent.pos)
        menu.x = (
            bookcard_pos[0]
            + caller.parent.parent.width
            + self.root.ids.grid.spacing[0] / 2
        )
        menu.y = bookcard_pos[1]
        menu.scale_value_center = menu.caller.to_window(*menu.caller.center)
        menu.set_menu_pos()
        # pylint: enable=protected-access
        _menu_on_open(menu)

    def get_ancastor(self, obj: object, n: int = 1) -> object | None:
        """
        Get the n-th ancastor (counting from the direct parent = 1). If
        not exist, return None.

        """
        try:
            for _ in range(n):
                obj = obj.parent
            return obj
        except AttributeError:
            return None

    def _plus_menu_open(self, menu: MDDropdownMenu, caller: Any) -> None:
        # pylint: disable=protected-access
        menu.set_menu_properties()

        # check ver_growth
        menu.ver_growth = "up"
        if menu.target_height > menu._start_coords[1] - menu.border_margin:
            menu.ver_growth = "up"
        elif (
            menu._start_coords[1]
            > Window.height - menu.border_margin - menu.target_height
        ):
            menu.ver_growth = "down"

        Window.add_widget(menu)
        menu.position = menu.adjust_position()

        menu.width = dp(160)

        menu.height = menu.target_height
        menu._tar_x, menu._tar_y = menu.get_target_pos()
        button_pos = caller.to_window(*caller.pos)
        menu.x = button_pos[0] + caller.width * 0.8 - menu.width
        menu.y = button_pos[1] - menu.height - caller.height * 0.1
        menu.scale_value_center = menu.caller.to_window(*menu.caller.center)
        menu.set_menu_pos()
        # pylint: enable=protected-access
        _menu_on_open(menu)


def _menu_on_open(menu: MDDropdownMenu) -> None:
    anim = Animation(
        _scale_y=1,
        duration=menu.show_duration,
        transition=menu.show_transition,
    )
    anim &= Animation(
        _scale_x=1,
        duration=max(menu.show_duration - 0.3, 0.0),
        transition="out_quad",
    )
    anim.start(menu)
