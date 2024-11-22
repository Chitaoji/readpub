"""
The installer for readpub.

"""

import argparse
from pathlib import Path

from colorama import just_fix_windows_console
from PyInstaller.__main__ import run as pyinstall

just_fix_windows_console()


parser = argparse.ArgumentParser(
    prog="install.py", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("dir", nargs="?", help="output directory", default="ReadPub")


filepath = Path(__file__)

SPEC = f"""from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path

a = Analysis(
    ['{filepath.with_name("main.py").as_posix()}'],
    pathex=[],
    binaries=[],
    datas=[('{filepath.parent.as_posix()}/src/*.py', 'src'),
    ('{filepath.parent.as_posix()}/src/bookmanager/*.py', 'src/bookmanager'),
    ('{filepath.parent.as_posix()}/src/kivyapp/*.py', 'src/kivyapp'),
    ('{filepath.parent.as_posix()}/src/kivyapp/*.kv', 'src/kivyapp')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    exclude_binaries=True,
    name='ReadPub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ReadPub',
)

"""

if __name__ == "__main__":
    namespace = parser.parse_args()
    outdir = Path(namespace.dir)
    if not outdir.exists():
        outdir.mkdir()
    (specpath := outdir / "ReadPub.spec").write_text(SPEC)
    pyinstall(
        [
            specpath.as_posix(),
            "--distpath",
            specpath.with_name("dist").as_posix(),
            "--workpath",
            specpath.with_name("build").as_posix(),
            "--noconfirm",
        ]
    )
