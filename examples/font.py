"""Preview all the fonts."""

from pathlib import Path

from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.metrics import sp
from kivy.properties import StringProperty  # pylint: disable=E0611:no-name-in-module
from kivymd.app import MDApp
from kivymd.uix.list import MDListItem
from kivymd.uix.screen import MDScreen

Builder.load_string(
    """
<FontItem>
    MDListItemHeadlineText:
        text: root.text
        font_style: root.style if root.style else "Title"
        
    MDListItemSupportingText:
        text: root.style
        
<FontMenu>
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(20)

        MDBoxLayout:
            adaptive_height: True

            MDIconButton:
                icon: 'magnify'
                pos_hint: {'center_y': .5}

            MDTextField:
                id: search_field
                hint_text: 'Search icon'
                on_text: root.set_list_md_icons(self.text, True)

        RecycleView:
            id: rv
            key_viewclass: 'viewclass'
            key_size: 'height'

            RecycleBoxLayout:
                padding: dp(10), dp(10), 0, dp(10)
                default_size: None, dp(80)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
                
"""
)


class FontItem(MDListItem):
    """Font item."""

    style = StringProperty()
    text = StringProperty()


class FontMenu(MDScreen):
    """Font menu screen."""

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app

    def set_list_md_icons(self, text="", search=False):
        """Builds a list of icons for the screen."""
        self.ids.rv.data = []
        for styl in self.app.theme_cls.font_styles:
            if styl in {
                "Icon",
                "Display",
                "Headline",
                "Title",
                "Body",
                "Label",
                "mstmc",
                "HYZhongHeiTi-197",
                "segmdl2",
            }:
                continue
            if search:
                print(text)
                self.add_font_item(styl, text)
            else:
                self.add_font_item(styl, styl)

    def add_font_item(self, font_style: str, text: str):
        """Add an icon item."""
        self.ids.rv.data.append(
            {
                "viewclass": "FontItem",
                "style": font_style,
                "text": text,
                "callback": lambda x: x,
            }
        )


class IconPreview(MDApp):
    """Example application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen = FontMenu(self)
        self.font_names: list[str] = []
        self.__get_all_fonts()

    def __get_all_fonts(self) -> None:
        """Get all the available fonts."""
        for p in Path("C:\\Windows\\Fonts").iterdir():
            if p.suffix in {".ttf", ".ttc"}:
                self.register(p.stem, p, p.stem, 21)
            self.font_names.append(p.stem)

    def register(
        self, font_name: str, font_path: Path, font_style: str, font_size: float
    ) -> None:
        """Register a new font."""
        LabelBase.register(name=font_name, fn_regular=font_path.as_posix())
        font_properties = {
            "large": {
                "line-height": 1.28,
                "font-name": font_name,
                "font-size": sp(font_size),
            }
        }
        self.theme_cls.font_styles[font_style] = font_properties

    def build(self):
        return self.screen

    def on_start(self):
        self.screen.set_list_md_icons()


if __name__ == "__main__":
    IconPreview().run()
