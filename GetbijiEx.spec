# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path


ROOT = Path(SPECPATH)
IS_MACOS = sys.platform == 'darwin'


a = Analysis(
    [str(ROOT / 'scripts' / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'scripts'), './scripts'),
        (str(ROOT / 'skill'), './skill'),
    ],
    hiddenimports=[
        'scripts.app_paths',
        'scripts.biji_export',
        'scripts.auto_token',
        'scripts.biji_cli',
        'scripts.skill_installer',
        'scripts.gui_app',
    ],
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
    [],
    exclude_binaries=True,
    name='GetbijiEx',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GetbijiEx',
)
if IS_MACOS:
    app = BUNDLE(
        coll,
        name='GetbijiEx.app',
        icon=None,
        bundle_identifier=None,
    )
