"""
Contains a tool class for reading settings: Book, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReadingSetting:
    """Manages reading settings."""

    fontpath: Path = field(default_factory=lambda: Path("msyh"))
    fontsize: float = 21.0
    page_width: float = 800.0
    page_height: float = 1200.0
    line_height: float = 40.0
    para_gap: float = 40.0
