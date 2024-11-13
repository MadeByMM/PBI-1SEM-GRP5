# nexttech_calc.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['nexttech_calc.py'],
    pathex=['.'],
    binaries=[],
    datas=[('nexttech_calculator.db', '.'), ('nexttech_users.db', '.'), ('Nexttech logo.png', '.'), ('button login.png', '.'), ('next.ico', '.')],  # Include necessary files
    hiddenimports=['PIL', 'customtkinter'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='nexttech_calc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='next.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='nexttech_calc',
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='nexttech_calc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='next.ico',
    onefile=True  # Ensure the application is packaged into a single file
)