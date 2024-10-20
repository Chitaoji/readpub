"""
Contains the container for a book: Book, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import datetime
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from .core import BookManager


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
        self.__page_now = -1
        self.__filedict: dict[str, bytes] = {}

    def __repr__(self) -> str:
        metadata = self.get_metadata()
        title, author = metadata["title"], metadata["author"]
        return f"{self.__class__.__name__}({title=}, {author=})"

    def get_metadata(self) -> dict[str, str]:
        """Get the metadata from the book."""
        yml_path = self.dirpath / "metadata.yml"
        if yml_path.exists():
            return yaml.safe_load(yml_path.read_text())
        metadata = read_ebook(self.dirpath, only_metadata=True)
        metadata.update(
            {
                "uploader": self.manager.username,
                "uploadtime": str(datetime.datetime.now()),
                "status": "normal",
            }
        )
        with open(yml_path, "w+", encoding="utf-8") as stream:
            yaml.safe_dump(metadata, stream)
        return metadata

    def update_metadata(self, metadata: dict[str, str]) -> None:
        """
        Update the metadata.

        Parameters
        ----------
        metadata : dict[str, str]
            New metadata.

        """
        oldmeta = self.get_metadata()
        oldmeta.update(metadata)
        with open(self.dirpath / "metadata.yml", "w+", encoding="utf-8") as stream:
            yaml.safe_dump(metadata, stream)

    def del_metadata(self) -> None:
        """Delete the saved metadata."""
        yml_path = self.dirpath / "metadata.yml"
        if yml_path.is_file():
            yml_path.unlink()

    def load(self) -> None:
        """Load the whole book."""
        if self.__filedict:
            raise RuntimeError("book is already loaded")
        self.__filedict = read_ebook(self.dirpath)

    def release(self) -> None:
        """Unload the book and release memory."""
        self.__filedict.clear()

    def open(self) -> None:
        """Open the book."""
        if self.manager.opened_book:
            if self.__page_now == -1:
                raise RuntimeError(
                    f"can't open book {self.bookid!r} because another book is "
                    f"already opened: {self.manager.opened_book!r}"
                )
            raise RuntimeError(f"book is already opened: {self.bookid!r}")
        if not self.__filedict:
            raise RuntimeError("book is empty; run '.load()' first")
        self.manager.opened_book = self.bookid

    def close(self) -> None:
        """
        Close the book. Nothing can be read from the book after it
        is closed.

        """
        self.__page_now = -1

    def turn_to_page(self, n: int) -> str:
        """Turn to page n."""
        if self.__page_now == -1:
            raise RuntimeError("book is closed, run '.open()' first.")
        self.__page_now = n

    def next_page(self) -> str:
        """Turn to the next page"""
        return self.turn_to_page(self.__page_now + 1)

    def prev_page(self) -> str:
        """Turn to the previous page"""
        return self.turn_to_page(self.__page_now - 1)

    def divide_into_pages(self) -> None: ...

    @property
    def is_loaded(self) -> bool:
        """Indicates whether the book is already loaded."""
        return bool(self.__filedict)

    @property
    def is_opened(self) -> bool:
        """Indicates whether the book is already opened."""
        return self.__page_now > -1

    @property
    def filedict(self) -> dict[str, bytes]:
        """Dictionary of book files."""
        return self.__filedict


def read_ebook(path: Path, only_metadata: bool = False) -> dict[str, str]:
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
    dict[str, str]
        A dict of files or paths.

    Raises
    ------
    NotImplementedError
        Raised when the book format is unsupported.

    """
    if path.is_dir():
        for p in path.iterdir():
            if p.suffix in [".epub"]:
                path = p
                break
        else:
            raise NotImplementedError(f"unsupported book format: {path}")
    match path.suffix:
        case ".epub":
            return _read_epub_metadata(path) if only_metadata else _read_epub(path)


def _read_epub(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        if opf_href := _find_opf(z):  # opf format
            return _get_opf_items(z, opf_href)
        else:
            raise NotImplementedError(f"unsupported epub format: {path}")


def _read_epub_metadata(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as z:
        if opf_href := _find_opf(z):  # opf format
            author, cover_href = _get_opf_info(z, opf_href)
            cover_path = _save_cover(z, cover_href, path)
        else:
            raise NotImplementedError(f"unsupported epub format: {path}")
    return {
        "title": path.stem,
        "author": author,
        "filepath": path.as_posix(),
        "coverpath": cover_path.as_posix(),
    }


def _find_opf(z: zipfile.ZipFile) -> str:
    for n in z.namelist():
        if n.endswith(".opf"):
            return n
    return ""


def _get_opf_items(z: zipfile.ZipFile, opf_href: str) -> dict[str, bytes]:
    maindir = "".join(opf_href.rpartition("/")[:-1])
    bs = BeautifulSoup(z.read(opf_href), features="xml")
    idrefs = [i.attrs["idref"] for i in bs.spine.find_all("itemref")]
    manifest, namelist = bs.manifest, z.namelist()

    items: dict[str, bytes] = {}
    for i in idrefs:
        itemdir = _merge_dir(maindir, manifest.find(id=i).attrs["href"])
        items[i] = z.read(itemdir) if itemdir in namelist else b""

    return items


def _get_opf_info(z: zipfile.ZipFile, opf_href: str):
    maindir = "".join(opf_href.rpartition("/")[:-1])
    bs = BeautifulSoup(z.read(opf_href), features="xml")
    author = a if (a := bs.creator.text) else "Unknown"
    c = bs.find("meta", attrs={"name": "cover"}).attrs["content"]
    cover_href = _merge_dir(maindir, bs.find(id=c).attrs["href"])
    return author, cover_href


def _save_cover(z: zipfile.ZipFile, cover_href: str, path: Path) -> Path:
    cover = z.read(cover_href)
    for p in path.parent.iterdir():
        if p.stem == "cover":
            p.unlink()
    new_path = path.parent / cover_href.rpartition("/")[-1]
    new_path.write_bytes(cover)
    return new_path


def _merge_dir(fromdir: str, to: str) -> str:
    if to.startswith("../"):
        parentdir = Path(fromdir).parent.as_posix()
        return _merge_dir("" if parentdir == "." else parentdir, to[3:])
    return fromdir + to
