"""
Contains the config parser: local_config.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Self

from kivy.config import Config
from kivy.logger import Logger

from ..bookmanager import get_datapath

if TYPE_CHECKING:
    from kivy.config import ConfigParser

__all__ = ["kvconfig"]


class KivyConfig:
    """
    Config parser for kivy-app.

    Parameters
    ----------
    datapath : Path
        Data path.
    parser : Optional[ConfigParser], optional
        An instance of `kivy.config.ConfigParser`, by default None.

    """

    def __init__(self, datapath: Path, parser: Optional["ConfigParser"] = None) -> None:
        if parser is None:
            self.path = datapath / "kivyapp.kivy.ini"
            self.parser = Config
        elif parser:
            self.path = datapath
            self.parser = parser
        self.parser.read(self.path.as_posix())
        self.children: dict[str, Self] = {}

    def __getitem__(self, __key: object) -> Self:
        return self.children[__key.__class__.__name__]

    def get_inipath(self, obj: object) -> Path:
        """Get the `.ini` path for any object."""
        return self.path.parent / f"kivyapp.{self.get_inistem(obj)}.ini"

    def get_inistem(self, obj: object) -> str:
        """Get the stem for `.ini` file."""
        return obj.__class__.__name__.lower().removesuffix("app")

    def resgister(self, obj: object, parser: "ConfigParser") -> None:
        """Register a config parser of the user's own."""
        self.children[obj.__class__.__name__] = KivyConfig(
            self.get_inipath(obj), parser=parser
        )

    def set_defaults(self, commands: list[list]) -> None:
        """
        Set default values in the config by commands.

        Parameters
        ----------
        commands : list[list]
            User specified commands.

        """
        done = [self._setdefault(*c) for c in commands]
        if any(done) or not Path(self.path).exists():
            Logger.info('Config: Saving default values to "%s"', self.path)
            self.parser.write()

    def update(self, commands: list[list]) -> None:
        """
        Update config by commands.

        Parameters
        ----------
        commands : list[list]
            User specified commands.

        """
        done = [self._set(*c) for c in commands]
        if any(done) or not Path(self.path).exists():
            Logger.info('Config: Updating "%s"', self.path)
            self.parser.write()

    def update_and_read(self, commands: list[list]) -> None:
        """
        Update config by commands, and read the config file again.

        Parameters
        ----------
        commands : list[list]
            User specified commands.

        """
        done = [self._set(*c) for c in commands]
        if any(done):
            Logger.info('Config: Updating "%s" and reading it again', self.path)
            self.parser.write()
            self.parser.read(self.path.as_posix())
        elif not Path(self.path).exists():
            Logger.info('Config: Updating "%s"', self.path)
            self.parser.write()

    def get(self, section: str, option: str) -> str:
        """Get a config value."""
        return self.parser.get(section, option)

    def clear(self) -> None:
        """Clear the local config."""
        if self.path.exists():
            self.path.unlink()

    def _set(self, *args) -> bool:
        if self.parser.get(*args[:-1]) != args[-1]:
            self.parser.set(*args)
            return True
        return False

    def _setdefault(self, *args) -> bool:
        if self.parser.getdefault(args[0], args[1], "...") == "...":
            self.parser.adddefaultsection(args[0])
            self.parser.set(*args)
            return True
        return False


kvconfig = KivyConfig(get_datapath())
kvconfig.update_and_read(
    [
        ["input", "mouse", "mouse,multitouch_on_demand"],
        # ["graphics", "fullscreen", "auto"],
    ]
)
