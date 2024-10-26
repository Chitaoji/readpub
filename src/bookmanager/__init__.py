"""
Contains a book manager.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from . import core, measure
from .core import *
from .measure import *

__all__: list[str] = []
__all__.extend(core.__all__)
__all__.extend(measure.__all__)
