# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scripts/gui_app.py'],
    pathex=['/Users/macbook/Downloads/getbiji_dy_export'],
    binaries=[],
    datas=[('/Users/macbook/Downloads/getbiji_dy_export/scripts', './scripts')],
    hiddenimports=['scripts.app_paths', 'scripts.biji_export', 'scripts.refresh_token_browser'],
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
    name='Biji导出小工具',
)
app = BUNDLE(
    coll,
    name='Biji导出小工具.app',
    icon=None,
    bundle_identifier=None,
)
