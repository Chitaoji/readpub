"""
Contains a kivy app: Reader.

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

from ..bookmanager import BookImage

if TYPE_CHECKING:
    from ._typing import BasicApp
else:
    from kivymd.app import MDApp as BasicApp

__all__ = ["Reader"]


class BookContentItem(MDListItem):
    """Book Content."""

    text = StringProperty()
    npage = NumericProperty()


class Reader(BasicApp):
    """Implements a reader app."""

    def homepage(self):
        """Return to the homepage."""
        self.check_cards()
        self.root.transition = FadeTransition()
        self.root.current = "MainScreen"
        self.close_book()
        self.delete_content()

    def on_reader_touch_down(self, _, touch):
        """On mouse down."""
        if not self.reader_disabled:
            lb, rb = Window.width / 3, Window.width * 2 / 3
            if Window.height * 0.2 < touch.y < Window.height * 0.8:
                if lb < touch.x < rb:
                    if (toolbar := self.root.ids.reader_toolbar).disabled:
                        asynckivy.start(self.activate_reader_toolbar())
                    else:
                        self.root.ids.reader_bottom.disabled = toolbar.disabled = True
                        self.root.ids.reader_bottom.opacity = toolbar.opacity = 0
                elif touch.x <= lb:
                    self.prev_page()
                elif touch.x >= rb:
                    self.next_page()

    async def activate_reader_toolbar(self) -> None:
        """Activate reader toolbar."""
        self.fix_reader_search_field()
        self.root.ids.reader_toolbar.disabled = False
        await asynckivy.sleep(0.15)
        if not self.root.ids.reader_toolbar.disabled:
            self.root.ids.reader_search_field_helper.text = ""
            self.root.ids.reader_toolbar.opacity = 1
        self.root.ids.reader_bottom.disabled = False
        self.root.ids.reader_bottom.opacity = 1

    def fix_reader_search_field(self):
        """Fix the search field."""
        field = self.root.ids.reader_search_field
        field.set_texture_color(
            getattr(field, "_helper_text_label"),
            field.canvas.before.get_group("helper-text-color")[0],
            self.theme_cls.transparentColor,
        )

    def open_book(self, bookid: str) -> None:
        """Open a book."""
        if self.book is not None:
            if self.book.bookid != bookid:
                self.book.release()
        self.book = self.bookmanager.books[bookid]
        self.book.adjust(
            page_height=min(Window.height * 0.7, 900),
            page_width=min(Window.width * 0.4, 1000),
        )

        self.book.typeset()
        self.book.open()
        self.turn_to_page(self.book.pagenow)

    def close_book(self) -> None:
        """Close the book."""
        for bookcard in self.root.ids.grid.children:
            if bookcard.bookid == self.book.bookid:
                bookcard.progress = f"阅读到 {self.book.pagenow/self.book.pagemax:.2%}"
                break
        self.book.close()
        for widget in list((box := self.root.ids.textbox).children):
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
        box = self.root.ids.textbox
        for widget in list((box := self.root.ids.textbox).children):
            box.remove_widget(widget)
        for widget in list((imgbox := self.root.ids.imagebox).children):
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
                Logger.info('Image: Loading image "%s"', para.path)
                imgbox.add_widget(Image(source=para.path.as_posix()))
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
        self.root.ids.progress_button.text = (
            f"{self.book.pagenow}/{self.book.pagemax}"
            f"  {self.book.pagenow/self.book.pagemax:.2%}"
        )

    def truly_disable_reader(self) -> None:
        """Disable the reader."""
        self.reader_disabled = True

    def truly_enable_reader(self) -> None:
        """Enable the reader."""
        self.reader_disabled = False

    def generate_content(self):
        """Generate the book content."""
        if len(self.root.ids.nav_content_box.children) > 0:
            return
        self.__generate_content(self.book.get_content()[0][0].content)

    def __generate_content(self, content, indent: int = 0):
        box = self.root.ids.nav_content_box
        for x in content:
            if x.title.text != "Unknown":
                box.add_widget(
                    BookContentItem(
                        text=" " * indent * 4 + x.title.text, npage=x.title.npage
                    )
                )
            # if 0 < len(x.content) and indent <= 0:
            #     self.__generate_content(x.content, indent=indent + 1)

    def delete_content(self):
        """Delete the book content."""
        box = self.root.ids.nav_content_box
        for widget in list(box.children):
            box.remove_widget(widget)
