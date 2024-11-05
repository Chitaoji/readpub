"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bookmanager._typing import (
        Book,
        Chapter,
        MetaData,
        MetaDataKey,
        Page,
        Paragraph,
        RawParagraph,
        ReadingSettingDict,
        StatusHint,
        TextMeasureMethod,
        TitleLevel,
        para,
    )

logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)
