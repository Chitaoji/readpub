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

if TYPE_CHECKING:
    from .kivyapp import KivyApp
else:
    from kivyapp import KivyApp

parser = argparse.ArgumentParser(description="works as the launcher for readpub.")
parser.add_argument(
    "-f",
    "--frame",
    help="choose the gui frame (default: %(default)s)",
    default="kivy",
    choices=["kivy"],
)


if __name__ == "__main__":
    args = parser.parse_args()
    match args.frame:
        case "kivy":
            KivyApp().run()
