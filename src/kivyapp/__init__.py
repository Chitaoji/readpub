"""
Contains the kivy-app for readpub.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from . import core
from .core import *

__all__: list[str] = []
__all__.extend(core.__all__)
