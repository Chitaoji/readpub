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
import ctypes
import shutil
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import asynckivy
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.metrics import Metrics, dp, sp
from kivy.properties import ColorProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.menu.menu import BaseDropdownItem

from ..bookmanager import BookManager
from .bookcard import BookCardContainer
from .font import KivyFont
from .importer import FileImporter
from .input import InputMethod
from .reader import Reader

if TYPE_CHECKING:
    from kivy.config import ConfigParser

    from ._typing import VirtualApp
else:
    from kivymd.app import MDApp as VirtualApp


__all__ = ["MainApp"]


Window.maximize()
Logger.info(
    "Metrics: Window: dpi=%s, scale_factor=%s, dp(1)=%s, sp(1)=%s",
    Metrics.dpi,
    ctypes.windll.shcore.GetScaleFactorForDevice(0),
    dp(1),
    sp(1),
)


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


class MainApp(VirtualApp):
    """Kivy-App for ReadPub."""

    def get_application_config(self, defaultpath="") -> str:
        return kvconfig.get_ini_path(self).as_posix()

    def build_config(self, config: "ConfigParser") -> None:
        kvconfig.resgister(self, config)
        kvconfig[self].set_default(
            [
                ["main-screen", "theme_style", "Light"],
                ["main-screen", "primary_palette", "Blue"],
                ["main-screen", "background_image", ""],
                ["reader", "theme_style", "Light"],
                ["reader", "primary_palette", "Blue"],
            ]
        )

        self.font = KivyFont(Path("C:\\Windows\\Fonts"), self)
        self.input = InputMethod(self)
        self.cards = BookCardContainer(self)
        self.reader = Reader(self)

        self.theme_cls.theme_style = self.main_theme_style = kvconfig[self].get(
            "main-screen", "theme_style"
        )
        self.theme_cls.primary_palette = self.main_theme_palette = kvconfig[self].get(
            "main-screen", "primary_palette"
        )
        self.reader_theme_style = kvconfig[self].get("reader", "theme_style")
        self.reader_theme_palette = kvconfig[self].get("reader", "primary_palette")

        if (p := kvconfig[self].get("main-screen", "background_image")) and Path(
            p
        ).is_file():
            self.has_bgim = True
        else:
            self.has_bgim = False

        self.nav_now = None

    def build(self):
        self.title = "ReadPub"
        self.importer = FileImporter(self)

        if self.has_bgim:
            self.root.ids.bgim.source = kvconfig[self].get(
                "main-screen", "background_image"
            )
            self.root.ids.bgim.opacity = 1

    def on_start(self) -> None:
        m = BookManager(kvconfig.path.parent, sys_logger=Logger)

        asynckivy.start(
            self.cards.set(
                m.findnot(status="deleted").sort(*self.cards.current_sort_rule).books
            )
        )

        self.bookmanager = m
        self.init_color_buttons()

        self.root.get_screen("Reader").bind(on_touch_down=self.reader.on_touch_down)
        Window.bind(on_keyboard=self.on_keyboard)

    def on_stop(self) -> None:
        if self.reader.book:
            self.reader.book.close()

    def set_bgim(self, path: str | None = None) -> None:
        """Set a background image."""
        if path is None:
            self.root.ids.bgim.source = ""
            self.root.ids.bgim.opacity = 0
            self.has_bgim = False
            self.cards.setattr("theme_shadow_color", "Primary")
            self.cards.setattr("theme_bg_color", "Primary")
        else:
            self.root.ids.bgim.source = path
            self.root.ids.bgim.opacity = 1

            if pathnow := kvconfig[self].get("main-screen", "background_image"):
                Path(pathnow).unlink()
            savepath = (
                kvconfig.path.parent / f"background{Path(path).suffix}"
            ).as_posix()
            shutil.copyfile(path, savepath)
            kvconfig[self].update([["main-screen", "background_image", savepath]])

            self.has_bgim = True
            self.cards.setattr("theme_shadow_color", "Custom")
            self.cards.setattr("shadow_color", [0, 0, 0, 0])
            self.cards.setattr("theme_bg_color", "Custom")
        Clock.schedule_once(lambda *_: self.switch_theme_style(), 0)

    def trans_color(self, color: list[str], transparency: float = 0.4) -> str:
        """Adjust the color according to the transparency."""
        if self.has_bgim:
            return color[:-1] + [transparency]
        return color

    def trans_color_topbar(self, color: list[str], transparency: float = 0.0) -> str:
        """Adjust the color of topbars according to the transparency."""
        if self.has_bgim:
            return color[:-1] + [transparency]
        return [0, 0, 0, 0]

    def on_keyboard(self, _, key, *__):
        """On keyboard."""
        match key:
            case 292:  # F11
                match Window.fullscreen:
                    case "auto":
                        Window.fullscreen = False
                    case False:
                        Window.fullscreen = "auto"
            case 286:  # F5
                if self.root.current == "MainScreen":
                    self.close_nav_drawer()
                    self.cards.remove()
                    self.cards.set_category(self.cards.current_category)
            case 281:  # PgDn
                if self.root.current == "Reader":
                    self.reader.next_page()
            case 280:  # PgUp
                if self.root.current == "Reader":
                    self.reader.prev_page()
            case 278:  # Home
                if self.root.current == "Reader":
                    self.reader.toggle_toolbar()
            case 27:  # Esc
                if self.root.current == "Reader":
                    if self.nav_now:
                        self.close_nav_drawer()
                    else:
                        self.reader.homepage()
                elif not self.nav_now:
                    self.open_nav_drawer("nav_setting")

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
        """Switch the theme-style, and update the config."""
        if self.root.current == "Reader":
            if not to:
                to = "Dark" if self.reader_theme_style == "Light" else "Light"
            self.theme_cls.theme_style = self.reader_theme_style = to
            kvconfig[self].update([["reader", "theme_style", to]])
        else:
            if not to:
                to = "Dark" if self.main_theme_style == "Light" else "Light"
            self.theme_cls.theme_style = self.main_theme_style = to
            self.cards.check()
            kvconfig[self].update([["main-screen", "theme_style", to]])

    def switch_theme_palette(self, color: str):
        """Switch the theme-palette."""
        if self.root.current == "Reader":
            self.theme_cls.primary_palette = self.reader_theme_palette = color
            kvconfig[self].update([["reader", "primary_palette", color]])
        else:
            self.theme_cls.primary_palette = self.main_theme_palette = color
            kvconfig[self].update([["main-screen", "primary_palette", color]])

    def switch_theme(self) -> None:
        """Switch the theme-style."""
        if self.root.current == "Reader":
            self.theme_cls.theme_style = self.reader_theme_style
            self.theme_cls.primary_palette = self.reader_theme_palette
        else:
            self.theme_cls.theme_style = self.main_theme_style
            self.theme_cls.primary_palette = self.main_theme_palette

    def switch_fullscreen(self):
        """Switch between fullscreen and windowed screen."""
        Window.fullscreen = "auto" if Window.fullscreen is False else False

    def reset_theme(self):
        """Reset the theme."""
        self.switch_theme_style(to="Light")
        self.switch_theme_palette("Blue")

    def open_plus_menu(self, button) -> None:
        """Open the menu on releasing the plus button."""
        radius, shadow_radius = self.cards.get_radius()
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
                "leading_icon": "import",
                "height": dp(50),
                "on_release": lambda: (self.importer.open(), menu.dismiss()),
            },
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "回到首页",
                "leading_icon": "home-outline",
                "height": dp(50),
                "on_release": lambda: (
                    self.cards.set_category("home")
                    if self.cards.current_category != "home"
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
        radius, shadow_radius = self.cards.get_radius()
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
                    self.cards.set_category("home")
                    if self.cards.current_category != "home"
                    else None
                ),
            },
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "已置顶",
                "leading_icon": "pin",
                "height": dp(50),
                "on_release": lambda: (
                    self.cards.set_category("pinned")
                    if self.cards.current_category != "pinned"
                    else None
                ),
            },
            {
                "viewclass": "CoverDeleteDropdownTextItem",
                "text": "回收站",
                "leading_icon": "trash-can",
                "height": dp(50),
                "on_release": lambda: (
                    self.cards.set_category("deleted")
                    if self.cards.current_category != "deleted"
                    else None
                ),
            },
        ]
        menu.items.extend(menu_items)
        menu.on_enter = menu.on_leave
        self.open_menu(menu, button, rely=-dp(8), on_left=True, on_bottom=True)

    def open_nav_drawer(self, name: str) -> None:
        """Open the nav-drawer."""
        nav_drawer = getattr(self.root.ids, name)
        nav_drawer.set_state("toggle")
        self.nav_now = nav_drawer

    def close_nav_drawer(self) -> None:
        """Open the current nav-drawer."""
        if self.nav_now:
            self.nav_now.set_state("toggle")
        self.nav_now = None

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
        menu.x = (
            button_pos[0] + caller.width - menu.width * on_left + relx
            if absx is None
            else absx
        )
        menu.y = (
            button_pos[1] - menu.height * on_bottom + rely if absy is None else absy
        )
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
