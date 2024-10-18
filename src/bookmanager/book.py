"""
Contains the container for a book: Book, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

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
        self.manager = manager
        self.__page_now = -1
        self.__filedict: dict[str, bytes] = {}

    def load(self) -> None:
        """Load the whole book."""
        if self.__filedict:
            raise RuntimeError("book is already loaded")
        self.__filedict = read_ebook(self.dirpath)

    def get_metadata(self) -> None:
        """Get the metadata from the book."""
        return read_ebook(self.dirpath, only_metadata=True)

    def release(self) -> None:
        """Release memory."""
        self.__filedict.clear()

    def divide_pages(self) -> None: ...

    def open(self) -> None:
        """Open the book."""
        if self.manager.opened_book:
            if self.__page_now == -1:
                raise RuntimeError(
                    f"can't open book {self.dirpath.name!r} because another book is "
                    f"already opened: {self.manager.opened_book!r}"
                )
            raise RuntimeError(f"book is already opened: {self.dirpath.name!r}")
        if not self.__filedict:
            raise RuntimeError("book is empty; run '.load()' first")
        self.manager.opened_book = self.dirpath.name

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

    @property
    def is_loaded(self) -> bool:
        """Indicates whether the book is already loaded."""
        return bool(self.__filedict)


def read_ebook(path: Path, only_metadata: bool = False) -> dict:
    """
    Read an e-book according to the path.

    Parameters
    ----------
    path : Path
        File path or directory path.
    only_metadata : bool, optional
        If true, only returns the metadata of the book, by default
        False.

    Returns
    -------
    dict
        A dict of files or metadata.

    Raises
    ------
    NotImplementedError
        Raised when the file suffix is illegal.

    """
    if path.is_dir():
        for p in path.iterdir():
            if p.suffix in [".epub"]:
                path = p
                break
        else:
            raise FileNotFoundError(f"can't find a book from the directory: {path}")
    match path.suffix:
        case ".epub":
            return _read_epub_metadata(path) if only_metadata else _read_epub(path)
        case _ as x:
            raise NotImplementedError(f"can't read a {x!r} file: {path}")


def _read_epub(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as z:
        filedict = {f.filename: z.read(f) for f in z.filelist}
    return filedict


def _read_epub_metadata(path: Path) -> dict[str, str | Path]:
    with zipfile.ZipFile(path) as z:
        namelist = z.namelist()
        if (name := "content.opf") in namelist:
            content = z.read(name)
        else:
            raise NotImplementedError(f"unsupported epub format: {path}")
    return content


def _find_cover_from_outside(path: Path) -> Path | None:
    for p in path.parent.iterdir():
        if p.stem == "cover":
            return p
    return None
