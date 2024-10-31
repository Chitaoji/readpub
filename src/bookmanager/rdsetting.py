"""
Contains a tool class for reading settings: Book, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:

    from ._typing import TitleLevel


@dataclass
class ReadingSetting:
    """Manages reading settings."""

    fontpath: Path = field(default_factory=lambda: Path("msyh"))
    fontsize: float = 21.0
    page_width: float = 800.0
    page_height: float = 1200.0
    hline: float = 40.0
    himage: float = 1200.0
    htitle: Mapping["TitleLevel", float] = field(
        default_factory=lambda: {f"h{i}": 100 for i in range(1, 7)}
    )
    gap: float = 40.0
