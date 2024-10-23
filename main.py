"""
The launcher for readpub.

If you want to launch the app directly, run:

```sh
python main.py
```

If you want to import from the module, use the main `readpub` namespace instead.

"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .src.kivyapp import KivyApp
else:
    from src.kivyapp import KivyApp


if __name__ == "__main__":
    KivyApp().run()
