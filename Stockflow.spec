a = Analysis(
    ['main.py'],
    pathex=['D:\\stockflow\\database'],  # 显式添加 database 目录
    binaries=[],
    datas=[
        ('ui', 'ui'),
        ('database', 'database'),
        ('models', 'models'),
        ('utils', 'utils'),
        ('data', 'data'),
    ],
    hiddenimports=['pandas', 'openpyxl', 'PyQt5', 'db_setup'],  # 显式包含 db_setup
    hookspath=[],
    runtime_hooks=[],
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