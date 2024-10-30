"""
Contains a tool class for text measuring and wrapping: TextMaster.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from PIL import ImageFont

if TYPE_CHECKING:
    from ._typing import para

__all__ = ["TextMaster"]


@dataclass
class TextMaster:
    """
    Provides tools for text measuring and wrapping.

    Parameters
    ----------
    font : str | Path
        Font name, or the path of the font file.
    size : float
        Text size.

    """

    font: str | Path = "msyh"
    size: float = 21

    def __post_init__(self):
        self.fonttype = ImageFont.truetype(font=self.font, size=self.size)

    def getlength(self, text: str) -> float:
        """Get the text length (in pixels)."""
        return self.fonttype.getlength(text)

    def getbbox(self, text: str) -> tuple[float, float, float, float]:
        """Get the (left, top, right, bottom) bounding box."""
        return self.fonttype.getbbox(text)

    def shorten(self, text: str, length: float, ellipsis: str = "...") -> str:
        """
        Shorten the text if it is longer than length (in pixels).

        Parameters
        ----------
        text : str
            Text.
        length : float
            Specifies the maximum length of text (in pixels).
        ellipsis : str, optional
            Specifies the ending of the text if it is to be shortend, by
            default "...".

        Returns
        -------
        str
            Shortened text.

        """
        if not ellipsis:
            return self.fill(text, length)[0]
        len_textnow, text_with_ellipsis, textnow = 0, "", ""
        len_ellip = self.fonttype.getlength(ellipsis)
        for char in text:
            len_textnow += self.fonttype.getlength(char)
            if not text_with_ellipsis and (len_textnow + len_ellip > length):
                text_with_ellipsis = textnow + ellipsis
            if len_textnow > length:
                return text_with_ellipsis
            textnow += char
        return textnow

    def fill(self, text: Iterator[str], length: float) -> tuple[str, str]:
        """
        Similar to `.shorten(text, length, ellipsis="")`, but accepts
        an iterator of string.

        Parameters
        ----------
        text : Iterator[str]
            Iterator of text.
        length : float
            Specifies the maximum length of text (in pixels).

        Returns
        -------
        tuple[str, str]
            2-tuple (shortened-text, remaining-character).

        """
        len_textnow, textnow = 0, ""
        for char in text:
            len_textnow += self.fonttype.getlength(char)
            if len_textnow > length:
                return textnow, char
            textnow += char
        return textnow, ""

    def divide_into_lines(self, text: str, width: float) -> list[str]:
        """
        Divide the text into lines according to the page-width. The
        original "\\n" in the text will not be respected.

        Parameters
        ----------
        text : str | Iterator[str]
            Text.
        width : float
            Maximum page-width in pixels.

        Returns
        -------
        ### list[ ----------- str]
        ### - ↑ -------------- ↑
        ### paragraph   ->    line

        """
        itertext = iter(text)
        paragraph: list[str] = []
        line, char = self.fill(itertext, width)
        while line:
            paragraph.append(line)
            itertext = chain(char, itertext)
            line, char = self.fill(itertext, width)
        return paragraph

    def divide_into_pages(
        self,
        paraiter: Iterator["str | FakeParagraph"],
        width: float,
        height: float,
        line_height: float,
        para_gap: float,
    ) -> list[list["para[str]"]]:
        """
        Divide the iterator of paragraphs into pages according to the
        page-height and page-width. The original "\\n" in the text
        will not be respected.

        Parameters
        ----------
        paraiter : Iterator[str | FakeParagraph]
            Iterator of original paragraphs.
        height : float
            Maximum page-height in pixels.
        width : float
            Maximum page-width in pixels.

        Returns
        -------
        ### list[ -------- list[ -------- para[ ----- str]]]
        ### - ↑ ----------- ↑ ------------ ↑ --------- ↑
        ### chapter   ->   page  ->  paragraph  ->  line

        """
        chapter: list[list["para[str]"]] = []
        pagenow: list["para[str]"] = []
        height_remain = height
        for para in paraiter:
            if isinstance(para, FakeParagraph):
                if (r := height_remain - para.height) >= 0:
                    pagenow.append(para)
                    height_remain = r - para_gap
                else:
                    pagenow = [para]
                    chapter.append(pagenow)
                    height_remain = height - para.height - para_gap
            else:
                divided = self.divide_into_lines(para, width)


@dataclass
class FakeParagraph:
    """A fake string with specified length and width."""

    height: float
