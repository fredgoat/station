# -*- mode: python -*-

block_cipher = None


a = Analysis(['component.py'],
             pathex=['C:\\Users\\Damian\\Documents\\GitHub\\station'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
			 
#for d in a.datas:
#    if 'pyconfig' in d[0]:
#        a.datas.remove(d)
#        break
#		
#a.datas += [('C:\\Users\\Damian\\Documents\\GitHub\\station\\*.bmp', '.'), \
#('C:\\Users\\Damian\\Documents\\GitHub\\station\\*.png', '.')]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='component',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
