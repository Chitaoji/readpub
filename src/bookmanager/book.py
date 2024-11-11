"""
Contains the container for a book: Book, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import datetime
import io
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Unpack, overload
from zipfile import ZipFile

import yaml
from bs4 import BeautifulSoup
from PIL import Image

from .setting import PageSettings
from .textmaster import BookIndex, TextMaster, merge_dir
from .viewer import BookViewer

if TYPE_CHECKING:
    from ._typing import Chapter, MetaData, Page, PageSettingsDict, Paragraph
    from .core import BookManager

__all__ = ["image_auto_resize"]


class Book:
    """
    Contains an e-book.

    Parameters
    ----------
    dirpath : Path
        Directory path of the book.

    """

    def __init__(self, dirpath: Path, manager: "BookManager") -> None:
        self.dirpath = dirpath
        self.bookid = dirpath.name
        self.manager = manager
        self.settings: PageSettings | None = None
        self.textmaster = TextMaster()
        self.pagenow, self.pagemax = -1, -1
        self.__content: list[list["Paragraph"]] | None = None
        self.__typeset: "Chapter" | None = None
        self.__metadata: MetaData | None = None

    def __repr__(self) -> str:
        metadata = self.get_metadata()
        title, author = metadata["title"], metadata["author"]
        return f"{self.__class__.__name__}({title=}, {author=})"

    def get_metadata(self) -> "MetaData":
        """Get the metadata from the book."""
        if self.__metadata is not None:
            return self.__metadata
        yml_path = self.dirpath / "metadata.yml"
        if yml_path.exists():
            self.__metadata = yaml.safe_load(yml_path.read_text())
            self.settings = PageSettings(**self.__metadata["settings"])
            return self.__metadata
        metadata = read_ebook(self.dirpath, only_metadata=True)
        metadata["title"] = self.textmaster.shorten(metadata["title"], 600)
        self.settings = PageSettings()
        metadata.update(
            {
                "uploader": self.manager.username,
                "uploadtime": str(datetime.datetime.now()),
                "status": "normal",
                "pagenow": 0,
                "pagemax": 1,
                "is_ready": False,
                "settings": asdict(self.settings),
            }
        )
        with open(yml_path, "w", encoding="utf-8") as stream:
            yaml.safe_dump(metadata, stream)
        self.__metadata = metadata
        return self.__metadata

    def save_metadata(self) -> None:
        """Save the metadata."""
        with open(self.dirpath / "metadata.yml", "w", encoding="utf-8") as stream:
            yaml.safe_dump(self.__metadata, stream)

    def update_metadata(self, **kwargs: Unpack["MetaData"]) -> None:
        """
        Update the metadata (but not save).

        Parameters
        ----------
        **kwargs : **MetaData
            New metadata.

        """
        self.__metadata |= kwargs

    def del_metadata(self) -> None:
        """Delete the saved metadata."""
        yml_path = self.dirpath / "metadata.yml"
        if yml_path.is_file():
            yml_path.unlink()

    def delete(self) -> None:
        """Delete."""
        self.update_metadata(status="deleted")
        self.save_metadata()

    def restore(self) -> None:
        """Restore."""
        self.update_metadata(status="normal")
        self.save_metadata()

    def pin(self) -> None:
        """Pin a book and return itself."""
        self.update_metadata(status="pinned")
        self.save_metadata()

    def view(self) -> BookViewer:
        """View the n-th book in the bookshelf (in console mode)."""
        if (openid := self.manager.opened_book) == self.bookid:
            return BookViewer(self)
        if openid:
            self.manager.books[openid].close()
        self.get_metadata()
        self.typeset()
        self.open()
        return BookViewer(self)

    def extract(self) -> None:
        """
        Extract the whole book. This must be done before `.picklize()`,
        but we will not ensure it.

        """
        if not (self.dirpath / "source").exists():
            read_ebook(self.dirpath)

    def picklize(self) -> None:
        """
        Picklize the whole book. This must be done before `.open()`,
        but we will not ensure it.

        """
        if (pk := self.dirpath / ".pickle").exists():
            return
        srcpath = self.dirpath / "source"
        idx = BookIndex()
        to_pickle = [[idx]]
        for ref in yaml.safe_load((self.dirpath / "content.yml").read_text()):
            fromdir = "".join(ref.rpartition("/")[:-1])
            bs = BeautifulSoup((srcpath / ref).read_bytes(), features="xml")
            if paras := TextMaster.read_from_bs(
                bs, srcpath, fromdir, idx, self.manager.fonttable
            ):
                to_pickle.append(paras)
        with pk.open("wb") as f:
            pickle.dump(to_pickle, f)
        self.update_metadata(is_ready=True)
        self.save_metadata()

    def get_content(self) -> list[list["Paragraph"]]:
        """Get content from source."""
        if self.__content is None:
            with (self.dirpath / ".pickle").open("rb") as f:
                self.__content = pickle.load(f)
        return self.__content

    def typeset(self) -> "Chapter":
        """Typeset the content."""
        if self.__typeset is None:
            _typeset: list["Chapter"] = []
            st, npage = self.settings, 0
            for contentid in range(1, len(self.get_content())):
                chapter, npage = self.textmaster.divide_into_pages(
                    self.get_content()[contentid],
                    st.page_width,
                    st.page_height,
                    st.hline,
                    st.gap,
                    startpage=npage + 1,
                )
                _typeset.append(chapter)
            self.__typeset = sum(_typeset, [])
            self.update_metadata(
                pagemax=len(self.__typeset), settings=asdict(self.settings)
            )
            if self.manager.logger:
                self.manager.logger.info(
                    'Book: Typsetting book <"%s">', self.get_metadata()["title"]
                )
        return self.__typeset

    def adjust(self, **kwargs: Unpack["PageSettingsDict"]) -> None:
        """Adjust settings."""
        adjusted = False
        for k, v in kwargs.items():
            if getattr(self.settings, k) != v:
                setattr(self.settings, k, v)
                adjusted = True
        if adjusted:
            if self.manager.logger:
                self.manager.logger.info(
                    'Book: Ajusting settings for book <"%s">: %s',
                    self.get_metadata()["title"],
                    repr(kwargs),
                )
            self.__typeset = None

    def page_rawcount(self) -> int:
        """Count the pages."""
        n = 0
        for content in self.get_content()[1:]:
            st = self.settings
            n += self.textmaster.page_rawcount(
                content, st.page_width, st.page_height, st.hline, st.gap
            )
        return n

    def release(self) -> None:
        """Unload the book and release memory."""
        self.__content = None

    def open(self) -> None:
        """Open the book."""
        if self.manager.opened_book:
            if self.pagenow == -1:
                raise RuntimeError(
                    f"can't open book {self.bookid!r} because another book is "
                    f"already opened: {self.manager.opened_book!r}"
                )
            raise RuntimeError(f"book is already opened: {self.bookid!r}")
        self.manager.opened_book = self.bookid
        self.pagenow = self.get_metadata()["pagenow"]
        self.pagemax = self.get_metadata()["pagemax"]

    def close(self) -> None:
        """
        Close the book. Nothing can be read from the book after it
        is closed.

        """
        self.save_metadata()
        self.pagenow = -1
        self.manager.opened_book = ""

    def turn_to_page(self, n: int) -> "Page":
        """Turn to page n."""
        if self.pagenow < 0:
            raise RuntimeError("book is closed, run '.open()' first.")
        self.pagenow = n
        self.update_metadata(pagenow=n)
        return self.typeset()[n - 1]

    def next_page(self) -> "Page":
        """Turn to the next page"""
        return self.turn_to_page(self.pagenow + 1)

    def prev_page(self) -> "Page":
        """Turn to the previous page"""
        return self.turn_to_page(self.pagenow - 1)

    @property
    def is_opened(self) -> bool:
        """Indicates whether the book is already opened."""
        return self.pagenow > -1

    @property
    def cache(self) -> list[list["Paragraph"]]:
        """Book files."""
        return self.__typeset


@overload
def read_ebook(path: Path, only_metadata: Literal[True] = True) -> "MetaData": ...
@overload
def read_ebook(path: Path, only_metadata: Literal[False] = False) -> None: ...
def read_ebook(path: Path, only_metadata: bool = False) -> "MetaData | None":
    """
    Read an e-book from the path.

    Parameters
    ----------
    path : Path
        File path or directory path.
    only_metadata : bool, optional
        If true, only returns the metadata of the book, by default
        False.

    Returns
    -------
    MetaData | None
        MetaData or None.

    Raises
    ------
    EBookSupportError
        Raised when the e-book format is unsupported.

    """
    if path.is_dir():
        for p in path.iterdir():
            if p.suffix in [".epub"]:
                path = p
                break
        else:
            raise EBookFormatError(f"unsupported e-book format: {path}")

    match path.suffix:
        case ".epub":
            return _read_epub_metadata(path) if only_metadata else _read_epub(path)


def _read_epub(path: Path) -> None:
    if not (srcpath := path.parent / "source").exists():
        with ZipFile(path) as z:
            z.extractall(srcpath)


def _read_epub_metadata(path: Path) -> "MetaData":
    with ZipFile(path) as z:
        if opf_href := _find_opf(z):  # opf format
            author, cover_href, content = _get_opf_info(z, opf_href)
            cover_path = _save_cover(z, cover_href, path)
        else:
            raise EBookFormatError(f"unsupported epub format: {path}")
    with open(path.parent / "content.yml", "w", encoding="utf-8") as stream:
        yaml.safe_dump(content, stream)
    return {
        "title": path.stem,
        "author": author,
        "filepath": path.as_posix(),
        "coverpath": cover_path.as_posix(),
    }


def _find_opf(z: ZipFile) -> str:
    for n in z.namelist():
        if n.endswith(".opf"):
            return n
    return ""


def _get_opf_info(z: ZipFile, opf_href: str) -> tuple[str, str, list[str]]:
    maindir = "".join(opf_href.rpartition("/")[:-1])
    bs = BeautifulSoup(z.read(opf_href), features="xml")
    author = a if (a := bs.creator.text) else "Unknown"
    c = bs.find("meta", attrs={"name": "cover"}).attrs["content"]
    cover_href = merge_dir(maindir, bs.find(id=c).attrs["href"])

    manifest = bs.manifest
    idrefs = [i.attrs["idref"] for i in bs.spine.find_all("itemref")]
    content = [merge_dir(maindir, manifest.find(id=i).attrs["href"]) for i in idrefs]
    return author, cover_href, content


def _save_cover(z: ZipFile, cover_href: str, path: Path) -> Path:
    cover = z.read(cover_href)
    for p in path.parent.iterdir():
        if p.stem == "cover":
            p.unlink()
    savepath = path.parent / cover_href.rpartition("/")[-1]
    with Image.open(io.BytesIO(cover)) as image:
        image_auto_resize(image, 248, 360).save(savepath, optimize=True)
    return savepath


def image_auto_resize(image: Image.Image, width: int, height: int) -> Image.Image:
    """Reisze the image according to the width and height."""
    a, b = image.size
    if a / b > width / height:
        eps = int((a - b * width / height) / 2)
        box = (eps, 0, a - eps, b)
    else:
        eps = int((b - a * height / width) / 2)
        box = (0, eps, a, b - eps)
    image = image.resize((width, height), box=box, reducing_gap=1.1)
    return image


class EBookFormatError(NotImplementedError):
    """Raised when receiving unsupported e-book format."""
