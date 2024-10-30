"""
Contains a tool class for text wrapping: TextMaster.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Mapping

from PIL import ImageFont

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

    from ._typing import Chapter, Page, Paragraph, TextMeasureType, TitleLevel, para
__all__ = ["TextMaster", "view"]


@dataclass
class TextMesurePlain:
    """
    Provides tools for text measurement.

    Parameters
    ----------
    font : str | Path, optional
        Font name, or the path of the font file.
    size : float, optional
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


class TextMesureCached(TextMesurePlain):
    """Measures text with cache."""

    def __post_init__(self):
        self.len_cache: dict[str, float] = {}
        self.bbox_cache: dict[str, tuple[float, float, float, float]] = {}
        super().__post_init__()

    def getlength(self, text: str) -> float:
        if text in self.len_cache:
            return self.len_cache[text]
        self.len_cache[text] = (length := self.fonttype.getlength(text))
        return length

    def getbbox(self, text: str) -> tuple[float, float, float, float]:
        if text in self.bbox_cache:
            return self.bbox_cache[text]
        self.bbox_cache[text] = (bbox := self.fonttype.getbbox(text))
        return bbox


class TextMesureSameSized(TextMesurePlain):
    """Measures text assuming that they all have the same length."""

    def getlength(self, text: str) -> float:
        return self.size

    def getbbox(self, text: str) -> tuple[float, float, float, float]:
        return (0, 5, self.size, 4 + self.size)


@dataclass
class TextMaster:
    """
    Provides tools for text wrapping.

    Parameters
    ----------
    font : str | Path, optional
        Font name, or the path of the font file.
    size : float, optional
        Text size.
    measure_type : TextMeasureType, optional
        Specifies the measuring tool, by default "cached".

    """

    font: str | Path = "msyh"
    size: float = 21
    measure_type: "TextMeasureType" = "cached"

    def __post_init__(self):
        match self.measure_type:
            case "plain":
                self.measure = TextMesurePlain(font=self.font, size=self.size)
            case "cached":
                self.measure = TextMesureCached(font=self.font, size=self.size)
            case "same-sized":
                self.measure = TextMesureSameSized(font=self.font, size=self.size)

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
        len_ellip = self.measure.getlength(ellipsis)
        for char in text:
            len_textnow += self.measure.getlength(char)
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
            len_textnow += self.measure.getlength(char)
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
            if char in {"，", "、", "；", "：", "。", "？", "！", "”", "）", "》"}:
                char = line[-1] + char
                line = line[:-1]
            if (i := line[-1]) in {"“", "（", "《"}:
                char = i + char
                line = line[:-1]
            paragraph.append(line)
            itertext = chain(char, itertext)
            line, char = self.fill(itertext, width)
        return paragraph

    def divide_into_pages(
        self,
        para_iter: Iterator["str | FakeParagraph"],
        width: float,
        height: float,
        hline: float,
        para_gap: float,
    ) -> "Chapter":
        """
        Divide the iterator of paragraphs into pages according to the
        page-height and page-width. The original "\\n" in the text
        will not be respected.

        Parameters
        ----------
        para_iter : Iterator[str | FakeParagraph]
            Iterator of original paragraphs.
        height : float
            Maximum page-height in pixels.
        width : float
            Maximum page-width in pixels.
        line_height : float
            Line-height in pixels.
        para_gap : float
            Gap between paragraphs in pixels.

        Returns
        -------
        ### list[ -------- list[ -------- para[ ----- str]]]
        ### - ↑ ----------- ↑ ------------ ↑ --------- ↑
        ### chapter   ->   page  ->  paragraph  ->   line

        Raises
        ------
        ValueError
            Raised when line-height is larger than page-height.

        """
        if hline > height:
            raise ValueError(
                f"line-height is larger than page-height: {hline} > {height}"
            )
        chapter: list[list["para[str]"]] = [[]]
        height_remain = height
        for para in para_iter:
            if isinstance(para, FakeParagraph):
                if (r := height_remain - para.height) >= 0:
                    chapter[-1].append(para)
                    height_remain = r - para_gap
                else:
                    chapter.append([para])
                    height_remain = height - para.height - para_gap
            else:
                divided = self.divide_into_lines(para, width)
                while len(divided) > 0:
                    if height_remain < hline:
                        chapter.append([])
                        height_remain = height
                    else:
                        nline = min(height_remain // hline, len(divided))
                        chapter[-1].append(divided[:nline])
                        divided = divided[nline:]
                        height_remain -= nline * hline + para_gap
        return chapter

    @staticmethod
    def read_from_bs(
        bs: "BeautifulSoup",
        htitle: Mapping["TitleLevel", float],
        himage: float,
        srcpath: Path,
    ) -> Iterator["str | FakeParagraph"]:
        """
        Read from instance of `BeautifulSoup`. The return value
        can be directly passed to `.divide_into_pages()`.

        Parameters
        ----------
        bs : BeautifulSoup
            Instance of `BeautifulSoup`.
        htitle : Mapping[&quot;TitleLevel&quot;, float]
            Title-height in pixels.
        himage : float
            Image height in pixels.
        srcpath : Path
            Source path.

        Yields
        ------
        str | FakeParagraph
            Paragraphs.

        """
        for tag in bs.body.find_all():
            if (n := tag.name) in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                yield BookTitle(htitle[n], n, tag.text)
            elif n == "p":
                if not (t := tag.text):
                    if img := tag.img:
                        yield BookImage(himage, srcpath / img.attrs["src"])
                    else:
                        continue
                yield t


@dataclass
class FakeParagraph:
    """Pretends to be a paragraph of the book."""

    height: float


@dataclass
class BookTitle(FakeParagraph):
    """Title."""

    level: "TitleLevel"
    text: str


@dataclass
class BookImage(FakeParagraph):
    """Image in the book."""

    path: Path


@dataclass
class TextViewer:
    """Text viewer."""

    text: str

    def __repr__(self) -> str:
        return self.text


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
            return TextViewer(
                "\n\n".join(
                    "\n".join(para) if isinstance(para, list) else repr(para)
                    for para in content
                )
            )
        if len(content[0]) == 0:
            return TextViewer("")  # empty page indicates empty chapter
        if isinstance(content[0][0], str):
            return TextViewer(
                "\n\n".join(
                    "\n".join(para) if isinstance(para, list) else repr(para)
                    for para in content
                )
            )
        page_split = f"\n\n{"="*12} NextPage {"="*12}\n\n"
        return TextViewer(
            page_split.join(
                "\n\n".join(
                    "\n".join(para) if isinstance(para, list) else repr(para)
                    for para in page
                )
                for page in content
            )
        )
    return TextViewer(repr(content))
