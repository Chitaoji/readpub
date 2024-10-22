"""
Contains the config parser: local_config.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from pathlib import Path

from kivy.config import Config

from ..bookmanager import get_datapath

__all__ = ["local_config"]


class LocalConfig:
    """
    Local config parser for kivy-app.

    Parameters
    ----------
    path : Path
        Config path.

    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.parser = Config

    def update(self, commands: list[list]) -> None:
        """
        Update config by commands.

        Parameters
        ----------
        commands : list[list]
            _description_.

        """
        self.parser.read(self.path.as_posix())
        done = [self._edit(*c) for c in commands]
        if any(done):
            self.parser.write()
            self.parser.read(self.path.as_posix())
        elif not Path(self.path).exists():
            self.parser.write()

    def clear(self) -> None:
        """Clear the local config."""
        if self.path.exists():
            self.path.unlink()

    def _edit(self, *args) -> bool:
        if self.parser.get(*args[:-1]) != args[-1]:
            self.parser.set(*args)
            return True
        return False


local_config = LocalConfig(get_datapath() / "kivyapp.ini")
local_config.update([["input", "mouse", "mouse,multitouch_on_demand"]])
