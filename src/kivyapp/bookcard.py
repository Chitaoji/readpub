"""
Contains a kivy app: BookCardContainer.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

# pylint: disable=no-name-in-module
from functools import partial
from typing import TYPE_CHECKING, Literal, Optional

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
    from ._typing import BasicApp
else:
    from kivymd.app import MDApp as BasicApp


class BookCard(MDCard):
    """Implements a material card."""

    bookid: str = StringProperty()
    image: str = StringProperty()
    title: str = StringProperty()
    author: str = StringProperty()
    progress: str = StringProperty()
    status: "StatusHint" = StringProperty()
    truly_disabled: bool = BooleanProperty()

    def check_border(self) -> None:
        """
        Check whether the widget itself is out of border. If True,
        set disabled=True; otherwise, set disabled=False

        """
        self.disabled = self._is_out_of_border()

    def _is_out_of_border(self) -> bool:
        return (
            self.to_window(0, self.pos[1] + self.height)[1]
            > self.parent.parent.to_window(
                0, self.parent.parent.pos[1] + self.parent.parent.height
            )[1]
        )

    def set_properties_widget(self) -> None:
        """Fired `on_release/on_press/on_enter/on_leave` events."""
        if not self.truly_disabled:
            super().set_properties_widget()


class BookCardContainer(BasicApp):
    """Implements a bookcard container."""

    def set_card(self, book: "Book") -> BookCard:
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
        idx = self.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.root.ids.grid.add_widget(widget, idx)
        return widget

    async def set_cards(
        self, books: dict[str, "Book"], duration: Optional[float] = None
    ):
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
            if metadata["status"] == "deleted":
                widget.theme_bg_color = "Custom"
                widget.md_bg_color = self.theme_cls.errorContainerColor
                self.theme_cls.bind(errorContainerColor=widget.setter("md_bg_color"))
            self.root.ids.grid.add_widget(widget)
            if duration is not None:
                await asynckivy.sleep(duration)

    def check_cards(self) -> None:
        for card in self.root.ids.grid.children:
            card.check_border()

    def truly_disable_cards(self) -> None:
        """Disable the bookcards."""
        for card in self.root.ids.grid.children:
            card.truly_disabled = True

    def truly_enable_cards(self) -> None:
        """Enable the bookcards."""
        for card in self.root.ids.grid.children:
            card.truly_disabled = False

    def prepare_book(self, book: "Book") -> None:
        Logger.info('Extract: Extracting book "%s"', book.get_metadata()["filepath"])
        book.extract()
        Logger.info('Picklize: Pickling book "%s"', book.get_metadata()["filepath"])
        book.picklize()

    def remove_cards(self) -> None:
        """Remove all the bookcards."""
        self.root.ids.grid.parent.scroll_y = 1
        for widget in list(self.root.ids.grid.children):
            self.root.ids.grid.remove_widget(widget)

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
                    partial(self.unpin_bookcard, button, menu)
                    if is_pinned
                    else (
                        partial(self.restore_bookcard, button, menu)
                        if is_deleted
                        else partial(self.pin_bookcard, button, menu)
                    )
                ),
            },
            {
                "viewclass": "CoverDropdownTextItem",
                "text": "书籍信息",
                "leading_icon": "information-outline",
                "height": dp(40),
                "on_release": partial(self.get_bookcard_info, button, menu),
            },
            {
                "viewclass": "CoverDeleteDropdownTextItem",
                "text": "永久删除" if is_deleted else "删除本书",
                "leading_icon": "delete-alert" if is_deleted else "delete",
                "leading_icon_color": self.theme_cls.errorColor,
                "text_color": self.theme_cls.errorColor,
                "height": dp(40),
                "on_release": partial(
                    self.show_alert_dialog if is_deleted else self.delete_bookcard,
                    button,
                    menu,
                ),
            },
        ]

        menu.items.extend(menu_items)
        menu.on_enter = menu.on_leave
        self.open_menu(menu, button.parent.parent, relx=dp(12), show_duration_x=0.04)

    def pin_bookcard(self, button, menu=None) -> None:
        """Pin the bookcard containing the button."""
        book = self.bookmanager.pin_book(button.parent.parent.bookid)

        button.parent.parent.status = "pinned"
        self.root.ids.grid.remove_widget(button.parent.parent)

        idx = self.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.root.ids.grid.add_widget(button.parent.parent, idx)
        if menu:
            menu.dismiss()

    def unpin_bookcard(self, button, menu=None) -> None:
        """Unpin the bookcard containing the button."""
        book = self.bookmanager.restore_book(button.parent.parent.bookid)

        button.parent.parent.status = "normal"
        self.root.ids.grid.remove_widget(button.parent.parent)

        idx = self.bookmanager.where_to_insert(
            book.bookid,
            (x.bookid for x in self.root.ids.grid.children),
            *self.current_sort_rule,
            ascending=True,
        )
        self.root.ids.grid.add_widget(button.parent.parent, idx)
        if menu:
            menu.dismiss()

    def restore_bookcard(self, button, menu=None) -> None:
        """Restore the bookcard containing the button."""
        self.bookmanager.restore_book(button.parent.parent.bookid)
        button.parent.parent.status = "normal"
        self.root.ids.grid.remove_widget(button.parent.parent)
        if menu:
            menu.dismiss()

    def get_bookcard_info(self, button, menu=None) -> None:
        """Pin the bookcard containing the button."""

    def delete_bookcard(self, button, menu=None) -> None:
        """Delete the bookcard."""
        self.bookmanager.del_book(button.parent.parent.bookid)
        self.root.ids.grid.remove_widget(button.parent.parent)
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
                    md_bg_color=self.theme_cls.transparentColor,
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
                        text_color=self.theme_cls.errorColor,
                    ),
                    style="text",
                    on_release=lambda _: (
                        dialog.dismiss(),
                        menu.dismiss(),
                        self.bookmanager.del_book_entirely(button.parent.parent.bookid),
                        self.root.ids.grid.remove_widget(button.parent.parent),
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
