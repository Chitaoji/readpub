"""
Contains a dataclass: PageSettings.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:

    from ._typing import TitleLevel


@dataclass
class PageSettings:
    """Manages the book-page settings."""

    fontpath: str = "msyh"
    fontsize: float = 21.0
    page_width: float = 1000.0
    page_height: float = 900.0
    hline: float = 40.0
    himage: float = 1200.0
    htitle: Mapping["TitleLevel", float] = field(
        default_factory=lambda: {f"h{i}": 40.0 for i in range(1, 7)}
    )
    gap: float = 40.0
