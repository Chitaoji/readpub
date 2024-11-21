"""
Contains a read logger: ReadLogger, etc.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._typing import ReadTimeLog


class ReadLogger:
    """Records and logs the reading history."""

    def __init__(self, filename: str = "reading.log.json") -> None:
        self.filename = filename
        self.time = 0.0
        self.counter: "ReadTimeLog" = []

    def start(self) -> None:
        """Start logging."""
        self.time = perf_counter()

    def end(self) -> str:
        """End logging."""
        readtime = round(perf_counter() - self.time, 2)
        y, m, w, d, time = (
            datetime.now().strftime("%Y-%m-%U-%d-%H:%M:%S.%f")[:-4].split("-")
        )
        self.counter.append([int(y), int(m), int(w), int(d), time, readtime])
        return f"{y}-{m}-{d} {time}"

    def dump(self, dirpath: Path) -> None:
        """Dump the read-time in a log file."""
        if (jspath := dirpath / self.filename).exists():
            with jspath.open(encoding="utf-8") as stream:
                log: "ReadTimeLog" = json.load(stream)
        else:
            log: "ReadTimeLog" = []
        log.extend(self.counter)
        with jspath.open("w", encoding="utf-8") as stream:
            json.dump(log, stream)
        self.counter.clear()

    def load(self, dirpath: Path) -> "ReadTimeLog":
        """Load from the file."""
        with (dirpath / self.filename).open(encoding="utf-8") as stream:
            log = json.load(stream)
        return log
