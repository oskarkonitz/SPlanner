# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/Users/oskarkonitz/Documents/UG/Wstęp do Programowania/wdp-project/main.py'],
    pathex=[],
    binaries=[],
    datas=[('/Users/oskarkonitz/Documents/UG/Wstęp do Programowania/wdp-project/languages', 'languages')],
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
    [],
    exclude_binaries=True,
    name='Splanner',
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
    icon=['/Users/oskarkonitz/Documents/UG/Wstęp do Programowania/wdp-project/_dev_tools/assets/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Splanner',
)
app = BUNDLE(
    coll,
    name='Splanner.app',
    icon='/Users/oskarkonitz/Documents/UG/Wstęp do Programowania/wdp-project/_dev_tools/assets/icon.icns',
    bundle_identifier=None,
)
