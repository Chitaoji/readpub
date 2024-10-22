"""
The launcher for readpub.

If you want to launch the app directly, run:

```sh
python main.py
```

If you want to import from the module, use the main `readpub` namespace instead.

"""

import argparse
from typing import TYPE_CHECKING

parser = argparse.ArgumentParser(
    prog="readpub/main.py", description="Launch a readpub application."
)
subparsers = parser.add_subparsers(
    title="choose the gui frame (default: kivy)", dest="subcommand"
)
subparsers.add_parser("kivy", help="Kivy/KivyMD")

if __name__ == "__main__":
    args = parser.parse_args()
    match args.subcommand:
        case "kivy" | None:
            if TYPE_CHECKING:
                from .src.kivyapp import KivyApp
            else:
                from src.kivyapp import KivyApp

            KivyApp().run()
