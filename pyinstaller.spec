# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Git Dungeon
打包配置
"""

import sys
import os

PROJECT_NAME = "GitDungeon"
VERSION = "1.0.0"

a = Analysis(
    ['src/main_cli.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('docs', 'docs'),
    ],
    hiddenimports=[
        'pkg_resources.py2_warn',
        'git',
        'git.cmd',
        'git.config',
        'git.diff',
        'git.exc',
        'git.index',
        'git.objects',
        'git.objects.base',
        'git.objects.blob',
        'git.objects.commit',
        'git.objects.refs',
        'git.objects.tag',
        'git.objects.tree',
        'git.objects.util',
        'git.repo.base',
        'git.repo.fun',
        'git.repo.util',
        'git.util',
        'gitdb',
        'gitdb.db',
        'gitdb.db.base',
        'gitdb.db.ref',
        'gitdb.db.loose',
        'gitdb.db.pack',
        'gitdb.fun',
        'gitdb.obj',
        'gitdb.pack',
        'gitdb.sha',
        'gitdb.stream',
        'gitdb.util',
        'pydantic',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.datetime_parse',
        'pydantic.validators',
        'pydantic.error_wrappers',
        'pydantic.class_validators',
        'pydantic.types',
        'pydantic.utils',
        'toml',
        'toml.encoder',
        'toml.decoder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'textual',
        'bs4',
        'urllib3',
        'requests',
        'numpy',
        'scipy',
        'pandas',
        'matplotlib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=PROJECT_NAME,
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
    icon=None,
)

print(f"""
========================================
PyInstaller Configuration Complete
========================================

Project: {PROJECT_NAME}
Version: {VERSION}
Platform: {sys.platform}

To build:
  {sys.executable} -m PyInstaller pyinstaller.spec

Output: {PROJECT_NAME} (executable)
""")
