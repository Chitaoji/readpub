"""
Contains the core of kivyapp: KivyApp, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

try:
    from . import config as _
except ImportError:
    ...
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty  # pylint: disable=no-name-in-module
from kivymd.app import MDApp
from kivymd.uix.card import MDCard

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
<MyCard>
    padding: "4dp"
    size_hint: None, None
    size: "360dp", "150dp"

    MDRelativeLayout:

        MDIconButton:
            icon: "dots-vertical"
            pos_hint: {"top": 1, "right": 1}

        MDLabel:
            text: root.text
            adaptive_size: True
            color: "grey"
            pos: "12dp", "12dp"
            bold: True
            theme_font_name: "Custom"
            font_name: 'msyh'


MDScreen:
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        id: box
        adaptive_size: True
        spacing: "12dp"
        pos_hint: {"center_x": .5, "center_y": .5}
        
"""


class MyCard(MDCard):
    """Implements a material card."""

    text = StringProperty()

    # def on_touch_down(self, *args):
    #     print(args)
    # super().on_touch_down(*args)


class KivyApp(MDApp):
    """Kivy-App for ReadPub."""

    def build(self):
        self.theme_cls.theme_style = "Dark"
        # self.theme_cls.primary_palette = "Darkgoldenrod"
        return Builder.load_string(KV)

    def on_start(self):
        for i in range(3):
            self.root.ids.box.add_widget(MyCard(style="elevated", text=f"卡片{i}"))

    def open_settings(self, *_): ...
