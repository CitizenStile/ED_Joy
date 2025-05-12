# -*- mode: python ; coding: utf-8 -*-
# type: ignore
"""Spec for building OneFile version of distribution"""
import os
import sys

# PyInstaller, add an additional folder to parse spec from
sys.path.insert(0, os.path.dirname(SPEC))

import build as com

a = Analysis(
    com.entry,
    pathex=[],
    binaries=[],
    datas=com.additional_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,  # True for OneFolder, False for OneFile
    name=com.name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=com.icon,
)
