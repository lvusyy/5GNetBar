# -*- mode: python -*-

block_cipher = None

a = Analysis(['5GNetBar_app.py'],
             pathex=['.'],
             binaries=[],
             datas=[],
             hiddenimports=['requests', 'Foundation', 'AppKit', 'objc'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='5GNetBar',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='5GNetBar')

app = BUNDLE(coll,
             name='5GNetBar.app',
             icon='Myicon.icns',
             bundle_identifier=None)