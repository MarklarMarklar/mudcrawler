# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['scripts/main.py'],
    pathex=['.', './scripts'],
    binaries=[],
    datas=[
        ('assets/', 'assets/'),
        ('config.py', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'pygame',
        'numpy',
        'pytmx',
        'cv2',
        'pillow',
        'pygame_menu',
        'pathfinding',
        'noise',
        'scripts.asset_manager',
        'scripts.boss_factory',
        'scripts.camera',
        'scripts.dark_lord',
        'scripts.enemy',
        'scripts.level',
        'scripts.particle',
        'scripts.pickups',
        'scripts.player',
        'scripts.sound_manager',
        'scripts.ui',
        'scripts.update_ui',
        'scripts.weapons',
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

for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
) 