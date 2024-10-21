"""
Config file.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from typing import TYPE_CHECKING

from kivy.config import Config

if TYPE_CHECKING:
    from kivy.config import ConfigParser

__all__ = []


def edit_config(cfg: "ConfigParser", *args) -> bool:
    """
    Edit the config.

    Parameters
    ----------
    cfg : ConfigParser
        Config parser.

    Returns
    -------
    bool
        Whether the config has been changed.

    """
    if cfg.get(*args[:-1]) != args[-1]:
        cfg.set(*args)
        return True
    return False


Config.read("myapp.ini")
commands = [
    edit_config(Config, "input", "mouse", "mouse,multitouch_on_demand"),
    edit_config(Config, "graphics", "fullscreen", "auto"),
]
if any(commands):
    Config.write()
    Config.read("myapp.ini")
