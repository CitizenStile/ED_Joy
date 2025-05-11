# -*- mode: python ; coding: utf-8 -*-

additional_files = [
    ('assets', 'assets'),
    ('config', 'config'),
    ('pyproject.toml', '.'),
]

a = Analysis(  # noqa: F821 # type: ignore
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=additional_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)  # noqa: F821 # type: ignore

exe = EXE(  # noqa: F821 # type: ignore
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ed_joy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)
coll = COLLECT(  # noqa: F821 # type: ignore
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ed_joy',
)
