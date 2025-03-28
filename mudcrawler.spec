# -*- mode: python ; coding: utf-8 -*-

import sys
from os.path import abspath, join, dirname

# Add the project root to the Python path
project_root = dirname(abspath('__file__'))
sys.path.insert(0, project_root)

block_cipher = None

a = Analysis(
    ['./scripts/main.py'],  # Path to main script
    pathex=[project_root],  # Include project root in the path
    binaries=[],
    datas=[
        ('assets', 'assets'),  # Include all assets
        ('config.py', '.'),    # Include config file
        ('scripts', 'scripts'),  # Include scripts as a package
    ],
    hiddenimports=[
        'pygame',
        'numpy',
        'pytmx',
        'cv2',  # For OpenCV functionality
        'scripts.ui',
        'scripts.enemy',
        'scripts.level',
        'scripts.player',
        'scripts.sound_manager',
        'scripts.particle',
        'scripts.asset_manager',
        'scripts.camera',
        'scripts.weapons',
        'scripts.pickups',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MudCrawler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True to see error messages during testing
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Uncomment and update this line after creating an .ico file
    # icon='assets/icons/game_icon.ico',
)

# For creating a single directory (optional)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='MudCrawler',
# ) 