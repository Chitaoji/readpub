"""Preview all the themes and palettes."""

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (  # pylint: disable=E0611:no-name-in-module
    ColorProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import hex_colormap
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu

KV = """
<ColorCard>
    orientation: "vertical"

    MDLabel:
        text: root.text
        color: "grey"
        adaptive_height: True

    MDCard:
        theme_bg_color: "Custom"
        md_bg_color: root.bg_color


MDScreen:
    md_bg_color: app.theme_cls.backgroundColor

    MDIconButton:
        on_release: app.open_menu(self)
        pos_hint: {"top": .98}
        x: "12dp"
        icon: "menu"

    MDRecycleView:
        id: card_list
        viewclass: "ColorCard"
        bar_width: 0
        size_hint_y: None
        height: root.height - dp(68)

        RecycleGridLayout:
            cols: 3
            spacing: "16dp"
            padding: "16dp"
            default_size: None, dp(56)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            
"""


class ColorCard(BoxLayout):
    """Color card."""

    text = StringProperty()
    bg_color = ColorProperty()


class ThemePreview(MDApp):
    """Example application."""

    menu: MDDropdownMenu = None

    def build(self):
        self.theme_cls.dynamic_color = False
        return Builder.load_string(KV)

    def get_instance_from_menu(self, name_item):
        """Get the view."""
        index = 0
        rv = self.menu.ids.md_menu
        opts = rv.layout_manager.view_opts
        datas = rv.data[0]

        for data in rv.data:
            if data["text"] == name_item:
                index = rv.data.index(data)
                break

        instance = rv.view_adapter.get_view(index, datas, opts[index]["viewclass"])

        return instance

    def open_menu(self, menu_button):
        """Open the menu."""
        menu_items = []
        for item, method in {
            "Set palette": self.set_palette,
            "Switch theme style": self.swicth_theme,
        }.items():
            menu_items.append({"text": item, "on_release": method})
        self.menu = MDDropdownMenu(caller=menu_button, items=menu_items)
        self.menu.open()

    def set_palette(self):
        """Set the palette."""
        instance_from_menu = self.get_instance_from_menu("Set palette")
        available_palettes = [
            name_color.capitalize() for name_color in list(hex_colormap)
        ]

        menu_items = []
        for name_palette in available_palettes:
            menu_items.append(
                {
                    "text": name_palette,
                    "on_release": lambda x=name_palette: self.switch_palette(x),
                }
            )
        MDDropdownMenu(caller=instance_from_menu, items=menu_items).open()

    def switch_palette(self, selected_palette):
        """Swicth the palette."""
        self.theme_cls.primary_palette = selected_palette
        Clock.schedule_once(self.generate_cards, 0.5)

    def swicth_theme(self) -> None:
        """Switch the theme."""
        self.theme_cls.switch_theme()
        Clock.schedule_once(self.generate_cards, 0.5)

    def generate_cards(self, *args):
        """Generate color cards."""
        self.root.ids.card_list.data = []
        for color in dir(self.theme_cls):
            if color.endswith("Color"):
                self.root.ids.card_list.data.append(
                    {
                        "bg_color": getattr(self.theme_cls, color),
                        "text": color,
                    }
                )

    def on_start(self):
        Clock.schedule_once(self.generate_cards)


if __name__ == "__main__":
    ThemePreview().run()
