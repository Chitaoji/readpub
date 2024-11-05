"""
Contains the core of bookmanager: BookManager, get_datapath(), etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import secrets
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional, Self, Unpack

from .book import Book
from .textmaster import FontTable
from .viewer import BookViewer

if TYPE_CHECKING:
    from logging import Logger

    from ._typing import MetaData, MetaDataKey

__all__ = ["BookManager", "get_datapath"]


class BookManager:
    """
    Book manager.

    Parameters
    ----------
    datapath : Path
        The path for data storage.
    logger : Logger, optional
        Logger.

    Raises
    ------
    NotADirectoryError
        Raised when datapath is not a directory - use `get_datapath()`
        to get a legal path.

    """

    def __init__(self, datapath: Path, logger: Optional["Logger"] = None) -> None:
        if not datapath.is_dir():
            raise NotADirectoryError(f"not a directory: {datapath}")
        self.datapath = datapath
        self.logger = logger
        self.opened_book = ""
        self.username = "testuser"
        self.fonttable = FontTable()
        self.__init_books()

    def __getitem__(self, __key: int) -> Book:
        return list(self.books.values())[__key]

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

    def __init_books(self) -> None:
        """Load data."""
        books_path = self.datapath / "books"
        if not books_path.exists():
            books_path.mkdir()
        self.books = {p.name: Book(p, self) for p in books_path.iterdir()}

    def add_book(self, src: Path) -> Book:
        """
        Add a book.

        Parameters
        ----------
        src : Path
            Path of the book.

        Returns
        -------
        Book
            New book.

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

        self.books[bookid] = book = Book(dirpath, self)
        return book

    def check_book(self, src: Path) -> bool:
        """Check whether the source file is an e-book."""
        if src.suffix in {".epub"}:
            return True
        return False

    def del_book(self, bookid: str) -> Book:
        """
        Delete a book and return itself.

        NOTE: you can use `.recover_book()` to recover it.

        """
        book = self.books[bookid]
        book.update_metadata(status="deleted")
        book.save_metadata()
        return book

    def restore_book(self, bookid: str) -> Book:
        """Recover a book and return itself."""
        book = self.books[bookid]
        book.update_metadata(status="normal")
        book.save_metadata()
        return book

    def pin_book(self, bookid: str) -> Book:
        """Pin a book and return itself."""
        book = self.books[bookid]
        book.update_metadata(status="pinned")
        book.save_metadata()
        return book

    def del_book_entirely(self, bookid: str) -> None:
        """
        Delete a book entirely.

        NOTE: this will entirely delete all the files and records related
        to the book, so the book can not be recoverd again!!

        """
        shutil.rmtree(self.datapath / "books" / bookid, ignore_errors=True)
        del self.books[bookid]

    def view_book(self, n: int | str) -> BookViewer:
        """View the n-th book in the bookshelf (in console mode)."""
        if isinstance(n, int):
            book = self[n]
        else:
            book = self.books[n]
        if self.opened_book == book.bookid:
            return BookViewer(book)
        if self.opened_book:
            self.books[self.opened_book].close()
        book.get_metadata()
        book.typeset()
        book.open()
        return BookViewer(book)

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

    def find(self, **kwargs: Unpack["MetaData"]) -> "TempBookManager":
        """
        Find books with certain metadata equal to specific values.

        Parameters
        ----------
        **kwargs : **MetaData
            Specifies the metadata keys and values. Only the books
            that meet `book[key] = value` for all the `(key, value)
            in kwargs.items()` will be returned.

        Returns
        -------
        TempBookManager
            Contains the books found.

        """
        books: dict[str, Book] = {}
        for bookid, book in self.books.items():
            metadata = book.get_metadata()
            if all(metadata[k] == v for k, v in kwargs.items()):
                books[bookid] = book
        return TempBookManager(books)

    def findnot(self, **kwargs: Unpack["MetaData"]) -> "TempBookManager":
        """
        Find books with certain metadata not equal to specific
        values.

        Parameters
        ----------
        **kwargs : **MetaData
            Specifies the metadata keys and values. Only the books
            that meet `book[key] != value` for any of the `(key,
            value) in kwargs.items()` will be returned.

        Returns
        -------
        TempBookManager
            Contains the books found.

        """
        books: dict[str, Book] = {}
        for bookid, book in self.books.items():
            metadata = book.get_metadata()
            if any(metadata[k] != v for k, v in kwargs.items()):
                books[bookid] = book
        return TempBookManager(books)

    def sort(self, *args: "MetaDataKey", ascending: bool = False) -> "TempBookManager":
        """
        Return a new dict of books sorted by its metadata.

        Parameters
        ----------
        *arg : *MetaDataKey
            Specifies by which key(s) the books should be sorted.
        ascending : bool, optional
            If True, the first element will be the one with the
            smallest values; if False, it will be the one with the
            largest values. By default False.

        Returns
        -------
        TempBookManager
            Contains the sorted books.

        """
        ids = list(self.books)
        sortids = sorted(
            ids,
            key=lambda x: tuple(self.books[x].get_metadata()[a] for a in args),
            reverse=not ascending,
        )
        books = {bookid: self.books[bookid] for bookid in sortids}
        return TempBookManager(books)

    def where_to_insert(
        self,
        bookid: str,
        iditer: Iterator[str],
        *args: "MetaDataKey",
        ascending: bool = False,
    ) -> int:
        """
        Given a bookid and an iterator of bookids, find where to insert
        the bookid according to the sorting rules.

        Parameters
        ----------
        bookid : str
            Bookid to be inserted.
        iditer : Iterator[str]
            Iterator of bookids.
        *args : *MetaDataKey
            Sorting rules. Specifies by which metadata-key(s) the bookids
            should be sorted.
        ascending : bool, optional
            If True, the first element will be the one with the
            smallest values; if False, it will be the one with the
            largest values. By default False.

        Returns
        -------
        int
            Index to insert the new bookid.

        """
        cnt = 0
        to_cmp = tuple(self.books[bookid].get_metadata()[a] for a in args)
        if ascending:
            for b in iditer:
                if to_cmp < tuple(self.books[b].get_metadata()[a] for a in args):
                    return cnt
                cnt += 1
        else:
            for cnt, b in enumerate(iditer):
                if to_cmp > tuple(self.books[b].get_metadata()[a] for a in args):
                    return cnt
                cnt += 1
        return cnt + 1


class TempBookManager:
    """
    Works as a result of `Bookmanager.find()`, `.fondnot()`,
    `.sort()`, etc.

    Parameters
    ----------
    books : dict[str, Book]
        Dict of books.

    """

    def __init__(self, books: dict[str, Book]) -> None:
        self.books = books

    def find(self, **kwargs: Unpack["MetaData"]) -> Self:
        """See BookManager.find()."""
        return BookManager.find(self, **kwargs)

    def findnot(self, **kwargs: Unpack["MetaData"]) -> Self:
        """See BookManager.findnot()."""
        return BookManager.findnot(self, **kwargs)

    def sort(self, *args: "MetaDataKey", ascending: bool = False) -> Self:
        """See BookManager.sort()."""
        return BookManager.sort(self, *args, ascending=ascending)


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
