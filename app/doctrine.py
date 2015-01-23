from ctypes import *
import filecmp
import fnmatch
import os
import platform
import shutil
import sys
import tempfile
import urllib
import urlparse
import uuid
import webbrowser
import zipfile
import time
import os.path as op

import PySide
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from asciidocapi import AsciiDocAPI
import doctview

# Set up the Asciidoc environment.
os.environ['ASCIIDOC_PY'] = op.join(op.dirname(__file__), r"asciidoc\asciidoc.py")
if getattr(sys, 'frozen', None):
    os.environ['ASCIIDOC_PY'] = op.normpath(op.join(sys._MEIPASS, r"asciidoc\asciidoc.py"))

# Splash displayed at startup.
SPLASH = r"static\splash.html"
if getattr(sys, 'frozen', None):
    SPLASH = op.join(sys._MEIPASS, r"static\splash.html")
SPLASH = QUrl().fromLocalFile(op.abspath(SPLASH))

# Splash displayed at startup.
RENDER = r"static\render.html"
if getattr(sys, 'frozen', None):
    RENDER = op.join(sys._MEIPASS, r"static\render.html")
RENDER = QUrl().fromLocalFile(op.abspath(RENDER))

# Prefix of the generated HTML document.
DOCPRE = "__doctrine-"
# Extension of the generated HTML document.
DOCEXT = ".html"

URLFILE = "file:///"

# Name of archive info file.
ARCINFO = "__archive_info__.txt"

# Name and version of the application.
NAMEVER = "Doctrine 0.1.0-alpha"

class DoctrineApp(QApplication):
    def __init__(self, *args, **kwargs):
        super(DoctrineApp, self).__init__(*args, **kwargs)
        self.aboutToQuit.connect(self._handle_quit)
        self._init_ui()
        self.deldoc = False
        self.docpath = None
        self.tmppath = None
        self.tmpdir = None

    def _init_ui(self):
        self.mainwin = doctview.MainWindow()
        self.mainwin.actn_reload.setDisabled(True)
        self.mainwin.actn_display.setDisabled(True)
        self.mainwin.menu_navi.setDisabled(True)
        self.mainwin.webview.view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.mainwin.actn_open.triggered.connect(self._handle_open)
        self.mainwin.actn_quit.triggered.connect(self.quit)
        self.mainwin.actn_reload.triggered.connect(self._handle_reload)
        self.mainwin.actn_frwd.triggered.connect(self._nav_forward)
        self.mainwin.actn_back.triggered.connect(self._nav_back)
        self.mainwin.actn_display.triggered.connect(self._handle_display)
        self.mainwin.webview.view.linkClicked.connect(self._handle_link)
        self.mainwin.webview.view.setAcceptDrops(True)
        self.mainwin.webview.view.dragEnterEvent = self._handle_drag
        self.mainwin.webview.view.dropEvent = self._handle_drop
        shortcut = QShortcut(self.mainwin)
        shortcut.setKey(QKeySequence("F5"))
        shortcut.activated.connect(self._handle_reload)
        self.mainwin.setWindowTitle(NAMEVER)
        # NOTE: Use to create custom context menu.
        self.mainwin.webview.view.contextMenuEvent = self._handle_context
        self.mainwin.webview.view.mouseReleaseEvent = self._handle_mouse

    def _nav_forward(self):
        self.mainwin.webview.view.page().triggerAction(QWebPage.Forward)

    def _nav_back(self):
        self.mainwin.webview.view.page().triggerAction(QWebPage.Back)

    def _handle_mouse(self, event=None):
        if event.button() == Qt.MouseButton.XButton1:
            self._nav_back()
            return
        if event.button() == Qt.MouseButton.XButton2:
            self._nav_forward()
            return
        return QWebView.mouseReleaseEvent(self.mainwin.webview.view, event)

    def _handle_context(self, event=None):
        if self.docpath:
            menu = QMenu()
            menu.addAction(self.mainwin.webview.style().standardIcon(QStyle.SP_BrowserReload), "Reload", self._handle_reload)
            menu.exec_(event.globalPos())

    def _handle_drag(self, event=None):
        event.accept()

    def _handle_drop(self, event=None):
        if event.mimeData().hasUrls():
            self._load_doc(str(event.mimeData().urls()[0].toLocalFile()))

    def _handle_quit(self):
        self._delete_tmppath()
        self._delete_tmpdir()

    def _handle_display(self):
        if not self.docpath:
            return
        if not self.tmppath:
            self._load_doc(reload_=True)
        if not self.tmppath:
            return
        webbrowser.open(self.tmppath)

    def _handle_reload(self):
        if self.docpath:
            self._load_doc(reload_=True)

    def _handle_link(self, url=None):
        # Open URLs to webpages with default browser.
        if is_webpage(url):
            webbrowser.open(str(url.toString()))
            return

        # Open links to Asciidoc files in Doctrine.
        if is_asciidoc(url2path(url)):
            self._load_doc(url2path(url))
            return

        # Open the URL in the webview.
        self.mainwin.webview.view.load(url)

    def _handle_open(self):
        # path = self.mainwin.show_open_file("Asciidoc Files (*.txt *.ad *.adoc *.asciidoc)")
        path = self.mainwin.show_open_file()
        self._load_doc(path)

    def _load_doc(self, path="", reload_=False):
        # Delete existing temp files.
        self._delete_tmppath()
        self._delete_tmpdir()

        # If not reloading the previous document, clear out tmppath.
        if not reload_:
            self.tmppath = None
            self.tmpdir = None

        # Set the doc path.
        prev = self.docpath
        if path:
            self.docpath = path
        if not self.docpath:
            return
        self.docpath = op.abspath(self.docpath)

        self.setOverrideCursor(QCursor(Qt.WaitCursor))

        # Attempt to prepare the document for display.
        url = ""
        if self.docpath.endswith(".txt"):
            url = self._prep_text()
        elif self.docpath.endswith(".zip"):
            url = self._prep_archive()
        elif self.docpath.endswith(".csv"):
            url = self._prep_csv()

        # NOTE: URL is populated only if ready to display output.
        if url:
            self.mainwin.webview.view.load(url)
            self.mainwin.actn_reload.setDisabled(False)
            self.mainwin.actn_display.setDisabled(False)
            self.mainwin.menu_navi.setDisabled(False)
            self.mainwin.setWindowTitle("%s (%s) - %s" % (
                op.basename(self.docpath),
                op.dirname(self.docpath),
                NAMEVER))
        elif prev:
            self.docpath = prev

        self.restoreOverrideCursor()

    def _prep_text(self):
        if not self.docpath:
            return
        if not self.tmppath:
            self.tmppath = getuniqname(op.dirname(self.docpath), DOCEXT, DOCPRE)
        try:
            AsciiDocAPI().execute(self.docpath, self.tmppath)
        except:
            self.restoreOverrideCursor()
            err_msg = str(sys.exc_info()[0])
            err_msg += "\n"
            err_msg += str(sys.exc_info()[1])
            self.mainwin.show_error_msg(err_msg)
        return QUrl().fromLocalFile(self.tmppath)

    def _prep_archive(self):
        if not self.docpath:
            return
        if not self.tmpdir:
            self.tmpdir = tempfile.mkdtemp()
        if self.tmpdir and not op.isdir(self.tmpdir):
            os.makedirs(self.tmpdir)
        zfile = zipfile.ZipFile(self.docpath)
        zfile.extractall(self.tmpdir)

        path = ""

        # Attempt to locate archive info file.
        arcinfo = op.join(self.tmpdir, ARCINFO)
        if op.exists(arcinfo):
            path = arcinfo

        # If no archive info file found, attempt to locate any asciidoc text file.
        if not path:
            txts = findfile("*.txt", self.tmpdir)
            if txts:
                path = txts[0]

        # If no text file path was found, bail.
        if not path:
            return

        if not self.tmppath:
            self.tmppath = getuniqname(op.dirname(path), DOCEXT, DOCPRE)
        AsciiDocAPI().execute(path, self.tmppath)
        return QUrl().fromLocalFile(self.tmppath)

    def _prep_csv(self):
        if not self.docpath:
            return
        if not self.tmppath:
            self.tmppath = getuniqname(op.dirname(self.docpath), DOCEXT, DOCPRE)
        path = getuniqname(op.dirname(self.docpath), ".txt", "__temp-")
        with open(path, "w") as f:
            f.write('[format="csv"]\n')
            f.write("|===\n")
            f.write("include::" + self.docpath + "[]\n")
            f.write("|===\n")
        AsciiDocAPI().execute(path, self.tmppath)
        os.remove(path)
        return QUrl().fromLocalFile(self.tmppath)

    def _delete_tmppath(self):
        """Deletes the rendered HTML."""
        if not self.tmppath:
            return
        retries = 3
        while retries:
            if not op.exists(self.tmppath):
                return
            try:
                os.remove(self.tmppath)
            except:
                time.sleep(0.1)
                retries -= 1

    def _delete_tmpdir(self):
        """Deletes the temporary directory."""
        if not self.tmpdir:
            return
        if op.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)

    def show_main(self):
        self.mainwin.show()
        self.mainwin.webview.view.load(SPLASH)

    def run_loop(self):
        if self.docpath:
            self._load_doc()
        self.exec_()

def getuniqname(base, ext, pre=""):
    """Returns a unique random file name at the given base directory. Does not
    create a file."""
    while True:
        uniq = op.join(base, pre + "tmp" + str(uuid.uuid4())[:6] + ext)
        if not os.path.exists(uniq):
            break
    return op.normpath(uniq)

def is_webpage(url):
    # Handle types.
    url = url2str(url)
    if type(url) != str:
        return False

    # Return true if URL is external webpage, false otherwise.
    if url.startswith("http:") or url.startswith("https:"):
        return True
    return False

def findfile(pattern, path):
    """Finds a file matching the given pattern in the given path. Taken from
    `http://stackoverflow.com/questions/1724693/find-a-file-in-python`."""
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(op.join(root, name))
    return result

def url2path(url):
    url = url2str(url)
    if url.startswith(URLFILE):
        url = url[len(URLFILE):]
    return op.normpath(url)

def url2str(url):
    if type(url) == PySide.QtCore.QUrl:
        url = str(url.toString())
    return url

def is_asciidoc(path):
    if path.endswith(".txt"):
        return True
    return False

if __name__ == '__main__':
    app = DoctrineApp(sys.argv)
    if len(sys.argv) > 1 and op.isfile(sys.argv[1]):
        app.docpath = str(sys.argv[1])
    app.show_main()
    app.run_loop()
