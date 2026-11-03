# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir，窗口程序名 EvapCond。在项目根目录由 build_windows.bat 调用。"""

import os

from PyInstaller.utils.hooks import collect_all

root = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))
coolprop_datas, coolprop_binaries, coolprop_hidden = collect_all("CoolProp")
pyside_datas, pyside_binaries, pyside_hidden = collect_all("PySide6")

a = Analysis(
    [os.path.join(root, "evapcond", "__main__.py")],
    pathex=[root],
    binaries=coolprop_binaries + pyside_binaries,
    datas=coolprop_datas + pyside_datas,
    hiddenimports=coolprop_hidden + pyside_hidden + ["scipy", "numpy"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EvapCond",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="EvapCond",
)
