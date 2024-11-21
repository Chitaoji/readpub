"""Preview all the fonts."""

from pathlib import Path
from typing import Optional

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
                icon: 'form-textbox'
                pos_hint: {'center_y': .5}

            MDTextField:
                id: search_field
                hint_text: 'Search icon'
                on_text: root.set_list_items(self.text)
        
        MDBoxLayout:
            adaptive_height: True

            MDIconButton:
                icon: 'magnify'
                pos_hint: {'center_y': .5}

            MDTextField:
                id: search_field
                hint_text: 'Search icon'
                on_text: root.set_list_items(self.text, True)

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
        self.__searched_style, self.__text = "", ""

    def set_list_items(self, text="", search=False):
        """Builds a list of icons for the screen."""
        self.ids.rv.data = []
        for styl in self.app.font_names:
            if styl in {"mstmc"}:
                continue
            if search:
                if self.get_searched_style(text.lower()) in styl.lower():
                    self.add_font_item(styl, self.get_text(default=styl))
            elif self.get_searched_style() in styl.lower():
                self.add_font_item(styl, self.get_text(text, default=styl))

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

    def get_searched_style(self, maybe_style: Optional[str] = None, /) -> str:
        """Get the style."""
        if maybe_style is not None:
            self.__searched_style = maybe_style
        return self.__searched_style

    def get_text(self, maybe_text: Optional[str] = None, /, default: str = "") -> str:
        """Get the text."""
        if maybe_text is not None:
            self.__text = maybe_text
        return self.__text if self.__text else default


class FontPreview(MDApp):
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
        self.screen.set_list_items()


if __name__ == "__main__":
    FontPreview().run()
