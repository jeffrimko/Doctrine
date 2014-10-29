# -*- mode: python -*-

# Include all spellcheck dictionary files, as a folder named dict
dict_tree = Tree('./asciidoc', prefix = 'asciidoc')

a = Analysis(['doctrine.py'],
             pathex=['.'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          dict_tree,
          name='doctrine.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='doc.ico')
