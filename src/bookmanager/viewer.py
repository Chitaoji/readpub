"""
Contains a simple book viewer: BookViewer.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._typing import Book, Chapter, Page, Paragraph

__all__ = ["BookViewer", "view"]


@dataclass
class TextViewer:
    """Text viewer."""

    text: str

    def __repr__(self) -> str:
        return self.text


@dataclass
class BookViewer:
    """A simple book viewer"""

    book: "Book"

    def turn_to_page(self, n: int) -> TextViewer:
        """Turn to page n."""
        return TextViewer(self.book.turn_to_page(n))

    def next_page(self) -> TextViewer:
        """Turn to the next page"""
        return TextViewer(self.book.next_page())

    def prev_page(self) -> TextViewer:
        """Turn to the previous page"""
        return TextViewer(self.book.prev_page())


def view(content: "Chapter | Page | Paragraph | str") -> TextViewer:
    """View a chapter."""
    if isinstance(content, str):
        return TextViewer(content)
    if isinstance(content, list):
        if len(content) == 0:
            return TextViewer("")
        if isinstance(content[0], str):
            return TextViewer("\n".join(content))
        if not isinstance(content[0], list):
            return __join_page(content)
        if len(content[0]) == 0:
            return TextViewer("")  # empty page indicates empty chapter
        if isinstance(content[0][0], str):
            return __join_page(content)
        return __join_chapter(content)
    return TextViewer(content.plain_text())


def __join_page(page: "Page") -> TextViewer:
    return TextViewer(
        "\n\n".join(
            "\n".join(para) if isinstance(para, list) else para.plain_text()
            for para in page
        )
    )


def __join_chapter(chapter: "Chapter") -> TextViewer:
    page_split = f"\n\n{"="*12} NextPage {"="*12}\n\n"
    return TextViewer(
        page_split.join(
            "\n\n".join(
                "\n".join(para) if isinstance(para, list) else para.plain_text()
                for para in page
            )
            for page in chapter
        )
    )
