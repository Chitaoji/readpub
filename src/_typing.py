"""
Contains typing classes.

NOTE: this module is not intended to be imported at runtime.

"""

from typing import TYPE_CHECKING

import loggings

if TYPE_CHECKING:
    from .bookmanager._typing import (
        Book,
        Chapter,
        MetaData,
        MetaDataKey,
        Page,
        PageSettingsDict,
        Paragraph,
        RawParagraph,
        StatusHint,
        TextMeasureMethod,
        TitleLevel,
        para,
    )

loggings.warning("this module is not intended to be imported at runtime")
