"""
Contains a read logger: ReadLogger, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

from pathlib import Path
from time import localtime, perf_counter, strftime
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from ._typing import ReadTimeLog


class ReadLogger:
    """Records and logs the reading history."""

    def __init__(self, filename: str = "reading.log.yaml") -> None:
        self.filename = filename
        self.time = 0.0
        self.counter: "ReadTimeLog" = []

    def start(self) -> None:
        """Start logging."""
        self.time = perf_counter()

    def end(self) -> None:
        """End logging."""
        readtime = round(perf_counter() - self.time, 2)
        y, m, w, d, time = strftime("%Y-%m-%U-%d-%H:%M", localtime()).split("-")
        self.counter.append([int(y), int(m), int(w), int(d), time, readtime])

    def dump(self, dirpath: Path) -> None:
        """Dump the read-time in a log file."""
        if (yml_path := dirpath / self.filename).exists():
            log: "ReadTimeLog" = yaml.safe_load(yml_path.read_text())
        else:
            log: "ReadTimeLog" = []
        log.extend(self.counter)
        with open(yml_path, "w", encoding="utf-8") as stream:
            yaml.safe_dump(log, stream)
        self.counter.clear()

    def load(self, dirpath: Path) -> "ReadTimeLog":
        """Load from the file."""
        return yaml.safe_load((dirpath / self.filename).read_text())
