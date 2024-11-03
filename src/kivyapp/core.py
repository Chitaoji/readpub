"""
Contains the core of kivyapp: KivyApp, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

# pylint: disable=no-name-in-module
try:
    from .config import kvconfig
except ImportError as e:
    raise e
import os
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional

import asynckivy
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ColorProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.utils import hex_colormap
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
    MDDialogIcon,
    MDDialogSupportingText,
)
from kivymd.uix.divider import MDDivider
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemSupportingText
from kivymd.uix.list.list import MDListItem, MDListItemLeadingIcon
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.menu.menu import BaseDropdownItem
from kivymd.uix.progressindicator.progressindicator import MDCircularProgressIndicator
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.textfield import MDTextField, MDTextFieldHelperText

from ..bookmanager import BookManager, TextMaster
from .fileimport import FileImportManager
from .font import KivyFont

if TYPE_CHECKING:
    from kivy.config import ConfigParser

    from ..bookmanager._typing import Book, StatusHint

__all__ = ["MainApp"]


def _on_key_up(key, *_):
    if key == 292:  # "F11"
        match Window.fullscreen:
            case "auto":
                Window.fullscreen = False
            case False:
                Window.fullscreen = "auto"


Window.on_key_up = _on_key_up
Window.maximize()


class ColorCard(BoxLayout):
    """Implements a material card."""

    text = StringProperty()
    bg_color = ColorProperty()


class BookCard(MDCard):
    """Implements a material card."""

    bookid: str = StringProperty()
    image: str = StringProperty()
    title: str = StringProperty()
    author: str = StringProperty()
    progress: str = StringProperty()
    status: "StatusHint" = StringProperty()
    is_ready: bool = BooleanProperty()
    truly_disabled: bool = BooleanProperty()

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

    def set_properties_widget(self) -> None:
        """Fired `on_release/on_press/on_enter/on_leave` events."""
        if not self.truly_disabled:
            super().set_properties_widget()


class CoverDropdownTextItem(BaseDropdownItem):
    """Implements a menu item with text without leading and trailing icons."""


class CoverDeleteDropdownTextItem(CoverDropdownTextItem):
    """Implements a menu item with text without leading and trailing icons."""


class FakeModalView:
    """A fake view."""

    def open(self):
        """Open?"""

    def dismiss(self):
        """Dismiss?"""


class ColorButton(MDButton):
    """Button with color."""

    color: str = StringProperty()


class MainApp(MDApp):
    """Kivy-App for ReadPub."""

    bookmanager: BookManager
    filemanager: FileImportManager
    fontmanager: KivyFont
    current_sort_rule: list[str]
    current_category: str
    has_filemanager: bool = False
    prev_snackbar: MDSnackbar | None = None
    category_status: str
    test_bookcard: BookCard | None = None

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

        self.fontmanager = KivyFont(Path("C:\\Windows\\Fonts"))
        self.theme_cls.theme_style = kvconfig[self].get("theme-cls", "theme_style")
        self.theme_cls.primary_palette = kvconfig[self].get(
            "theme-cls", "primary_palette"
        )

    def build(self):
        self.title = "ReadPub"

        self.filemanager = FileImportManager(
            exit_manager=self.filemanager_exit, select_path=self.filemanager_select_path
        )
        self.filemanager._window_manager = (  # pylint: disable=protected-access
            FakeModalView()
        )

    def on_start(self) -> None:
        m = BookManager(kvconfig.path.parent)
        self.current_sort_rule = ["status", "uploadtime"]

        asynckivy.start(
            self.set_cards(
                m.findnot(status="deleted").sort(*self.current_sort_rule).books
            )
        )
        self.category_status = "home"
        self.bookmanager = m
        self.init_color_buttons()

        func = self.root.get_screen("Reader").on_touch_down
        self.root.get_screen("Reader").on_touch_down = (
            lambda x: self.on_reader_touch_down(func, x)
        )

    def on_reader_touch_down(self, func, touch):
        """On mouse down."""
        if Window.height * 0.2 < touch.y < Window.height * 0.8 and dp(
            480
        ) < touch.x < Window.width - dp(480):
            if (toolbar := self.root.ids.reader_toolbar).disabled:
                asynckivy.start(self.activate_reader_toolbar())
            else:
                toolbar.disabled = True
                toolbar.opacity = 0
        func(touch)

    async def activate_reader_toolbar(self) -> None:
        """Activate reader toolbar."""
        self.fix_reader_search_field()
        self.root.ids.reader_toolbar.disabled = False
        await asynckivy.sleep(0.15)
        if not self.root.ids.reader_toolbar.disabled:
            self.root.ids.reader_search_field_helper.text = ""
            self.root.ids.reader_toolbar.opacity = 1
            await asynckivy.sleep(0.1)
            if not self.root.ids.reader_toolbar.disabled:
                self.root.ids.reader_search_field_helper.text = "请输入搜索内容..."

    def fix_reader_search_field(self):
        """Fix the search field."""
        field = self.root.ids.reader_search_field
        field.set_texture_color(
            getattr(field, "_helper_text_label"),
            field.canvas.before.get_group("helper-text-color")[0],
            self.theme_cls.transparentColor,
        )

    def open_settings(self, *_) -> None: ...

    def open_book(self, bookid: str) -> None:
        """Open a book."""
        book = self.bookmanager.books[bookid]
        book.typeset()
        book.open()
        page = book.turn_to_page(100)
        box = self.root.ids.textbox
        for para in page:
            if isinstance(para, list):
                for line in para:
                    box.add_widget(
                        MDLabel(
                            adaptive_width=True,
                            font_style="BookCover",
                            role="medium",
                            text=line,
                        )
                    )
                box.add_widget(
                    MDLabel(
                        adaptive_width=True,
                        font_style="BookCover",
                        role="medium",
                        text="",
                    )
                )
            else:
                box.add_widget(
                    MDLabel(
                        adaptive_width=True,
                        font_style="BookCover",
                        role="medium",
                        text=para.text,
                    )
                )
                box.add_widget(
                    MDLabel(
                        adaptive_width=True,
                        font_style="BookCover",
                        role="medium",
                        text="",
                    )
                )

    def init_color_buttons(self):
        """Initialize the color buttons."""
        for color in [
            "red",
            "orange",
            "gold",
            "green",
            "cyan",
            "blue",
            "purple",
            "olive",
        ]:
            self.root.ids.palette_pre_grid.add_widget(ColorButton(color=color))
            self.root.ids.reader_palette_pre_grid.add_widget(ColorButton(color=color))
        self.theme_cls.bind(
            primary_palette=lambda _, c: setattr(
                self.root.ids.palette_now_button, "md_bg_color", c.lower()
            )
        )

    def filemanager_open(self):
        """Open filemanager."""
        self.open_nav_drawer("nav_upload")
        if not self.has_filemanager:
            self.root.ids.nav_upload.children[0].add_widget(self.filemanager)
            self.has_filemanager = True
        self.filemanager.show(os.path.expanduser(r"~\DeskTop"))

    def filemanager_select_path(self, path: str):
        """
        It will be called when you click on the file name
        or the catalog selection button.

        """
        self.filemanager_exit()
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
                text=TextMaster(*self.fontmanager.translate(fs, role)).shorten(
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
            bookcard = self.set_card(book := self.bookmanager.add_book(p))
            asynckivy.start(self.prepare_book(book, bookcard))

    def set_card(self, book: "Book") -> BookCard:
        """Set a new book card."""
        metadata = book.get_metadata()
        pagenow, pagemax = metadata["pagenow"], metadata["pagemax"]
        match pagenow / pagemax:
            case 0.0:
                progress = "待阅读"
            case 1.0:
                progress = "已读完√"
            case _ as x:
                progress = f"阅读到 {x:.2%}"
        widget = BookCard(
            style="elevated",
            bookid=book.bookid,
            image=metadata["coverpath"],
            title=metadata["title"],
            author=metadata["author"],
            progress=progress,
            status=metadata["status"],
            is_ready=metadata["is_ready"],
        )
        idx = self.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.root.ids.grid.add_widget(widget, idx)
        return widget

    async def set_cards(
        self, books: dict[str, "Book"], duration: Optional[float] = None
    ):
        """Set cards."""
        for bookid, book in books.items():
            metadata = book.get_metadata()
            pagenow, pagemax = metadata["pagenow"], metadata["pagemax"]
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
            if metadata["status"] == "deleted":
                widget.theme_bg_color = "Custom"
                widget.md_bg_color = self.theme_cls.errorContainerColor
                self.theme_cls.bind(errorContainerColor=widget.setter("md_bg_color"))
            self.root.ids.grid.add_widget(widget)
            if duration is not None:
                await asynckivy.sleep(duration)

    def check_cards(self) -> None:
        """Check the bookcards."""
        for card in self.root.ids.grid.children:
            card.check_border()

    def truly_disable_cards(self) -> None:
        """Disable the bookcards."""
        for card in self.root.ids.grid.children:
            card.truly_disabled = True

    def truly_enable_cards(self) -> None:
        """Enable the bookcards."""
        for card in self.root.ids.grid.children:
            card.truly_disabled = False

    async def asynctest(self, time: int, duration: Optional[float] = None):
        """Test the async functionality."""
        for i in range(1, 1 + time):
            if duration is not None:
                await asynckivy.sleep(duration)
            Logger.info("Test: Test Step No.%s", str(i))

    async def prepare_book(
        self, book: "Book", bookcard: BookCard, duration: Optional[float] = None
    ):
        """Extract the book."""
        if duration is not None:
            await asynckivy.sleep(duration)
        book.extract()
        Logger.info('Extract: Extracting book "%s"', book.get_metadata()["filepath"])
        if duration is not None:
            await asynckivy.sleep(duration)
        book.picklize()
        Logger.info('Picklize: Pickling book "%s"', book.get_metadata()["filepath"])
        bookcard.is_ready = True

    def remove_cards(self) -> None:
        """Remove all the bookcards."""
        self.root.ids.grid.parent.scroll_y = 1
        for widget in list(self.root.ids.grid.children):
            self.root.ids.grid.remove_widget(widget)

    def filemanager_exit(self, *_):
        """Called when the user reaches the root of the directory tree."""
        self.filemanager.close()

    def switch_theme_style(self, to: Optional[str] = None):
        """Switch the theme-style."""
        if to:
            self.theme_cls.theme_style = to
        else:
            self.theme_cls.theme_style = (
                "Dark" if self.theme_cls.theme_style == "Light" else "Light"
            )
        kvconfig[self].update(
            [["theme-cls", "theme_style", self.theme_cls.theme_style]]
        )

    def switch_theme_palette(self, color: str):
        """Switch the theme-palette."""
        self.theme_cls.primary_palette = color
        kvconfig[self].update([["theme-cls", "primary_palette", color]])

    def reset_theme(self):
        """Reset the theme."""
        self.switch_theme_style(to="Light")
        self.switch_theme_palette("Blue")

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
        is_pinned = button.parent.parent.status == "pinned"
        is_deleted = button.parent.parent.status == "deleted"
        menu_items = [
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "取消置顶" if is_pinned else ("恢复" if is_deleted else "置顶"),
                "leading_icon": (
                    "pin-off" if is_pinned else ("restore" if is_deleted else "pin")
                ),
                "height": dp(40),
                "on_release": (
                    partial(self.unpin_bookcard, button, menu)
                    if is_pinned
                    else (
                        partial(self.restore_bookcard, button, menu)
                        if is_deleted
                        else partial(self.pin_bookcard, button, menu)
                    )
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
                "text": "永久删除" if is_deleted else "删除本书",
                "leading_icon": "delete-alert" if is_deleted else "delete",
                "leading_icon_color": self.theme_cls.errorColor,
                "text_color": self.theme_cls.errorColor,
                "height": dp(40),
                "on_release": partial(
                    self.show_alert_dialog if is_deleted else self.delete_bookcard,
                    button,
                    menu,
                ),
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
            show_duration=0.2,
            hide_duration=0.2,
            hor_growth="left",
            ver_growth="down",
            radius=radius,
            shadow_radius=shadow_radius,
        )
        menu_items = [
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "导入新书",
                "leading_icon": "upload",
                "height": dp(50),
                "on_release": lambda: (self.filemanager_open(), menu.dismiss()),
            },
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "回到首页",
                "leading_icon": "home-outline",
                "height": dp(50),
                "on_release": lambda: (
                    (
                        self.remove_cards(),
                        asynckivy.start(
                            self.set_cards(
                                self.bookmanager.findnot(status="deleted")
                                .sort(*self.current_sort_rule)
                                .books,
                                0,
                            )
                        ),
                        self.set_category_status("home"),
                    )
                    if self.category_status != "home"
                    else None
                ),
            },
            {
                "viewclass": "CoverDeleteDropdownTextItem",
                "text": "全部分类",
                "leading_icon": "folder-multiple-outline",
                "height": dp(50),
                "on_release": partial(self.open_category_menu, menu),
            },
        ]
        menu.items.extend(menu_items)
        menu.on_enter = menu.on_leave
        self._plus_menu_open(menu, button)

    def open_category_menu(self, button) -> None:
        """Open the category menu."""
        radius, shadow_radius = self.get_radius()
        menu = MDDropdownMenu(
            caller=button,
            items=[],
            show_duration=0.1,
            hide_duration=0.0,
            hor_growth="left",
            ver_growth="down",
            radius=radius,
            shadow_radius=shadow_radius,
        )

        menu.on_dismiss = partial(_button_auto_dismiss, button, menu.on_dismiss)
        menu_items = [
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "首页",
                "leading_icon": "home-outline",
                "height": dp(50),
                "on_release": lambda: (
                    (
                        self.remove_cards(),
                        asynckivy.start(
                            self.set_cards(
                                self.bookmanager.findnot(status="deleted")
                                .sort(*self.current_sort_rule)
                                .books,
                                0,
                            )
                        ),
                        self.set_category_status("home"),
                    )
                    if self.category_status != "home"
                    else None
                ),
            },
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "已置顶",
                "leading_icon": "pin",
                "height": dp(50),
                "on_release": lambda: (
                    (
                        self.remove_cards(),
                        asynckivy.start(
                            self.set_cards(
                                self.bookmanager.find(status="pinned")
                                .sort(*self.current_sort_rule)
                                .books,
                                0,
                            )
                        ),
                        self.set_category_status("pinned"),
                    )
                    if self.category_status != "pinned"
                    else None
                ),
            },
            {
                "viewclass": "CoverDeleteDropdownTextItem",
                "text": "回收站",
                "leading_icon": "trash-can",
                "height": dp(50),
                "on_release": lambda: (
                    (
                        self.remove_cards(),
                        asynckivy.start(
                            self.set_cards(
                                self.bookmanager.find(status="deleted")
                                .sort(*self.current_sort_rule)
                                .books,
                                0,
                            )
                        ),
                        self.set_category_status("deleted"),
                    )
                    if self.category_status != "deleted"
                    else None
                ),
            },
        ]
        menu.items.extend(menu_items)
        menu.on_enter = menu.on_leave
        self._category_menu_open(menu, button)

    def set_category_status(self, category_status: str) -> None:
        """Set the category status."""
        self.category_status = category_status

    def pin_bookcard(self, button, menu=None) -> None:
        """Pin the bookcard containing the button."""
        book = self.bookmanager.pin_book(button.parent.parent.bookid)

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

    def unpin_bookcard(self, button, menu=None) -> None:
        """Unpin the bookcard containing the button."""
        book = self.bookmanager.restore_book(button.parent.parent.bookid)

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

    def restore_bookcard(self, button, menu=None) -> None:
        """Restore the bookcard containing the button."""
        self.bookmanager.restore_book(button.parent.parent.bookid)
        button.parent.parent.status = "normal"
        self.root.ids.grid.remove_widget(button.parent.parent)
        if menu:
            menu.dismiss()

    def get_bookcard_info(self, button, menu=None) -> None:
        """Pin the bookcard containing the button."""

    def delete_bookcard(self, button, menu=None) -> None:
        """Delete the bookcard."""
        self.bookmanager.del_book(button.parent.parent.bookid)
        self.root.ids.grid.remove_widget(button.parent.parent)
        if menu:
            menu.dismiss()

    def get_radius(
        self, nav: Optional[Literal["left", "right"]] = None
    ) -> tuple[list, list]:
        """Get the radius and the shadow-radius."""
        if self.test_bookcard is None:
            self.test_bookcard = BookCard(style="elevated")
        radius, shadow_radius = (
            self.test_bookcard.radius.copy(),
            self.test_bookcard.shadow_radius,
        )
        match nav:
            case "left":
                radius[0] = 0
                radius[3] = 0
            case "right":
                radius[1] = 0
                radius[2] = 0
        return radius, shadow_radius

    def open_nav_drawer(self, name: str) -> None:
        """Open the nav-drawer."""
        nav_drawer = getattr(self.root.ids, name)
        nav_drawer.set_state("toggle")

    def show_alert_dialog(self, button, menu):
        """Show alert dialog on deleting a book."""
        dialog = MDDialog(
            # ----------------------------Icon-----------------------------
            MDDialogIcon(icon="delete-alert"),
            # -----------------------Headline text-------------------------
            MDDialogHeadlineText(
                text="永久删除此书？", font_style="NavText", role="large"
            ),
            # -----------------------Supporting text-----------------------
            MDDialogSupportingText(
                text="这将会移除该书的所有本地文件和缓存, 并且无法再次恢复, 建议您在此之前"
                "保留好书籍的备份:",
                font_style="NavText",
                role="small",
            ),
            # -----------------------Custom content------------------------
            MDDialogContentContainer(
                MDDivider(),
                MDListItem(
                    MDListItemLeadingIcon(
                        icon="book-open-variant-outline",
                    ),
                    MDListItemSupportingText(
                        text=button.parent.parent.title,
                        font_style="NavText",
                        role="small",
                    ),
                    theme_bg_color="Custom",
                    md_bg_color=self.theme_cls.transparentColor,
                ),
                MDDivider(),
                orientation="vertical",
            ),
            # ---------------------Button container------------------------
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="确认删除",
                        font_style="NavText",
                        role="small",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.errorColor,
                    ),
                    style="text",
                    on_release=lambda _: (
                        dialog.dismiss(),
                        menu.dismiss(),
                        self.bookmanager.del_book_entirely(button.parent.parent.bookid),
                        self.root.ids.grid.remove_widget(button.parent.parent),
                    ),
                ),
                MDButton(
                    MDButtonText(text="取消", font_style="NavText", role="small"),
                    style="text",
                    on_release=lambda _: (dialog.dismiss(), menu.dismiss()),
                ),
                spacing="8dp",
            ),
            # -------------------------------------------------------------
        )
        dialog.open()

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

    def _plus_menu_open(self, menu: MDDropdownMenu, caller: Any) -> None:
        # pylint: disable=protected-access
        menu.set_menu_properties()

        Window.add_widget(menu)
        menu.position = menu.adjust_position()

        menu.width = dp(160)

        menu.height = menu.target_height
        menu._tar_x, menu._tar_y = menu.get_target_pos()
        button_pos = caller.to_window(*caller.pos)
        menu.x = caller.to_window(*caller.pos)[0] + caller.width - menu.width - dp(5)
        menu.y = button_pos[1] - menu.height - dp(5)
        menu.scale_value_center = menu.caller.to_window(*menu.caller.center)
        menu.set_menu_pos()
        # pylint: enable=protected-access
        _menu_on_open(menu)

    def _category_menu_open(self, menu: MDDropdownMenu, caller: Any) -> None:
        # pylint: disable=protected-access
        menu.set_menu_properties()

        Window.add_widget(menu)
        menu.position = menu.adjust_position()

        menu.width = dp(160)

        menu.height = menu.target_height
        menu._tar_x, menu._tar_y = menu.get_target_pos()
        button_pos = caller.to_window(*caller.pos)
        menu.x = caller.to_window(*caller.pos)[0] + caller.width - menu.width
        menu.y = button_pos[1] - menu.height - dp(8)
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


def _button_auto_dismiss(button, on_dismiss):
    x, y = Window.mouse_pos
    x1, y1 = button.to_window(*button.pos)
    x2 = x1 + button.to_window(button.width, 0)[0]
    y2 = y1 + button.to_window(0, button.height)[1]
    if not (x1 <= x <= x2 and y1 <= y <= y2):
        button.dismiss()
    on_dismiss()
