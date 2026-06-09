import sys
from pathlib import Path

block_cipher = None
script_dir = Path(SPECPATH)
ffmpeg_dir = Path(r"D:\ffmpeg-master-latest-win64-gpl-shared\bin")

a = Analysis(
    [str(script_dir / 'batch_convert.py')],
    pathex=[str(script_dir)],
    binaries=[
        (str(ffmpeg_dir / 'ffmpeg.exe'), '.'),
        (str(ffmpeg_dir / 'ffprobe.exe'), '.'),
    ],
    datas=[
        (str(script_dir / 'config.json'), '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='批量视频转码器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='批量视频转码器',
)
