# -*- mode: python -*-

FILES = [("qt.conf", "qt.conf", "DATA")]
TREES = [
        Tree("asciidoc", prefix="asciidoc"),
        Tree("static", prefix="static"),
        Tree(r"C:\Python27\Lib\site-packages\PySide\imports", prefix="imports"),
        Tree(r"C:\Python27\Lib\site-packages\PySide\translations", prefix="translations"),
        Tree(r"C:\Python27\Lib\site-packages\PySide\plugins", prefix="plugins")]

##==============================================================#
## SECTION: Function Definitions                                #
##==============================================================#

def Datafiles(*filenames, **kw):
    """Function to specify data files to be included in the output executable.
    Taken from 'http://www.pyinstaller.org/wiki/Recipe/CollectDatafiles'.
    """
    def datafile(path, strip_path=True):
        parts = path.split('/')
        path = name = os.path.join(*parts)
        if strip_path:
            name = os.path.basename(path)
        return name, path, 'DATA'
    strip_path = kw.get('strip_path', True)
    return TOC(datafile(filename, strip_path=strip_path) for filename in filenames if os.path.isfile(filename))

##==============================================================#
## SECTION: Main Body                                           #
##==============================================================#

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
        TOC(FILES),
        name='doctrine.exe',
        debug=False,
        strip=None,
        upx=True,
        console=False,
        icon='doc.ico',
        *TREES)
