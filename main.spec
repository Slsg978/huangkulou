# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['yys_02.py'],
    pathex=[os.path.abspath('.')],  # 加项目根路径
    binaries=[],
    datas=[
        ('img/huodong/*.png', 'img/huodong'),
        ('img/huodong/img.json', 'img/huodong'),
    ],
    hiddenimports=[
        'pygetwindow',
        'pyautogui',
        'cv2',
        'PIL',
        'pywinauto',
        'win32gui',
        'win32con',
        'keyboard'
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
    name='multi_window_clicker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True  # 改为 False 可隐藏控制台窗口
)
