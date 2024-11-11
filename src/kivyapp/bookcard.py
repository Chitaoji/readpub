"""
Contains a bookcard api: BookCardContainer.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

# pylint: disable=no-name-in-module
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional

import asynckivy
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
    MDDialogIcon,
    MDDialogSupportingText,
)
from kivymd.uix.divider import MDDivider
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemSupportingText
from kivymd.uix.menu import MDDropdownMenu

if TYPE_CHECKING:
    from ..bookmanager._typing import Book, StatusHint
    from .core import MainApp


class BookCard(MDCard):
    """Implements a material card."""

    bookid: str = StringProperty()
    image: str = StringProperty()
    title: str = StringProperty()
    author: str = StringProperty()
    progress: str = StringProperty()
    status: "StatusHint" = StringProperty()
    truly_disabled: bool = BooleanProperty()

    def trans_color(self, color: list[str], transparency: float = 0.4) -> str:
        """Adjust the color according to the transparency."""
        return color[:-1] + [transparency]

    def check_border(self) -> None:
        """
        Check whether the widget itself is out of border. If True,
        set disabled=True; otherwise, set disabled=False

        """
        if self._is_out_of_border():
            self.auto_disable()
        else:
            if self.theme_bg_color == "Primary":
                self.disabled = False
            else:
                self.md_bg_color = self.trans_color(
                    self.theme_cls.errorContainerColor
                    if self.status == "deleted"
                    else self.theme_cls.surfaceContainerLowColor
                )
                self.truly_disabled = False

    def auto_disable(self) -> None:
        """Disable the bookcard."""
        if self.theme_bg_color == "Primary":
            self.disabled = True
        else:
            self.md_bg_color = self.trans_color(self.md_bg_color, 0)
            self.truly_disabled = True

    def set_properties_widget(self) -> None:
        """Fired `on_release/on_press/on_enter/on_leave` events."""
        if not self.truly_disabled:
            super().set_properties_widget()

    def _is_out_of_border(self) -> bool:
        return (
            self.to_window(0, self.pos[1] + self.height)[1]
            > self.parent.parent.to_window(
                0, self.parent.parent.pos[1] + self.parent.parent.height
            )[1]
        )


class BookCardContainer:
    """Implements a bookcard container."""

    def __init__(self, app: "MainApp") -> None:
        self.app = app
        self.test_bookcard: BookCard | None = None
        self.current_sort_rule: list[str] = ["status", "uploadtime"]
        self.current_category: str = "home"

    async def set(self, books: dict[str, "Book"], duration: Optional[float] = None):
        """Set cards."""
        for bookid, book in books.items():
            metadata = book.get_metadata()
            if not metadata["is_ready"]:
                self.prepare_book(book)
            pagenow, pagemax = metadata["pagenow"], metadata["pagemax"]
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
                status=metadata["status"],
            )
            self.app.root.ids.grid.add_widget(widget)
            if duration is not None:
                await asynckivy.sleep(duration)

    def insert(self, book: "Book") -> BookCard:
        """Insert one single card."""
        metadata = book.get_metadata()
        pagenow, pagemax = metadata["pagenow"], metadata["pagemax"]
        match pagenow / pagemax:
            case 0.0:
                progress = "待阅读"
            case 1.0:
                progress = "已读完√"
            case _ as x:
                progress = f"阅读到 {x:.2%}"
        widget = BookCard(
            style="elevated",
            bookid=book.bookid,
            image=metadata["coverpath"],
            title=metadata["title"],
            author=metadata["author"],
            progress=progress,
            status=metadata["status"],
        )
        idx = self.app.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.app.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.app.root.ids.grid.add_widget(widget, idx)
        return widget

    def set_category(self, category: str) -> None:
        """Reset the cards according to the category."""
        self.remove()
        match category:
            case "home":
                booklist = self.app.bookmanager.findnot(status="deleted")
            case "deleted":
                booklist = self.app.bookmanager.find(status="deleted")
            case "pinned":
                booklist = self.app.bookmanager.find(status="pinned")
            case _:
                raise RuntimeError(f"undefined category: {category}")
        asynckivy.start(self.set(booklist.sort(*self.current_sort_rule).books, 0))
        self.current_category = category

    def color_setter(self, widget: Any) -> Callable[[Any, list[str]], None]:
        """Get a color setter for widget."""
        return lambda _, x: setattr(widget, "md_bg_color", self.app.trans_color(x))

    def setattr(self, name: str, value: Any) -> None:
        """Setattr."""
        for card in self.app.root.ids.grid.children:
            setattr(card, name, value)

    def truly_disable(self) -> None:
        """Disable the bookcards."""
        for card in self.app.root.ids.grid.children:
            card.truly_disabled = True

    def truly_enable(self) -> None:
        """Enable the bookcards."""
        for card in self.app.root.ids.grid.children:
            card.truly_disabled = False

    def check(self) -> None:
        """Check the bookcards."""
        for card in self.app.root.ids.grid.children:
            card.check_border()

    def prepare_book(self, book: "Book") -> None:
        """Extract and picklize the book."""
        Logger.info('Book: Extracting book "%s"', book.get_metadata()["filepath"])
        book.extract()
        Logger.info('Book: Pickling book "%s"', book.get_metadata()["filepath"])
        book.picklize()

    def remove(self) -> None:
        """Remove all the bookcards."""
        self.app.root.ids.grid.parent.scroll_y = 1
        for widget in list(self.app.root.ids.grid.children):
            self.app.root.ids.grid.remove_widget(widget)

    def open_cover_menu(self, button) -> None:
        """Open a menu on the book cover."""
        menu = MDDropdownMenu(
            caller=button,
            items=[],
            show_duration=0.1,
            hide_duration=0.1,
            hor_growth="right",
            ver_growth="up",
            radius=button.parent.parent.radius,
            shadow_radius=button.parent.parent.shadow_radius,
            width=dp(160),
        )
        is_pinned = button.parent.parent.status == "pinned"
        is_deleted = button.parent.parent.status == "deleted"
        menu_items = [
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "取消置顶" if is_pinned else ("恢复" if is_deleted else "置顶"),
                "leading_icon": (
                    "pin-off" if is_pinned else ("restore" if is_deleted else "pin")
                ),
                "height": dp(40),
                "on_release": (
                    partial(self.unpin, button, menu)
                    if is_pinned
                    else (
                        partial(self.restore, button, menu)
                        if is_deleted
                        else partial(self.pin, button, menu)
                    )
                ),
            },
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "书籍信息",
                "leading_icon": "information-outline",
                "height": dp(40),
                "on_release": partial(self.getinfo, button, menu),
            },
            {
                "viewclass": "CoverDeleteDropdownTextItem",
                "text": "永久删除" if is_deleted else "删除本书",
                "leading_icon": "delete-alert" if is_deleted else "delete",
                "leading_icon_color": self.app.theme_cls.errorColor,
                "text_color": self.app.theme_cls.errorColor,
                "height": dp(40),
                "on_release": partial(
                    self.show_alert_dialog if is_deleted else self.delete,
                    button,
                    menu,
                ),
            },
        ]

        menu.items.extend(menu_items)
        menu.on_enter = menu.on_leave
        self.app.open_menu(
            menu, button.parent.parent, relx=dp(12), show_duration_x=0.04
        )

    def pin(self, button, menu=None) -> None:
        """Pin the bookcard containing the button."""
        (book := self.app.bookmanager.books[button.parent.parent.bookid]).pin()

        button.parent.parent.status = "pinned"
        self.app.root.ids.grid.remove_widget(button.parent.parent)

        idx = self.app.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.app.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.app.root.ids.grid.add_widget(button.parent.parent, idx)
        if menu:
            menu.dismiss()

    def unpin(self, button, menu=None) -> None:
        """Unpin the bookcard containing the button."""
        (book := self.app.bookmanager.books[button.parent.parent.bookid]).restore()

        button.parent.parent.status = "normal"
        self.app.root.ids.grid.remove_widget(button.parent.parent)

        idx = self.app.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.app.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.app.root.ids.grid.add_widget(button.parent.parent, idx)
        if menu:
            menu.dismiss()

    def restore(self, button, menu=None) -> None:
        """Restore the bookcard containing the button."""
        self.app.bookmanager.books[button.parent.parent.bookid].restore()
        button.parent.parent.status = "normal"
        self.app.root.ids.grid.remove_widget(button.parent.parent)
        if menu:
            menu.dismiss()

    def getinfo(self, button, menu=None) -> None:
        """Pin the bookcard containing the button."""

    def delete(self, button, menu=None) -> None:
        """Delete the bookcard."""
        self.app.bookmanager.books[button.parent.parent.bookid].delete()
        self.app.root.ids.grid.remove_widget(button.parent.parent)
        if menu:
            menu.dismiss()

    def get_radius(
        self, nav: Optional[Literal["left", "right"]] = None
    ) -> tuple[list, list]:
        """Get the radius and the shadow-radius."""
        if self.test_bookcard is None:
            self.test_bookcard = BookCard(style="elevated")
        radius, shadow_radius = (
            self.test_bookcard.radius.copy(),
            self.test_bookcard.shadow_radius,
        )
        match nav:
            case "left":
                radius[0] = 0
                radius[3] = 0
            case "right":
                radius[1] = 0
                radius[2] = 0
        return radius, shadow_radius

    def show_alert_dialog(self, button, menu):
        """Show alert dialog on deleting a book."""
        dialog = MDDialog(
            # ----------------------------Icon-----------------------------
            MDDialogIcon(icon="delete-alert"),
            # -----------------------Headline text-------------------------
            MDDialogHeadlineText(
                text="永久删除此书？", font_style="NavText", role="large"
            ),
            # -----------------------Supporting text-----------------------
            MDDialogSupportingText(
                text="这将会移除该书的所有本地文件和缓存, 并且无法再次恢复, 建议您在此之前"
                "保留好书籍的备份:",
                font_style="NavText",
                role="small",
            ),
            # -----------------------Custom content------------------------
            MDDialogContentContainer(
                MDDivider(),
                MDListItem(
                    MDListItemLeadingIcon(
                        icon="book-open-variant-outline",
                    ),
                    MDListItemSupportingText(
                        text=button.parent.parent.title,
                        font_style="NavText",
                        role="small",
                    ),
                    theme_bg_color="Custom",
                    md_bg_color=self.app.theme_cls.transparentColor,
                ),
                MDDivider(),
                orientation="vertical",
            ),
            # ---------------------Button container------------------------
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="确认删除",
                        font_style="NavText",
                        role="small",
                        theme_text_color="Custom",
                        text_color=self.app.theme_cls.errorColor,
                    ),
                    style="text",
                    on_release=lambda _: (
                        dialog.dismiss(),
                        menu.dismiss(),
                        self.app.bookmanager.remove(button.parent.parent.bookid),
                        self.app.root.ids.grid.remove_widget(button.parent.parent),
                    ),
                ),
                MDButton(
                    MDButtonText(text="取消", font_style="NavText", role="small"),
                    style="text",
                    on_release=lambda _: (dialog.dismiss(), menu.dismiss()),
                ),
                spacing="8dp",
            ),
            # -------------------------------------------------------------
        )
        dialog.open()
