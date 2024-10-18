"""
Contains the core of bookmanager: BookManager, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import secrets
import shutil
from pathlib import Path
from typing import Optional

from .book import Book

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
        Datapath is not a directory - please use `get_datapath()`
        to get a legal datapath.

    """

    def __init__(self, datapath: Path) -> None:
        if not datapath.is_dir():
            raise NotADirectoryError(f"not a directory: {datapath}")
        self.datapath = datapath
        self.opened_book = ""
        self.load_data()

    def load_data(self) -> None:
        """Load data."""
        books_path = self.datapath / "books"
        if not books_path.exists():
            books_path.mkdir()
        self.books = {p.name: Book(p, self) for p in books_path.iterdir()}

    def add_book(self, path: Path) -> None:
        """
        Add a book.

        Parameters
        ----------
        path : Path
            Path of the book.

        Raises
        ------
        FileNotFoundError
            Book is not found.

        """
        if not path.exists():
            raise FileNotFoundError(f"no such file: {path}")
        bookid = self.get_new_bookid()
        backup_path = self.datapath / "books" / bookid
        backup_path.mkdir()
        shutil.copyfile(path, backup_path / path.name)

        self.books[bookid] = Book(backup_path, self)

    def del_book(self, bookid: str) -> None:
        """
        Delete a book.

        NOTE: this will also delete the backup file of the book.

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
            Exceeded the max times of runs.

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


def get_datapath(datapath: Optional[Path] = None) -> tuple[Path, str]:
    """
    Get the path for data storage.

    Parameters
    ----------
    datapath : Optional[Path], optional
        A user specified path, by default None.

    Returns
    -------
    tuple[Path, str]
        A 2-tuple containing (datapath, error_message). If no error
        occured, error_message will be "".

    """
    datapath = datapath if datapath else Path("~/AppData/Local/ReadPub").expanduser()
    if not datapath.exists():
        try:
            datapath.mkdir(parents=True)
        except OSError:
            return datapath, "mkdir-failed"
    elif not datapath.is_dir():
        return datapath, "not-a-dir"
    return datapath, ""