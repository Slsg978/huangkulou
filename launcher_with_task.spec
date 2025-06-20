# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

a = Analysis(
    ['launcher_with_task.py'],
    pathex=[os.path.abspath('.')],  # 加项目根路径
    binaries=[],
    hiddenimports=[
        'sys',
        'subprocess',
        'time',
        'win32con',
        'ctypes',
        'win32gui',
        'win32api'
    ],
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='launcher_with_task',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True  # 改为 False 可隐藏控制台窗口
)
