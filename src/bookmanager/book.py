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
    path : Path
        File path.

    """

    def __init__(self, path: Path, manager: "BookManager") -> None:
        self.path = path
        self.manager = manager
        self.__page_now = -1
        self.__filedict: dict[str, bytes] = {}

    def load(self) -> None:
        """Load the whole book."""
        if self.__filedict:
            raise RuntimeError("book is already loaded")
        self.__filedict = read_ebook(self.path)

    def release(self) -> None:
        """Release memory."""
        self.__filedict.clear()

    def divide_pages(self) -> None: ...

    def open(self) -> None:
        """Open the book."""
        if self.manager.opened_book:
            if self.__page_now == -1:
                raise RuntimeError(
                    f"can't open book {self.path.name!r} because another book is "
                    f"already opened: {self.manager.opened_book!r}"
                )
            raise RuntimeError(f"book is already opened: {self.path.name!r}")
        if not self.__filedict:
            raise RuntimeError("book is empty; run '.load()' first")
        self.manager.opened_book = self.path.name

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


def read_ebook(path: Path) -> dict[str, bytes]:
    """
    Read an e-book according to the path.

    Parameters
    ----------
    path : Path
        File path or directory path.

    Returns
    -------
    dict[str, bytes]
        A dict of files.

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
            with zipfile.ZipFile(path) as z:
                filedict = {f.filename: z.read(f) for f in z.filelist}
        case _ as x:
            raise NotImplementedError(f"can't read a {x!r} file: {path}")
    return filedict
