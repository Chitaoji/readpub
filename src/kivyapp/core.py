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
from kivy.metrics import sp
from kivy.properties import StringProperty  # pylint: disable=no-name-in-module
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu

from ..bookmanager import BookManager

__all__ = ["KivyApp"]


LabelBase.register(name="msyh", fn_regular=r"C:\Windows\Fonts\msyh.ttc")
LabelBase.register(name="msyhbd", fn_regular=r"C:\Windows\Fonts\msyhbd.ttc")
LabelBase.register(name="simhei", fn_regular=r"C:\Windows\Fonts\simhei.ttf")


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
            pos_hint: {"bottom": 1, "right": 1}
            on_release: app.menu_open(self)

        MDBoxLayout:
            adaptive_height: True
            orientation: "vertical"
            padding: "190dp", "0dp", "10dp", "0dp"
            pos_hint: {"top": .88}
            spacing: "26dp"
            
            MDLabel:
                text: root.title
                font_style: "BookCover"
                role: "large"
                
                adaptive_height: True
                pos_hint: {"top": 1}
                
            MDLabel:
                text: root.author
                font_style: "BookCover"
                role: "small"
                color: "grey"
                
        MDLabel:
            text: root.progress
            font_style: "BookCover"
            role: "small"
            color: "grey"
            adaptive_height: True
            padding: "190dp", "0dp", "10dp", "16dp"
            pos_hint: {"bottom": 1}
                

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
            padding: "240dp"
        
"""


class BookCard(MDCard):
    """Implements a material card."""

    bookid = StringProperty()
    image = StringProperty()
    title = StringProperty()
    author = StringProperty()
    progress = StringProperty()

    # def on_release(self, *args):
    #     super().on_release(*args)


class KivyApp(MDApp):
    """Kivy-App for ReadPub."""

    bookmanager: BookManager

    def build(self):
        self.title = "ReadPub"
        # self.theme_cls.theme_style = "Dark"
        # self.theme_cls.primary_palette = "Green"
        self.theme_cls.font_styles["BookCover"] = {
            "large": {
                "line-height": 1.28,
                "font-name": "msyhbd",
                "font-size": sp(21),
            },
            "medium": {
                "line-height": 1.24,
                "font-name": "msyh",
                "font-size": sp(20),
            },
            "small": {
                "line-height": 1.2,
                "font-name": "msyh",
                "font-size": sp(16),
            },
        }
        return Builder.load_string(KV)

    def on_start(self):
        m = BookManager(kivyconfig.path.parent)

        async def set_cards(duration: Optional[float] = None):
            for bookid, book in m.books.items():
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
                )
                self.root.ids.grid.add_widget(widget)
                if duration is not None:
                    await asynckivy.sleep(duration)

        asynckivy.start(set_cards())
        self.bookmanager = m

    def open_settings(self, *_): ...

    def menu_open(self, button):
        menu_items = [
            {
                "text": f"Item {i}",
                "on_release": lambda x=f"Item {i}": self.menu_callback(x),
            }
            for i in range(5)
        ]
        MDDropdownMenu(caller=button, items=menu_items, ver_growth="up").open()

    def menu_callback(self, text_item):
        print(text_item)
