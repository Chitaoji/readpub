"""
Contains a tool class for text wrapping: TextMaster.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass, field
from itertools import chain
from math import ceil
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional

from PIL import ImageFont

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

    from ._typing import Chapter, TextMeasureMethod, TitleLevel, para

__all__ = ["TextMaster", "BookIndex"]


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


class TextMesureSameSized(TextMesurePlain):
    """Measures text assuming that they all have the same length."""

    def getlength(self, text: str) -> float:
        return self.size

    def getbbox(self, text: str) -> tuple[float, float, float, float]:
        return (0, 5, self.size, 4 + self.size)


class TextMesureCached(TextMesurePlain):
    """Measures text with cache."""

    def __post_init__(self):
        self.len_cache: dict[str, float] = {}
        self.bbox_cache: dict[str, tuple[float, float, float, float]] = {}
        super().__post_init__()

    def getlength(self, text: str) -> float:
        if text in self.len_cache:
            return self.len_cache[text]
        self.len_cache[text] = length = self.fonttype.getlength(text)
        return length

    def getbbox(self, text: str) -> tuple[float, float, float, float]:
        if text in self.bbox_cache:
            return self.bbox_cache[text]
        self.bbox_cache[text] = bbox = self.fonttype.getbbox(text)
        return bbox


class TextMesureMixed(TextMesureCached):
    """
    Measures text with mixed methods. This is not necessarily faster
    than `TextMesureCached`, but can save memory.

    """

    def getlength(self, text: str) -> float:
        if "一" <= text <= "鿿":  # U+4E00 ~ U+9FFF
            return self.size
        if text in self.len_cache:
            return self.len_cache[text]
        self.len_cache[text] = length = self.fonttype.getlength(text)
        return length


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
    method : TextMeasureMethod, optional
        Specifies the measure method, by default "cached".

    """

    font: str | Path = "msyh"
    size: float = 21
    method: "TextMeasureMethod" = "mixed"

    def __post_init__(self):
        match self.method:
            case "plain":
                self.measure = TextMesurePlain(font=self.font, size=self.size)
            case "same-sized":
                self.measure = TextMesureSameSized(font=self.font, size=self.size)
            case "cached":
                self.measure = TextMesureCached(font=self.font, size=self.size)
            case "mixed":
                self.measure = TextMesureMixed(font=self.font, size=self.size)

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
            if (i := line[-1]) in {"“", "（", "《"} and char:
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
        gap: float,
        startpage: int = 1,
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
        gap : float
            Gap between paragraphs in pixels.
        startpage : int, optional
            Starting page number, by default 1.

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
        npage, height_remain = startpage, height
        for para in para_iter:
            if isinstance(para, FakeParagraph):
                if (r := height_remain - para.height) >= 0:
                    chapter[-1].append(para)
                    height_remain = r - gap
                else:
                    npage += 1
                    chapter.append([para])
                    height_remain = height - para.height - gap
                para.npage = npage
            else:
                divided = self.divide_into_lines(para, width)
                while len(divided) > 0:
                    if height_remain < hline:
                        npage += 1
                        chapter.append([])
                        height_remain = height
                    else:
                        nline = min(int(height_remain // hline), len(divided))
                        chapter[-1].append(divided[:nline])
                        divided = divided[nline:]
                        height_remain -= nline * hline + gap
        if npage == startpage and height_remain == height:
            return [], startpage - 1
        return chapter, npage

    def page_rawcount(
        self,
        para_iter: Iterator["str | FakeParagraph"],
        width: float,
        height: float,
        hline: float,
        gap: float,
    ) -> int:
        """
        A simplified version of `divide_into_pages()` which only
        calculates the number of pages.

        Parameters
        ----------
        See `.divide_into_pages()`.

        Returns
        -------
        int
            Total number of pages.

        Raises
        ------
        ValueError
            Raised when line-height is larger than page-height.

        """
        if hline > height:
            raise ValueError(
                f"line-height is larger than page-height: {hline} > {height}"
            )
        npage, height_remain = 1, height
        for para in para_iter:
            if isinstance(para, FakeParagraph):
                if (r := height_remain - para.height) >= 0:
                    height_remain = r - gap
                else:
                    npage += 1
                    height_remain = height - para.height - gap
            else:
                ndivided = ceil(len(para) / (width / self.measure.size))
                while ndivided > 0:
                    if height_remain < hline:
                        npage += 1
                        height_remain = height
                    else:
                        nline = min(int(height_remain // hline), ndivided)
                        ndivided -= nline
                        height_remain -= nline * hline + gap
        return npage

    @staticmethod
    def read_from_bs(
        bs: "BeautifulSoup",
        srcpath: Path,
        idx: "BookIndex",
    ) -> Iterator["str | FakeParagraph"]:
        """
        Read from instance of `BeautifulSoup`. The return value
        can be directly passed to `.divide_into_pages()`.

        Parameters
        ----------
        bs : BeautifulSoup
            Instance of `BeautifulSoup`.
        srcpath : Path
            Source path.
        idx : BookIndex
            Book index.

        Yields
        ------
        str | FakeParagraph
            Paragraphs.

        """
        for tag in bs.body.find_all():
            if (n := tag.name) in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                yield BookTitle(tag.text, int(n[1]), idx)
            elif n == "p":
                if not (t := tag.text):
                    if img := tag.img:
                        yield BookImage(srcpath / img.attrs["src"])
                    else:
                        continue
                yield t


@dataclass
class FakeParagraph:
    """Pretends to be a paragraph of the book."""

    def plain_text(self) -> str:
        """Return plain text."""
        return ""


@dataclass
class BookIndex(FakeParagraph):
    """Book index."""

    title: Optional["BookTitle"] = None
    content: list["BookIndex"] = field(default_factory=list)
    npage: int = field(init=False, default=-1)
    height: float = field(init=False, default=0.0)

    def __repr__(self) -> str:
        string = repr(self.title)
        if self.content:
            string += "\n" + "\n".join(
                "- " + repr(x).replace("\n", "\n  ") for x in self.content
            )
        return string

    def plain_text(self) -> str:
        """Return plain text."""
        string = self.title.text
        if self.content:
            string += "\n" + "\n".join(
                f"- {x.plain_text().replace("\n", "\n  ")}, {x.title.npage}"
                for x in self.content
            )
        return string

    def pop(self, title: "BookTitle") -> None:
        """Pop a new (sub)title."""
        if self.title is None:
            self.title = title
        elif self.title.level == title.level:
            self.content = [BookIndex(self.title, self.content), BookIndex(title)]
            self.title = BookTitle("Unknown", title.level - 1)
        elif self.title.level > title.level:
            self.content = [
                BookIndex(
                    BookTitle("Unknown", title.level),
                    [BookIndex(self.title, self.content)],
                ),
                BookIndex(title),
            ]
            self.title = BookTitle("Unknown", title.level - 1)
        elif len(self.content) == 0:
            self.content.append(BookIndex(title))
        elif self.content[-1].title.level == title.level:
            self.content.append(BookIndex(title))
        elif self.content[-1].title.level < title.level:
            self.content[-1].pop(title)
        else:
            self.content = [
                BookIndex(BookTitle("Unknown", title.level), self.content),
                BookIndex(title),
            ]


@dataclass
class BookTitle(FakeParagraph):
    """Title."""

    text: str
    level: "TitleLevel"
    npage: int = field(init=False, default=-1)
    height: float = field(init=False, default=100.0)
    idx: Optional[BookIndex] = None

    def __post_init__(self) -> None:
        if self.idx:
            self.idx.pop(self)
            self.idx = None

    def plain_text(self) -> str:
        return f"{self.text}\n"


@dataclass
class BookImage(FakeParagraph):
    """Image in the book."""

    path: Path
    npage: int = field(init=False, default=-1)
    height: float = field(init=False, default=1200.0)

    def plain_text(self) -> str:
        return f"[image={self.path}]"
