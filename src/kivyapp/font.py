"""
Contains a tool class for kivy font management: KivyFont.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from pathlib import Path

from kivy.core.text import LabelBase
from kivy.metrics import sp
from kivymd.font_definitions import theme_font_styles

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

    def __init__(self, sys_fontpath: Path) -> None:
        if not sys_fontpath.is_dir():
            raise NotADirectoryError(f"not a directory: {sys_fontpath}")

        self.fontpath = sys_fontpath
        self.fonts: dict[str, tuple[Path, str]] = {}
        self.__find_sys_font()
        self.__set_font_styles()

    def __find_sys_font(self):
        for p in self.fontpath.iterdir():
            if (stem := p.stem) in SYS_FONT_MAPPING:
                LabelBase.register(name=stem, fn_regular=p.as_posix())
                self.fonts[stem] = (p, SYS_FONT_MAPPING[stem])

    def __set_font_styles(self):
        self.font_styles = {
            "BookCover": {
                "large": {
                    "line-height": 1.28,
                    "font-name": "msyhbd",
                    "font-size": sp(21),
                },
                "medium": {
                    "line-height": 1.24,
                    "font-name": "msyh",
                    "font-size": sp(18),
                },
                "small": {
                    "line-height": 1.2,
                    "font-name": "msyh",
                    "font-size": sp(16),
                },
            },
            "BookHint": {
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
                    "font-size": sp(13),
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
                    "font-size": sp(12),
                },
            },
        }
        for fontstyle, properties in self.font_styles.items():
            theme_font_styles[fontstyle] = properties
