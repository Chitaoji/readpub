"""
Contains a tool class for text measuring and wrapping: TextMaster.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont

__all__ = ["TextMaster"]


@dataclass
class TextMaster:
    """
    Provides tools for text measuring and wrapping.

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
        self.fonttype = ImageFont.truetype(font=self.font, size=self.size)

    def getlength(self, text: str) -> float:
        """Get the text length (in pixels)."""
        return self.fonttype.getlength(text)

    def getbbox(self, text: str) -> tuple[float, float, float, float]:
        """Get the (left, top, right, bottom) bounding box."""
        return self.fonttype.getbbox(text)

    def shorten(self, text: str, length: float, ellipsis: str = "...") -> str:
        """
        Shorten the text if it is longer than length (in pixels).

        Parameters
        ----------
        text : str
            Text.
        length : float
            Specifies the maximum length of text (in pixels).
        ellipsis : str, optional
            Specifies the ending of the text if it is to be shortend, by
            default "...".

        Returns
        -------
        str
            Shortened text.

        """
        pass

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
            Maximum page-height in pixels.
        width : float
            Maximum page-width in pixels.

        Returns
        -------
        list[str]
            List of divided lines.

        """
