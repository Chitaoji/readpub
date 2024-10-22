"""
Contains the core of kivyapp: KivyApp, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

try:
    from .config import local_config
except ImportError as e:
    raise e

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
    size: "480dp", "240dp"

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

    MDScrollView:
        do_scroll_x: False
        do_scroll_y: True
        scroll_x: .5
        scroll_type: ["content", "bars"]
        scroll_wheel_distance: 80
        bar_width: "12dp"
        bar_inactive_color: root.theme_cls.backgroundColor
        
        MDGridLayout:
            id: box
            cols: 3
            adaptive_size: True
            spacing: ["24dp", "24dp"]
            padding: "360dp"
            pos_hint: {"center_y": .9}
        
"""


class MyCard(MDCard):
    """Implements a material card."""

    text = StringProperty()

    # def on_touch_down(self, *args):
    #     print(args)
    # super().on_touch_down(*args)


# async def set_panel_list():
#     for i in range(12):
#         await asynckivy.sleep(0)
#         self.root.ids.container.add_widget(ExpansionPanelItem())


class KivyApp(MDApp):
    """Kivy-App for ReadPub."""

    def build(self):
        self.title = "ReadPub"
        self.theme_cls.theme_style = "Dark"
        # self.theme_cls.primary_palette = "Darkgoldenrod"
        return Builder.load_string(KV)

    def on_start(self):
        for i in range(31):
            self.root.ids.box.add_widget(MyCard(style="elevated", text=f"卡片{i}"))

    def open_settings(self, *_): ...

    def _update_local_config(self, commands: list[list]) -> None:
        local_config.update(commands)
