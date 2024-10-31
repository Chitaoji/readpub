"""
Contains the container for a book: Book, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import datetime
import io
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Unpack, overload
from zipfile import ZipFile

import yaml
from bs4 import BeautifulSoup
from PIL import Image

from .setting import ReadingSetting
from .textmaster import TextMaster

if TYPE_CHECKING:
    from ._typing import Chapter, MetaData
    from .core import BookManager

__all__ = []


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
        self.pagemax = 0
        self.textmaster = TextMaster("msyh", 21)
        self.rdsetting = ReadingSetting()
        self.__page_now = -1
        self.__content: dict[int, BeautifulSoup] = {}
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
            return self.__metadata
        metadata = read_ebook(self.dirpath, only_metadata=True)
        metadata["title"] = self.textmaster.shorten(metadata["title"], 600)
        metadata.update(
            {
                "uploader": self.manager.username,
                "uploadtime": str(datetime.datetime.now()),
                "extracted": False,
                "status": "normal",
                "progress": (0.0, 1.0, -1),
            }
        )
        with open(yml_path, "w+", encoding="utf-8") as stream:
            yaml.safe_dump(metadata, stream)
        self.__metadata = metadata
        return self.__metadata

    def save_metadata(self) -> None:
        """Save the metadata."""
        with open(self.dirpath / "metadata.yml", "w+", encoding="utf-8") as stream:
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

    def extract(self) -> None:
        """Extract the whole book."""
        if not self.get_metadata()["extracted"]:
            read_ebook(self.dirpath)
            self.update_metadata(extracted=True)
            self.save_metadata()

    def get_content(self, contentid: int) -> BeautifulSoup:
        """Get content from source."""
        if contentid not in self.__content:
            metadata = self.get_metadata()
            contentpath = self.dirpath / "source" / metadata["content"][contentid]
            self.__content[contentid] = content = BeautifulSoup(
                contentpath.read_bytes(), features="xml"
            )
            return content
        return self.__content[contentid]

    def typeset(self, contentid: int) -> "Chapter":
        """Typeset the content."""
        bs, st = self.get_content(contentid), self.rdsetting
        textmaster = TextMaster(st.fontpath, st.fontsize)
        it = textmaster.read_from_bs(bs, st.htitle, st.himage, self.dirpath / "source")
        return textmaster.divide_into_pages(
            it, st.page_width, st.page_height, st.hline, st.gap
        )

    def release(self) -> None:
        """Unload the book and release memory."""
        self.__content.clear()

    def open(self) -> None:
        """Open the book."""
        if self.manager.opened_book:
            if self.__page_now == -1:
                raise RuntimeError(
                    f"can't open book {self.bookid!r} because another book is "
                    f"already opened: {self.manager.opened_book!r}"
                )
            raise RuntimeError(f"book is already opened: {self.bookid!r}")
        self.manager.opened_book = self.bookid
        self.extract()

    def close(self) -> None:
        """
        Close the book. Nothing can be read from the book after it
        is closed.

        """
        self.__page_now = -1
        self.manager.opened_book = ""

    def turn_to_page(self, n: int) -> str:
        """Turn to page n."""
        if self.__page_now < 0:
            raise RuntimeError("book is closed, run '.open()' first.")
        self.__page_now = n

    def next_page(self) -> str:
        """Turn to the next page"""
        return self.turn_to_page(self.__page_now + 1)

    def prev_page(self) -> str:
        """Turn to the previous page"""
        return self.turn_to_page(self.__page_now - 1)

    @property
    def is_opened(self) -> bool:
        """Indicates whether the book is already opened."""
        return self.__page_now > -1

    @property
    def cache(self) -> dict[str, bytes]:
        """Dictionary of book files."""
        return self.__content


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
    return {
        "title": path.stem,
        "author": author,
        "filepath": path.as_posix(),
        "coverpath": cover_path.as_posix(),
        "content": content,
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
    cover_href = _merge_dir(maindir, bs.find(id=c).attrs["href"])

    manifest = bs.manifest
    idrefs = [i.attrs["idref"] for i in bs.spine.find_all("itemref")]
    content = [_merge_dir(maindir, manifest.find(id=i).attrs["href"]) for i in idrefs]
    return author, cover_href, content


def _save_cover(z: ZipFile, cover_href: str, path: Path) -> Path:
    cover = z.read(cover_href)
    for p in path.parent.iterdir():
        if p.stem == "cover":
            p.unlink()
    savepath = path.parent / cover_href.rpartition("/")[-1]
    with Image.open(io.BytesIO(cover)) as image:
        _image_auto_resize(image, 248, 360).save(savepath, optimize=True)
    return savepath


def _image_auto_resize(image: Image.Image, width: int, height: int) -> Image.Image:
    a, b = image.size
    if a / b > width / height:
        eps = int((a - b * width / height) / 2)
        box = (eps, 0, a - eps, b)
    else:
        eps = int((b - a * height / width) / 2)
        box = (0, eps, a, b - eps)
    image = image.resize((width, height), box=box, reducing_gap=1.1)
    return image


# def _cv2_auto_resize(cover: bytes, width: int, height: int) -> np.ndarray:
#     img_nuffer = np.frombuffer(cover, dtype=np.uint8)
#     mat = cv2.imdecode(img_nuffer, 1)

#     b, a, _ = mat.shape
#     if a / b > width / height:
#         eps = int((a - b * width / height) / 2)
#         mat = mat[0:b, eps : a - eps]
#     else:
#         eps = int((b - a * height / width) / 2)
#         mat = mat[eps : b - eps, 0:a]
#     return cv2.resize(mat, (width, height))


def _merge_dir(fromdir: str, to: str) -> str:
    if to.startswith("../"):
        parentdir = Path(fromdir).parent.as_posix()
        return _merge_dir("" if parentdir == "." else parentdir, to[3:])
    return fromdir + to


class EBookFormatError(NotImplementedError):
    """Raised when receiving unsupported e-book format."""
