"""
Contains tools for text measuring and wrapping: TextMeasure, TextMaster, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont

__all__ = ["TextMeasure", "TextMaster"]


@dataclass
class TextMeasure:
    """
    Text measure tools.

    Parameters
    ----------
    font : str | Path
        Font name, or the path of the font file.
    size : float
        Text size.

    """

    font: Path
    size: float

    def __post_init__(self):
        self.typefont = ImageFont.truetype(font=self.font, size=21)

    def getlength(self, text: str) -> float:
        """Get text length."""
        return self.typefont.getlength(text)

    def getbbox(self, text: str) -> tuple[float, float, float, float]:
        """Get (left, top, right, bottom) bounding box."""
        return self.typefont.getbbox(text)


@dataclass
class TextMaster:
    """
    Divide and wrap text.

    Parameters
    ----------
    font : str | Path
        Font name, or the path of the font file.
    size : float
        Text size.

    """

    measure: TextMeasure
