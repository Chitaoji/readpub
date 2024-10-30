"""
Contains tools for book management: BookManager, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from . import book, core, textmaster
from .book import *
from .core import *
from .textmaster import *

__all__: list[str] = []
__all__.extend(core.__all__)
__all__.extend(book.__all__)
__all__.extend(textmaster.__all__)
