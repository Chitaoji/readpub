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
    import secrets

    import asynckivy
    import kivymd.uix.list
    import yaml
    from bs4 import BeautifulSoup
    from kivy import animation, config, lang, logger, metrics, properties, utils
    from kivy.core import text, window
    from kivy.uix import boxlayout, widget
    from kivymd import app, font_definitions, icon_definitions
    from kivymd.uix import (
        button,
        card,
        dialog,
        divider,
        filemanager,
        label,
        menu,
        progressindicator,
        snackbar,
    )
    from PIL import Image, ImageFont

    from .src.kivyapp import MainApp
else:
    from src.kivyapp import MainApp


if __name__ == "__main__":
    MainApp().run()
