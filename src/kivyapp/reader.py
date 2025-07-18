"""
Contains a book reader: Reader.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

# pylint: disable=no-name-in-module
from typing import TYPE_CHECKING

import asynckivy
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.image import Image
from kivy.uix.screenmanager import FadeTransition
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDListItem

from ..bookmanager import AlternativeCharacter, BookImage

if TYPE_CHECKING:
    from ..bookmanager._typing import Book
    from .core import MainApp

__all__ = ["Reader"]


class BookContentItem(MDListItem):
    """Book Content."""

    text = StringProperty()
    npage = NumericProperty()


class Reader:
    """Implements a book reader."""

    def __init__(self, app: "MainApp") -> None:
        self.app = app
        self.disabled: bool = True
        self.book: "Book | None" = None

    def homepage(self):
        """Return to the homepage."""
        self.app.cards.check()
        self.app.root.transition = FadeTransition()
        self.app.root.current = "MainScreen"
        self.app.switch_screen()
        self.close()
        self.delete_content()

    def on_touch_down(self, _, touch):
        """On mouse down."""
        if not self.disabled:
            lb, rb = Window.width / 3, Window.width * 2 / 3
            if Window.height * 0.2 < touch.y < Window.height * 0.8:
                if lb < touch.x < rb:
                    self.toggle_toolbar()
                elif touch.x <= lb:
                    self.prev_page()
                elif touch.x >= rb:
                    self.next_page()

    def toggle_toolbar(self) -> None:
        """Toggle the opacity of toolbar."""
        if (toolbar := self.app.root.ids.reader_toolbar).disabled:
            asynckivy.start(self.activate_reader_toolbar())
        else:
            self.app.root.ids.reader_bottom.disabled = toolbar.disabled = True
            self.app.root.ids.reader_bottom.opacity = toolbar.opacity = 0

    async def activate_reader_toolbar(self) -> None:
        """Activate reader toolbar."""
        self.fix_reader_search_field()
        self.app.root.ids.reader_toolbar.disabled = False
        await asynckivy.sleep(0.15)
        if not self.app.root.ids.reader_toolbar.disabled:
            self.app.root.ids.reader_search_field_helper.text = ""
            self.app.root.ids.reader_toolbar.opacity = 1
        self.app.root.ids.reader_bottom.disabled = False
        self.app.root.ids.reader_bottom.opacity = 1

    def fix_reader_search_field(self):
        """Fix the search field."""
        field = self.app.root.ids.reader_search_field
        field.set_texture_color(
            getattr(field, "_helper_text_label"),
            field.canvas.before.get_group("helper-text-color")[0],
            self.app.theme_cls.transparentColor,
        )

    def open(self, bookid: str) -> None:
        """Open a book."""
        if self.book is not None:
            if self.book.bookid != bookid:
                self.book.release()
        self.book = self.app.bookmanager.books[bookid]
        self.book.adjust(
            page_height=min(Window.height * 0.7, 900),
            page_width=min(Window.width * 0.4, 1000),
        )

        self.book.typeset()
        self.book.open()
        self.turn_to_page(self.book.pagenow)

    def close(self) -> None:
        """Close the book."""
        for bookcard in self.app.root.ids.grid.children:
            if bookcard.bookid == self.book.bookid:
                bookcard.progress = f"阅读到 {self.book.pagenow/self.book.pagemax:.2%}"
                break
        self.book.close()
        for widget in list((box := self.app.root.ids.textbox).children):
            box.remove_widget(widget)

    def next_page(self) -> None:
        """Next page."""
        if self.book.pagenow >= self.book.pagemax:
            return
        self.turn_to_page(self.book.pagenow + 1)

    def prev_page(self) -> None:
        """Previous page."""
        if self.book.pagenow <= 1:
            return
        self.turn_to_page(self.book.pagenow - 1)

    def turn_to_page(self, n: int) -> None:
        """Turn to page n."""
        if n < 1:
            n = 1
        page = self.book.turn_to_page(n)
        box = self.app.root.ids.textbox
        for widget in list((box := self.app.root.ids.textbox).children):
            box.remove_widget(widget)
        for widget in list((imgbox := self.app.root.ids.imagebox).children):
            imgbox.remove_widget(widget)
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
            elif isinstance(para, BookImage):
                Logger.info('Image: Loading image at "%s"', para.path)
                imgbox.add_widget(Image(source=para.path.as_posix()))
            elif isinstance(para, AlternativeCharacter):
                font_style, role = self.app.font.getstyle(
                    para.font_name, self.book.settings.fontsize
                )
                box.add_widget(
                    MDLabel(
                        adaptive_width=True,
                        font_style=font_style,
                        role=role,
                        text=para.char,
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
        self.app.root.ids.progress_button.text = (
            f"{self.book.pagenow}/{self.book.pagemax}"
            f"  {self.book.pagenow/self.book.pagemax:.2%}"
        )

    def truly_disable(self) -> None:
        """Disable the reader."""
        self.disabled = True

    def truly_enable(self) -> None:
        """Enable the reader."""
        self.disabled = False

    def generate_content(self):
        """Generate the book content."""
        if len(self.app.root.ids.rv_content.children) > 0:
            return
        self.__generate_content(self.book.get_content()[0][0].content)

    def __generate_content(self, content, indent: int = 0):
        box = self.app.root.ids.rv_content
        for x in content:
            if x.title.text != "Unknown":
                box.add_widget(
                    BookContentItem(
                        text=" " * indent * 4 + x.title.text, npage=x.title.npage
                    )
                )
            if len(x.content) > 0:
                self.__generate_content(x.content, indent=indent + 1)

    def delete_content(self):
        """Delete the book content."""
        box = self.app.root.ids.rv_content
        for widget in list(box.children):
            box.remove_widget(widget)
