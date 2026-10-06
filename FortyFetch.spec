# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

ctk_dir = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        (ctk_dir, 'customtkinter'),
    ],
    hiddenimports=[
        'customtkinter',
        'darkdetect',
        'PIL',
        'PIL._tkinter_finder',
        'yt_dlp',
        'yt_dlp.utils',
        'yt_dlp.extractor',
        'yt_dlp.extractor.lazy_extractors',
        'yt_dlp.downloader',
        'yt_dlp.postprocessor',
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
    a.binaries,
    a.datas,
    [],
    name='FortyFetch',
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
    icon=['assets\\icon.ico'],
    version='version_info.txt',
    manifest='app.manifest',
)
