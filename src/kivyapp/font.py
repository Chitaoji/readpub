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
        for stem, name in SYS_FONT_MAPPING.items():
            if (p := self.fontpath / f"{stem}.ttc").exists() or (
                p := self.fontpath / f"{stem}.ttf"
            ).exists():
                LabelBase.register(name=stem, fn_regular=p.as_posix())
                self.fonts[stem] = (p, name)

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
                    "font-size": sp(13),
                },
            },
            "BigHint": {
                "large": {
                    "line-height": 1.36,
                    "font-name": "msyh",
                    "font-size": sp(27),
                },
                "medium": {
                    "line-height": 1.32,
                    "font-name": "msyh",
                    "font-size": sp(24),
                },
                "small": {
                    "line-height": 1.30,
                    "font-name": "msyh",
                    "font-size": sp(21),
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
        for fontstyle, properties in self.font_styles.items():
            theme_font_styles[fontstyle] = properties

    def translate(self, fontstyle: str, role: str) -> tuple[Path, float]:
        """
        Translate the 2-tuple (fontstyle, role) into font-path and
        font-size.

        Parameters
        ----------
        fontstyle : str
            Font style.
        role : str
            Font role.

        Returns
        -------
        tuple[Path, float]
            2-tuple (fontpath, fontsize).

        """
        role_properties = self.font_styles[fontstyle][role]
        return self.fonts[role_properties["font-name"]][0], role_properties["font-size"]
