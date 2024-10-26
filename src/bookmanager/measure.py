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
    Provides tools for text measuring.

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

    def divide_into_pages(
        self, text: str, height: float, width: float
    ) -> list[list[str]]:
        """
        Divide the text into pages according to the page-height and
        page-width. The original "\\n" in the text will be respected.

        Parameters
        ----------
        text : str
            Text.
        height : float
            Maximum page-height in digits.
        width : float
            Maximum page-width in digits.

        Returns
        -------
        list[str]
            List of divided lines.

        """
