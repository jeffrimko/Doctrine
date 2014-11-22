"""This script implements the main Doctrine application."""

##==============================================================#
## DEVELOPED 2014, REVISED 2014, Jeff Rimko.                    #
##==============================================================#

##==============================================================#
## SECTION: Imports                                             #
##==============================================================#

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
import os.path as op
from ctypes import *

import wx
import wx.html2
from asciidocapi import AsciiDocAPI

import doctview

##==============================================================#
## SECTION: Global Definitions                                  #
##==============================================================#

# Set up the Asciidoc environment.
os.environ['ASCIIDOC_PY'] = r"asciidoc\asciidoc.py"
if getattr(sys, 'frozen', None):
    os.environ['ASCIIDOC_PY'] = op.normpath(op.join(sys._MEIPASS, r"asciidoc\asciidoc.py"))

# Splash displayed at startup.
SPLASH = r"static\splash.html"
if getattr(sys, 'frozen', None):
    SPLASH = op.join(sys._MEIPASS, r"static\splash.html")

# Rednering message displayed when document loaded.
RENDER = r"static\render.html"
if getattr(sys, 'frozen', None):
    RENDER = op.join(sys._MEIPASS, r"static\render.html")

# Name and version of the application.
NAMEVER = "Doctrine 0.1.0-alpha"

# Default open file wildcard.
WILDCARD = "Asciidoc Text (*.txt)|*.txt|" \
        "Zip Archive (*.zip)|*.zip|" \
        "All files (*.*)|*.*"

# Prefix of the generated HTML document.
DOCPRE = "__doctrine-"
# Extension of the generated HTML document.
DOCEXT = ".html"

# Name of archive info file.
ARCINFO = "__archive_info__.txt"

##==============================================================#
## SECTION: Class Definitions                                   #
##==============================================================#

class DoctrineApp(wx.App):
    def OnInit(self):
        self._init_ui()
        self.docpath = None
        self.tmppath = None
        self.tmpdir = None
        self.redirect = False
        self.deldoc = False
        return True

    def _init_ui(self):
        """Initializes the application UI elements."""
        self.mainwin = doctview.MainWindow(None, NAMEVER)

        # Bind UI events.
        self.Bind(wx.EVT_MENU, self._open_file, self.mainwin.fm_open)
        self.Bind(wx.EVT_MENU, self._load_doc, self.mainwin.fm_reload)
        self.Bind(wx.EVT_MENU, self._display_browser, self.mainwin.fm_dispbw)
        self.Bind(wx.EVT_MENU, self._nav_forward, self.mainwin.nm_forward)
        self.Bind(wx.EVT_MENU, self._nav_backward, self.mainwin.nm_backward)
        self.Bind(wx.EVT_MENU, self.quit, self.mainwin.fm_quit)
        self.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self._handle_navigating, self.mainwin.mainpanel.webview)
        self.Bind(wx.html2.EVT_WEBVIEW_NAVIGATED, self._handle_navigated, self.mainwin.mainpanel.webview)
        self.mainwin.Bind(wx.EVT_CLOSE, self.quit)

        # Set UI to initial state.
        self.mainwin.fm_reload.Enable(False)
        self.mainwin.fm_dispbw.Enable(False)
        self.mainwin.menubar.EnableTop(1, False)

    def _nav_forward(self, event=None):
        """Handles navigation forward."""
        webview = self.mainwin.mainpanel.webview
        if webview.CanGoForward():
            webview.GoForward()

    def _nav_backward(self, event=None):
        """Handles navigation backward."""
        webview = self.mainwin.mainpanel.webview
        if webview.CanGoBack():
            webview.GoBack()

    def _set_doc(self, path):
        """Sets the document to be rendered. Returns true if a new document has
        been set, false otherwise."""
        path = op.normpath(str(path))
        self.deldoc = False

        # Open linked web URLs in the default browser.
        if (path.startswith("http:") or path.startswith("https:")) and self.tmppath:
            webbrowser.open(path)
            self._display_html() # Needed to prevent navigation to website.
            return

        # Delete temporary directory if a new document is set.
        if self.tmpdir:
            chk_tmp = self.tmpdir
            chk_pth = path
            if "Windows" == platform.system():
                # HACK ALERT: the `fixwinpath()` calls are needed because
                # sometimes a short path name is returned. Also sometimes the
                # path is lower case so just force it lower on windows.
                chk_tmp = fixwinpath(chk_tmp)
                chk_pth = fixwinpath(chk_pth)
            common = op.commonprefix([chk_pth, chk_tmp])
            if not common == chk_tmp:
                self._delete_tmpdir()

        # Handle file type.
        if path.endswith(".txt"):
            self.docpath = str(path)
            return True
        elif path.endswith(".zip"):
            # Extract all zip contents to a temporary directory.
            self.tmpdir = tempfile.mkdtemp()
            zfile = zipfile.ZipFile(path)
            zfile.extractall(self.tmpdir)

            # Attempt to locate archive info file.
            arcinfo = op.join(self.tmpdir, ARCINFO)
            if op.exists(arcinfo):
                self.docpath = arcinfo
                return True

            # Attempt to locate any text file.
            txts = findfile("*.txt", self.tmpdir)
            if txts:
                self.docpath = txts[0]
                return True

            # Delete the temporary directory since no valid document was found.
            self._delete_tmpdir()

        elif path.endswith(".csv"):
            self.docpath = getuniqname(op.dirname(path), ".txt", "__temp-")
            with open(self.docpath, "w") as f:
                f.write('[format="csv"]\n')
                f.write("|===\n")
                f.write("include::" + path + "[]\n")
                f.write("|===\n")
            self.deldoc = True
            return True

        return False

    def _handle_navigating(self, event=None):
        """Handles a navigating event."""
        url = event.GetURL()
        if self._set_doc(url):
            self._load_doc()

    def _handle_navigated(self, event=None):
        url = event.GetURL()
        if url.endswith(".zip"):
            # NOTE: This is a hack to get the IE backend to properly render the
            # document. Without this extra `_load_doc()` call, the zip file
            # contents will be shown if the file was drag-and-dropped onto the
            # web view window.
            self._load_doc()

    def _open_file(self, event=None):
        """Handles an open file event."""
        path = self.mainwin.show_open_file(WILDCARD)
        if self._set_doc(path):
            self._load_doc()

    def _load_doc(self, event=None):
        """Handles the logic to cleanup, render, and display a file.

        :Preconditions:
          - Attribute `docpath` should be set to a valid file to render.
        """
        self.mainwin.mainpanel.webview.LoadURL(path2url(RENDER))
        self._delete_html()
        self._create_html()
        self._display_html()

    def _display_browser(self, event=None):
        """Opens the rendered document in the default browser."""
        if not self.tmppath:
            return
        webbrowser.open(self.tmppath)

    def _display_html(self):
        """Displays the rendered HTML."""
        if not self.tmppath:
            return
        url = path2url(self.tmppath)
        self.mainwin.mainpanel.webview.LoadURL(url)
        title = "%s - %s" % (NAMEVER, self.docpath)
        self.mainwin.SetTitle(title)
        self.mainwin.fm_dispbw.Enable(True)
        self.mainwin.fm_reload.Enable(True)
        self.mainwin.menubar.EnableTop(1, True)

    def _create_html(self):
        """Creates the rendered HTML."""
        if not self.docpath:
            return
        self.tmppath = getuniqname(op.dirname(self.docpath), DOCEXT, DOCPRE)
        AsciiDocAPI().execute(self.docpath, self.tmppath)
        if self.deldoc:
            os.remove(self.docpath)
            self.deldoc = False

    def _delete_html(self):
        """Deletes the rendered HTML."""
        if not self.tmppath:
            return
        if op.exists(self.tmppath):
            os.remove(self.tmppath)
            self.tmppath = None

    def _delete_tmpdir(self):
        """Deletes the temporary directory."""
        if not self.tmpdir:
            return
        if op.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)
            self.tmpdir = None

    def show_main(self):
        """Shows the main application."""
        self.mainwin.show()

    def run_loop(self):
        """Runs the main application loop."""
        if self.docpath:
            self._load_doc()
        else:
            self.mainwin.mainpanel.webview.LoadURL(path2url(SPLASH))
        self.MainLoop()

    def quit(self, event=None):
        """Exits the application."""
        self._delete_html()
        self._delete_tmpdir()
        self.mainwin.Destroy()

##==============================================================#
## SECTION: Function Definitions                                #
##==============================================================#

def getuniqname(base, ext, pre=""):
    """Returns a unique random file name at the given base directory. Does not
    create a file."""
    while True:
        uniq = op.join(base, pre + "tmp" + str(uuid.uuid4())[:6] + ext)
        if not os.path.exists(uniq):
            break
    return uniq

def path2url(path):
    """Converts a local path to a valid file URL. Taken from
    `http://stackoverflow.com/a/14298190/789078`."""
    path = op.abspath(path)
    return urlparse.urljoin("file:", urllib.pathname2url(path))

def findfile(pattern, path):
    """Finds a file matching the given pattern in the given path. Taken from
    `http://stackoverflow.com/questions/1724693/find-a-file-in-python`."""
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(op.join(root, name))
    return result

def fixwinpath(path):
    """Returns a lowercase full path for any given windows path."""
    buf = create_unicode_buffer(500)
    winpath = windll.kernel32.GetLongPathNameW
    winpath(unicode(path), buf, 500)
    return str(buf.value).lower()

##==============================================================#
## SECTION: Main Body                                           #
##==============================================================#

if __name__ == '__main__':
    app = DoctrineApp()
    if len(sys.argv) > 1 and op.isfile(sys.argv[1]):
        app.docpath = str(sys.argv[1])
    app.show_main()
    app.run_loop()
