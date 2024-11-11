"""
Contains a tool class for kivy font management: KivyFont.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from math import ceil
from pathlib import Path
from typing import TYPE_CHECKING

from kivy.core.text import LabelBase
from kivy.logger import Logger
from kivy.metrics import sp
from kivymd.font_definitions import theme_font_styles

from ..bookmanager import TextMaster

if TYPE_CHECKING:
    from kivymd.app import MDApp

SYS_FONT_MAPPING = {
    "msyh": "微软雅黑",
    "msyhbd": "微软雅黑-粗体",
    "msyhl": "微软雅黑-细体",
    "simhei": "黑体",
}


class KivyFont:
    """
    Find system fonts and add them to kivy.

    Parameters
    ----------
    sys_fontpath : Path
        System font path (must be a directory).

    """

    def __init__(self, sys_fontpath: Path, app: "MDApp") -> None:
        if not sys_fontpath.is_dir():
            raise NotADirectoryError(f"not a directory: {sys_fontpath}")

        self.fontpath = sys_fontpath
        self.app = app
        self.font_info: dict[str, tuple[Path, str]] = {}
        self.font_textmaster: dict[str, dict[str, TextMaster]] = {}
        self.__find_sys_font()
        self.__set_font_styles()

    def __find_sys_font(self):
        for stem, name in SYS_FONT_MAPPING.items():
            if p := self.findfont(stem):
                LabelBase.register(name=stem, fn_regular=p.as_posix())
                self.font_info[stem] = (p, name)
            else:
                Logger.info('Font: Font style not found: "%s"', stem)

    def __set_font_styles(self):
        self.font_styles = {
            "BookCover": {
                "large": {
                    "line-height": 1.28,
                    "font-name": "msyhbd",
                    "font-size": sp(21),
                },
                "medium": {
                    "line-height": 1.28,
                    "font-name": "msyh",
                    "font-size": sp(21),
                },
                "small": {
                    "line-height": 1.2,
                    "font-name": "msyh",
                    "font-size": sp(16),
                },
            },
            "Hint": {
                "large": {
                    "line-height": 1.28,
                    "font-name": "msyh",
                    "font-size": sp(15),
                },
                "medium": {
                    "line-height": 1.24,
                    "font-name": "msyh",
                    "font-size": sp(14),
                },
                "small": {
                    "line-height": 1.2,
                    "font-name": "msyh",
                    "font-size": sp(12),
                },
            },
            "NavText": {
                "large": {
                    "line-height": 1.28,
                    "font-name": "msyh",
                    "font-size": sp(20),
                },
                "medium": {
                    "line-height": 1.24,
                    "font-name": "msyh",
                    "font-size": sp(16),
                },
                "small": {
                    "line-height": 1.2,
                    "font-name": "msyh",
                    "font-size": sp(14),
                },
            },
        }
        for styl, prop in self.font_styles.items():
            theme_font_styles[styl] = prop

    def register(
        self, font_name: str, font_path: Path, font_style: str, font_size: float
    ) -> None:
        """Register a new font."""
        LabelBase.register(name=font_name, fn_regular=font_path.as_posix())
        font_properties = {
            "large": {
                "line-height": 1.28,
                "font-name": font_name,
                "font-size": sp(font_size),
            }
        }
        self.font_styles[font_style] = font_properties
        self.app.theme_cls.font_styles[font_style] = font_properties

    def findfont(self, font_name: str) -> Path | None:
        """
        Find the font under the system-font-path.

        Parameters
        ----------
        font_name : str
            Font name.

        Returns
        -------
        Path | None
            If the font exists, return a Path object; otherwise return
            None.

        """
        if (p := self.fontpath / f"{font_name}.ttc").exists() or (
            p := self.fontpath / f"{font_name}.ttf"
        ).exists():
            return p
        return None

    def getstyle(self, font: str | Path, size: float) -> tuple[str, str]:
        """
        Translate the 2-tuple (font, font-size) into font-style and
        role.

        Parameters
        ----------
        font : str | Path
            Font name or path.
        size : str
            Font size.

        Returns
        -------
        tuple[Path, float]
            2-tuple (font-style, role).

        """
        if isinstance(font, str):
            if not (path := self.findfont(font)):
                return "", ""
        else:
            font, path = font.stem, font
        font_style = f"{font}-{int(size)}"
        if font_style not in self.font_styles:
            self.register(font, path, font_style, size)
        return font_style, "large"

    def getpath(self, font_style: str, role: str) -> tuple[Path, float]:
        """
        Translate the 2-tuple (font-style, role) into font-path and
        font-size.

        Parameters
        ----------
        font_style : str
            Font style.
        role : str
            Font role.

        Returns
        -------
        tuple[Path, float]
            2-tuple (font-path, font-size).

        """
        prop = self.font_styles[font_style][role]
        return self.font_info[prop["font-name"]][0], prop["font-size"]

    def gettextmaster(self, font_style: str, role: str) -> TextMaster:
        """Get the textmaster of the font-style."""
        if font_style not in self.font_textmaster:
            self.font_textmaster[font_style] = {}
        if role not in self.font_textmaster[font_style]:
            path, size = self.getpath(font_style, role)
            if size % 1 > 0:
                Logger.info(
                    "TextMaster: Font size is ceiled: %s -> %s",
                    size,
                    ceil(size),
                )
            self.font_textmaster[font_style][role] = TextMaster(path, size)
        return self.font_textmaster[font_style][role]
