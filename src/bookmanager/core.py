"""
Contains the core of bookmanager: BookManager, get_datapath(), etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import secrets
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Unpack

from .book import Book

if TYPE_CHECKING:
    from ._typing import MetaData

__all__ = ["BookManager", "get_datapath"]


class BookManager:
    """
    Book manager for readpub.

    Parameters
    ----------
    datapath : Path
        The path for data storage.

    Raises
    ------
    NotADirectoryError
        Raised when datapath is not a directory - use `get_datapath()`
        to get a legal path.

    """

    def __init__(self, datapath: Path) -> None:
        if not datapath.is_dir():
            raise NotADirectoryError(f"not a directory: {datapath}")
        self.datapath = datapath
        self.opened_book = ""
        self.username = "testuser"
        self.find_books()

    def login(self, username: str = "", password: str = "") -> None:
        """
        Login as a new user.

        Parameters
        ----------
        username : str, optional
            User name, by default "".
        password : str, optional
            User password, by default "".

        Raises
        ------
        LoginError
            Raised when failing to login.

        """
        if username == "":
            username = Path("~").expanduser().name
        else:
            raise LoginError(f"no such user: {username!r}")
        if password == "":
            self.username = username
        else:
            raise LoginError(f"wrong password for user: {username!r}")

    def find_books(self) -> None:
        """Load data."""
        books_path = self.datapath / "books"
        if not books_path.exists():
            books_path.mkdir()
        self.books = {p.name: Book(p, self) for p in books_path.iterdir()}

    def add_book(self, src: Path) -> dict[str, str]:
        """
        Add a book.

        Parameters
        ----------
        src : Path
            Path of the book.

        Returns
        -------
        dict[str, str]
            Book metadata.

        Raises
        ------
        FileNotFoundError
            Raised when book is not found.

        """
        if not src.exists():
            raise FileNotFoundError(f"no such file: {src}")
        bookid = self.get_new_bookid()
        dirpath = self.datapath / "books" / bookid
        dirpath.mkdir()
        shutil.copyfile(src, dirpath / src.name)

        self.books[bookid] = (book := Book(dirpath, self))
        return book.get_metadata()

    def del_book(self, bookid: str) -> None:
        """
        Delete a book.

        NOTE: you can use `.recover_book()` to recover it.

        Parameters
        ----------
        bookid : str
            Book id.

        """
        self.books[bookid].update_metadata(status="deleted")

    def recover_book(self, bookid: str) -> None:
        """
        Recover a book.

        Parameters
        ----------
        bookid : str
            Book id.

        """
        self.books[bookid].update_metadata(status="normal")

    def del_book_entirely(self, bookid: str) -> None:
        """
        Delete a book entirely.

        NOTE: this will entirely delete all the files and records related
        to the book, so the book can not be recoverd again!!

        Parameters
        ----------
        bookid : str
            Book id.

        """
        shutil.rmtree(self.datapath / "books" / bookid, ignore_errors=True)
        del self.books[bookid]

    def get_new_bookid(self, maxruns: int = 20) -> str:
        """
        Get a new bookid.

        Parameters
        ----------
        maxruns : int, optional
            Max times of runs, by default 20.

        Returns
        -------
        str
            A random text string in hexadecimal.

        Raises
        ------
        RuntimeError
            Raised when exceeding the max times of runs.

        """
        for _ in range(maxruns - maxruns // 2):
            bookid = secrets.token_hex(8)
            if bookid not in self.books:
                break
        else:
            # try 16-bytes
            for _ in range(maxruns // 2):
                bookid = secrets.token_hex(16)
                if bookid not in self.books:
                    break
            else:
                raise RuntimeError(f"can't find a legal book id after {maxruns} runs")
        return bookid

    def find(self, **kwargs: Unpack["MetaData"]) -> dict[str, Book]:
        """
        Find books with specified metadata.

        Parameters
        ----------
        **kwargs : **MetaData
            Specified metada.

        Returns
        -------
        dict[str,Book]
            Books found.

        """
        books: dict[str, Book] = {}
        for bookid, book in self.books.items():
            metadata = book.get_metadata()
            if all(metadata[k] == v for k, v in kwargs.items()):
                books[bookid] = book
        return books


def get_datapath(datapath: Optional[Path] = None) -> Path:
    """
    Get the path for storing data.

    Parameters
    ----------
    datapath : Optional[Path], optional
        A user specified path, by default None.

    Returns
    -------
    Path
        The data path.

    """
    datapath = datapath if datapath else Path("~/AppData/Local/ReadPub").expanduser()
    if not datapath.exists():
        datapath.mkdir(parents=True)
    elif not datapath.is_dir():
        raise NotADirectoryError(f"not a directory: {datapath}")
    return datapath


class LoginError(Exception):
    """Failed to log in."""
