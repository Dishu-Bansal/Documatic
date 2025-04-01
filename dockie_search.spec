# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('D:\\SPECIAL\\Documatic\\gcpKey.json', '.'), ('D:\\SPECIAL\\Documatic\\dockie', 'dockie'), ('D:\\SPECIAL\\Documatic\\dockie\\data', 'dockie\\data')]
binaries = [('D:\\SPECIAL\\Documatic\\libssl-3-x64.dll', '.'), ('D:\\SPECIAL\\Documatic\\libcrypto-3-x64.dll', '.')]
hiddenimports = ['_ssl', 'cryptography']
tmp_ret = collect_all('certifi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['new_ui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='dockie_search',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
