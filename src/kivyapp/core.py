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
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import asynckivy
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import ColorProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.menu.menu import BaseDropdownItem

from ..bookmanager import BookManager
from .bookcard import BookCardContainer
from .font import KivyFont
from .importer import FakeModalView, FileImporter, FileImporterManager
from .reader import Reader

if TYPE_CHECKING:
    from kivy.config import ConfigParser


__all__ = ["MainApp"]


Window.maximize()
# if Window.width <= 1920:
#     Metrics.dpi = 96


class ColorCard(BoxLayout):
    """Implements a material card."""

    text = StringProperty()
    bg_color = ColorProperty()


class CoverDropdownTextItem(BaseDropdownItem):
    """Implements a menu item with text without leading and trailing icons."""


class CoverDeleteDropdownTextItem(CoverDropdownTextItem):
    """Implements a menu item with text without leading and trailing icons."""


class ColorButton(MDButton):
    """Button with color."""

    color: str = StringProperty()


class MainApp(Reader, BookCardContainer, FileImporter):
    """Kivy-App for ReadPub."""

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

        self.fontmanager = KivyFont(Path("C:\\Windows\\Fonts"), self)
        self.theme_cls.theme_style = kvconfig[self].get("theme-cls", "theme_style")
        self.theme_cls.primary_palette = kvconfig[self].get(
            "theme-cls", "primary_palette"
        )

        self.test_bookcard = None

    def build(self):
        self.title = "ReadPub"

        self.filemanager = FileImporterManager(
            exit_manager=self.filemanager_exit, select_path=self.filemanager_select_path
        )
        setattr(self.filemanager, "_window_manager", FakeModalView())
        self.has_filemanager = False
        self.prev_snackbar = None

        self.reader_disabled = True
        self.book = None

    def on_start(self) -> None:
        m = BookManager(kvconfig.path.parent, logger=Logger)
        self.current_sort_rule = ["status", "uploadtime"]

        asynckivy.start(
            self.set_cards(
                m.findnot(status="deleted").sort(*self.current_sort_rule).books
            )
        )
        self.category_status = "home"

        self.bookmanager = m
        self.init_color_buttons()

        self.root.get_screen("Reader").bind(on_touch_down=self.on_reader_touch_down)
        Window.bind(on_keyboard=self.on_keyboard)

    def on_keyboard(self, _, key, *__):
        """On keyboard."""
        if key == 292:  # "F11"
            match Window.fullscreen:
                case "auto":
                    Window.fullscreen = False
                case False:
                    Window.fullscreen = "auto"
        elif key == 281:  # PgDn
            if self.root.current == "Reader":
                self.next_page()
        elif key == 280:  # PgUp
            if self.root.current == "Reader":
                self.prev_page()
        elif key == 278:  # Home
            if self.root.current == "Reader":
                self.homepage()

    def open_settings(self, *_) -> None: ...

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

    async def asynctest(self, time: int, duration: Optional[float] = None):
        """Test the async functionality."""
        for i in range(1, 1 + time):
            if duration is not None:
                await asynckivy.sleep(duration)
            Logger.info("Test: Test Step No.%s", str(i))

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

    def switch_fullscreen(self):
        """Switch between fullscreen and windowed screen."""
        Window.fullscreen = "auto" if Window.fullscreen is False else False

    def switch_theme_palette(self, color: str):
        """Switch the theme-palette."""
        self.theme_cls.primary_palette = color
        kvconfig[self].update([["theme-cls", "primary_palette", color]])

    def reset_theme(self):
        """Reset the theme."""
        self.switch_theme_style(to="Light")
        self.switch_theme_palette("Blue")

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
            width=dp(160),
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
        self.open_menu(
            menu, button, relx=-dp(5), rely=-dp(5), on_left=True, on_bottom=True
        )

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
            width=dp(160),
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
        self.open_menu(menu, button, rely=-dp(8), on_left=True, on_bottom=True)

    def set_category_status(self, category_status: str) -> None:
        """Set the category status."""
        self.category_status = category_status

    def open_nav_drawer(self, name: str) -> None:
        nav_drawer = getattr(self.root.ids, name)
        nav_drawer.set_state("toggle")

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
        menu.set_menu_properties()

        if check_ver_growth:
            coord_y = menu._start_coords[1]  # pylint: disable=protected-access
            if menu.target_height > coord_y - menu.border_margin:
                menu.ver_growth = "up"
            elif coord_y > Window.height - menu.border_margin - menu.target_height:
                menu.ver_growth = "down"

        Window.add_widget(menu)
        menu.position = menu.adjust_position()

        menu.height = menu.target_height
        menu._tar_x, menu._tar_y = (
            menu.get_target_pos()
        )  # pylint: disable=protected-access
        button_pos = caller.to_window(*caller.pos)
        menu.x = button_pos[0] + caller.width - menu.width * on_left + relx
        menu.y = button_pos[1] - menu.height * on_bottom + rely
        menu.scale_value_center = menu.caller.to_window(*menu.caller.center)
        menu.set_menu_pos()
        menu_on_open(menu, show_duration_x)


def menu_on_open(menu: MDDropdownMenu, show_duration_x: Optional[float] = None) -> None:
    """On opening menu."""
    if show_duration_x is None:
        show_duration_x = menu.show_duration - 0.3
    anim = Animation(
        _scale_y=1,
        duration=menu.show_duration,
        transition=menu.show_transition,
    )
    anim &= Animation(
        _scale_x=1,
        duration=max(show_duration_x, 0.0),
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
