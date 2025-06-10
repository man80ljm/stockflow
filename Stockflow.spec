import os
import sys

def resource_path(relative_path):
    """获取资源路径，兼容打包环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 确保 data 目录存在
if hasattr(sys, '_MEIPASS'):
    data_dir = os.path.join(sys._MEIPASS, "data")
    os.makedirs(data_dir, exist_ok=True)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui', 'ui'),
        ('database', 'database'),
        ('models', 'models'),
        ('utils', 'utils'),
        ('data', 'data'),  # 包含 data 目录
    ],
    hiddenimports=['pandas', 'openpyxl', 'PyQt5'],
    hookspath=[],
    runtime_hooks=['hook.py'],  # 添加运行时钩子
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Stockflow',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Stockflow',
)