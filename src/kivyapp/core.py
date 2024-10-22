"""
Contains the core of kivyapp: KivyApp, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

try:
    from .config import kivyconfig
except ImportError as e:
    raise e

from typing import Optional

import asynckivy
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty  # pylint: disable=no-name-in-module
from kivy.uix.image import Image
from kivymd.app import MDApp
from kivymd.uix.card import MDCard

from ..bookmanager import BookManager

__all__ = ["KivyApp"]


LabelBase.register(name="msyh", fn_regular=r"C:\Windows\Fonts\msyh.ttc")


def _on_key_up(key, *_):
    if key == 292:  # "F11"
        match Window.fullscreen:
            case "auto":
                Window.fullscreen = False
            case False:
                Window.fullscreen = "auto"


Window.on_key_up = _on_key_up
Window.maximize()

KV = """
<BookCard>
    padding: "4dp"
    size_hint: None, None
    size: "480dp", "240dp"
    
    MDRelativeLayout:
    
        Image:
            source: root.image
            fit_mode: "scale-down"
            pos_hint: {"center_x": .2, "center_y": .5}
            

    
        MDIconButton:
            icon: "dots-vertical"
            pos_hint: {"top": 1, "right": 1}

        MDLabel:
            text: root.text
            adaptive_size: True
            color: "grey"
            pos_hint: {"x": .4}
            bold: True
            theme_font_name: "Custom"
            font_name: 'msyh'


MDScreen:
    md_bg_color: self.theme_cls.backgroundColor

    MDScrollView:
        do_scroll_x: False
        do_scroll_y: True
        scroll_x: .5
        scroll_type: ["content", "bars"]
        scroll_wheel_distance: 80
        bar_width: "12dp"
        bar_inactive_color: root.theme_cls.backgroundColor
        
        MDGridLayout:
            id: grid
            cols: 3
            adaptive_size: True
            spacing: ["24dp", "24dp"]
            padding: "360dp"
        
"""


class BookCard(MDCard):
    """Implements a material card."""

    text = StringProperty()
    image = StringProperty()

    # def on_touch_down(self, *args):
    #     print(args)
    # super().on_touch_down(*args)


class KivyApp(MDApp):
    """Kivy-App for ReadPub."""

    bookmanager: BookManager

    def build(self):
        self.title = "ReadPub"
        # self.theme_cls.theme_style = "Dark"
        # self.theme_cls.primary_palette = "Green"

        return Builder.load_string(KV)

    def on_start(self):
        m = BookManager(kivyconfig.path.parent)

        async def set_cards(duration: Optional[float] = None):
            for bookid, book in m.books.items():
                metadata = book.get_metadata()
                widget = BookCard(
                    style="elevated",
                    text=metadata["title"],
                    image=metadata["coverpath"],
                )
                self.root.ids.grid.add_widget(widget)
                if duration is not None:
                    await asynckivy.sleep(duration)

        asynckivy.start(set_cards())
        self.bookmanager = m

    def open_settings(self, *_): ...
