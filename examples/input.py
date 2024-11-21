"""Input method."""

import ctypes
from ctypes import wintypes

from kivy.app import App
from kivy.core.text import LabelBase as kvLabelBase
from kivy.lang import Builder

# windows api preparing
# GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
# GlobalLock = ctypes.windll.kernel32.GlobalLock
GlobalFree = ctypes.windll.kernel32.GlobalFree
GlobalFree.argtypes = (wintypes.HGLOBAL,)
# GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
# GlobalSize = ctypes.windll.kernel32.GlobalSize
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


class CANDIDATELIST(ctypes.Structure):
    """Condidate list."""

    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwStyle", wintypes.DWORD),
        ("dwCount", wintypes.DWORD),
        ("dwSelection", wintypes.DWORD),
        ("dwPageStart", wintypes.DWORD),
        ("dwPageSize", wintypes.DWORD),
        ("dwOffset", ctypes.ARRAY(wintypes.DWORD, 10)),
    ]


kvLabelBase.register(name="msyh", fn_regular=r"C:\Windows\Fonts\msyh.ttc")


class InputMethod(App):
    """Example application."""

    def ime_press(self, *_):
        """Overrides `ime_press()`."""

        user32 = ctypes.WinDLL(name="user32")
        imm32 = ctypes.WinDLL(name="imm32")
        h_wnd = user32.GetForegroundWindow()
        h_imc = imm32.ImmGetContext(h_wnd)
        # imm32.ImmSetOpenStatus(h_imc, False)
        # mem = GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, 30)
        # pcontents = GlobalLock(mem)
        size = imm32.ImmGetCandidateListW(h_imc, 0, None, 0)

        buffer = ctypes.create_string_buffer(size)

        ptxt = ctypes.cast(buffer, ctypes.POINTER(CANDIDATELIST))
        imm32.ImmGetCandidateListW.argtypes = (
            wintypes.HGLOBAL,
            wintypes.DWORD,
            ctypes.POINTER(CANDIDATELIST),
            wintypes.DWORD,
        )
        imm32.ImmGetCandidateListW.restype = ctypes.c_size_t
        imm32.ImmGetCandidateListW(h_imc, 0, ptxt, size)

        a = [ptxt.contents.dwOffset[i] for i in range(ptxt.contents.dwPageSize + 1)]
        op = [
            str(ai + 1) + ":" + str(buffer[a[ai] : a[ai + 1]], encoding="utf-16")
            for ai in range(len(a) - 1)
        ]

        self.root.ids.outl.text = "\n".join(op)

        imm32.ImmReleaseContext(h_wnd, h_imc)

    def on_start(self):
        # 绑定输入键盘事件
        self.root.ids.ipt.bind(text=self.ime_press)

    def build(self):
        # 构建界面
        return Builder.load_string(
            """
BoxLayout:
    TextInput:
        text: ""
        id: ipt
        font_name: 'msyh'
    Label:
        text: "Hello Button!"
        id: outl
        font_name: 'msyh'
"""
        )


InputMethod().run()
