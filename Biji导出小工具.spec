# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scripts/main.py'],
    pathex=['/Users/macbook/Documents/getbiji_dy_export'],
    binaries=[],
    datas=[
        ('/Users/macbook/Documents/getbiji_dy_export/scripts', './scripts'),
        ('/Users/macbook/Documents/getbiji_dy_export/skill', './skill'),
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
    name='Biji导出小工具',
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
    name='Biji导出小工具',
)
app = BUNDLE(
    coll,
    name='Biji导出小工具.app',
    icon=None,
    bundle_identifier=None,
)
