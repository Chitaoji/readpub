"""
Contains an input method api: InputMethod.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import ctypes
from ctypes import wintypes
from typing import TYPE_CHECKING, Any

from kivy.metrics import dp
from kivymd.uix.menu import MDDropdownMenu

if TYPE_CHECKING:
    from .core import MainApp

__all__ = ["InputMethod"]

# windows api 准备
GlobalFree = ctypes.windll.kernel32.GlobalFree
GlobalFree.argtypes = (wintypes.HGLOBAL,)
GlobalLock = ctypes.windll.kernel32.GlobalLock
GlobalLock.argtypes = (wintypes.HGLOBAL,)
GlobalLock.restype = wintypes.LPVOID
GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
GlobalUnlock.argtypes = (wintypes.HGLOBAL,)
GlobalUnlock.restype = wintypes.BOOL
GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
GlobalAlloc.argtypes = (wintypes.UINT, ctypes.c_size_t)
GlobalAlloc.restype = wintypes.HGLOBAL
GlobalSize = ctypes.windll.kernel32.GlobalSize
GlobalSize.argtypes = (wintypes.HGLOBAL,)
GlobalSize.restype = ctypes.c_size_t
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040
GHND = 0x0042
DWOFFSET_MAX = 1000


class CandidateList(ctypes.Structure):
    """Condidate list."""

    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwStyle", wintypes.DWORD),
        ("dwCount", wintypes.DWORD),
        ("dwSelection", wintypes.DWORD),
        ("dwPageStart", wintypes.DWORD),
        ("dwPageSize", wintypes.DWORD),
        ("dwOffset", ctypes.ARRAY(wintypes.DWORD, 1 + DWOFFSET_MAX)),
    ]


class InputMethod:
    """Implements an input method."""

    def __init__(self, app: "MainApp") -> None:
        self.app = app
        self.textfields: dict[str, Any] = {}
        self.prev_input_menu: MDDropdownMenu | None = None

    def open(self, textfield: Any) -> None:
        """Open an input menu."""
        if textfield.name not in self.textfields:
            self.textfields[textfield.name] = textfield

        candidates = self.get_candidates()
        if not candidates:
            if self.prev_input_menu:
                self.prev_input_menu.dismiss()
                self.prev_input_menu = None
            self.app.cards.search_title(textfield.text)
            return

        menu_width = self.app.font.gettextmaster("NavText", "medium").getlinewidth(
            candidates
        ) + dp(8)
        if self.prev_input_menu is None:
            menu = MDDropdownMenu(
                caller=textfield,
                items=[
                    {
                        "viewclass": "MDLabel",
                        "text": candidates,
                        "font_style": "NavText",
                        "role": "medium",
                        "padding": dp(4),
                        "height": dp(30),
                        "adaptive_height": True,
                    }
                ],
                show_duration=0.0,
                hide_duration=0.0,
                hor_growth="right",
                ver_growth="up",
                radius=[dp(4), dp(4), dp(4), dp(4)],
                shadow_radius=[0, 0, 0, 0],
                width=menu_width,
                theme_shadow_softness="Custom",
                shadow_softness=12,
            )
            menu.on_enter = menu.on_leave = lambda: None
            menu.bind(on_dismiss=lambda _: setattr(self, "prev_input_menu", None))
            self.app.open_menu(
                menu, textfield, absx=textfield.cursor_pos[0], rely=-dp(14)
            )

            self.prev_input_menu = menu
        else:
            self.prev_input_menu.items = [
                {
                    "viewclass": "MDLabel",
                    "text": candidates,
                    "font_style": "NavText",
                    "role": "medium",
                    "padding": dp(4),
                    "height": dp(30),
                    "adaptive_height": True,
                }
            ]
            self.prev_input_menu.width = menu_width

    def get_candidates(self) -> str:
        """Get the candidates from the system input method."""

        user32 = ctypes.WinDLL(name="user32")
        imm32 = ctypes.WinDLL(name="imm32")
        h_wnd = user32.GetForegroundWindow()
        h_imc = imm32.ImmGetContext(h_wnd)
        size = imm32.ImmGetCandidateListW(h_imc, 0, None, 0)

        buffer = ctypes.create_string_buffer(size)

        ptxt = ctypes.cast(buffer, ctypes.POINTER(CandidateList))
        imm32.ImmGetCandidateListW.argtypes = (
            wintypes.HGLOBAL,
            wintypes.DWORD,
            ctypes.POINTER(CandidateList),
            wintypes.DWORD,
        )
        imm32.ImmGetCandidateListW.restype = ctypes.c_size_t
        imm32.ImmGetCandidateListW(h_imc, 0, ptxt, size)
        if (
            ptxt.contents.dwPageSize > 20
            or ptxt.contents.dwPageStart + ptxt.contents.dwPageSize > DWOFFSET_MAX
        ):
            return ""
        a = [
            ptxt.contents.dwOffset[i]
            for i in range(
                ptxt.contents.dwPageStart,
                ptxt.contents.dwPageStart + ptxt.contents.dwPageSize + 1,
            )
        ]
        op = [
            str(ai + 1) + ":" + str(buffer[a[ai] : a[ai + 1]], encoding="utf-16")
            for ai in range(len(a) - 1)
        ]

        imm32.ImmReleaseContext(h_wnd, h_imc)
        return " ".join(op).replace("\x00", "")

    def receive_backspace(self) -> None:
        """Receive a backspace."""
        if (
            "search_field" in self.textfields
            and not self.textfields["search_field"].text
        ):
            self.app.cards.reset()
        self.textfields.clear()
