"""This script implements the main Doctrine application."""

##==============================================================#
## DEVELOPED 2014, REVISED 2014, Jeff Rimko.                    #
##==============================================================#

##==============================================================#
## SECTION: Imports                                             #
##==============================================================#

import fnmatch
import os
import shutil
import sys
import tempfile
import urllib
import urlparse
import webbrowser
import zipfile

import wx
import wx.html2
from asciidocapi import AsciiDocAPI

import doctview

##==============================================================#
## SECTION: Global Definitions                                  #
##==============================================================#

# Set up the Asciidoc environment.
if getattr(sys, 'frozen', None):
    asciidoc_path = os.path.normpath(os.path.join(sys._MEIPASS, r"asciidoc"))
    os.environ['ASCIIDOC_PY'] = os.path.join(asciidoc_path, "asciidoc.py")
else:
    os.environ['ASCIIDOC_PY'] = r"asciidoc\asciidoc.py"

# Name and version of the application.
NAMEVER = "Doctrine 0.1.0-alpha"

# Default open file wildcard.
WILDCARD = "Asciidoc Text (*.txt)|*.txt|" \
        "Zip Archive (*.zip)|*.zip|" \
        "All files (*.*)|*.*"

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
        self.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self._handle_navigate, self.mainwin.mainpanel.webview)
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
        path = str(path)

        # Handle file type.
        if path.endswith(".txt"):
            self.docpath = str(path)
        elif path.endswith(".zip"):
            self.tmpdir = tempfile.mkdtemp()
            zfile = zipfile.ZipFile(path)
            zfile.extractall(self.tmpdir)
            txts = findfile("*.txt", self.tmpdir)
            if txts:
                self.docpath = txts[0]
            else:
                self._delete_tmpdir()
                return False
        else:
            return False

        return True

    def _handle_navigate(self, event=None):
        """Handles a navigation event."""
        url = event.GetURL()
        if self._set_doc(url):
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
        self.tmppath = os.path.join(os.path.dirname(self.docpath), "__doctrine__.html")
        AsciiDocAPI().execute(self.docpath, self.tmppath)

    def _delete_html(self):
        """Deletes the rendered HTML."""
        if not self.tmppath:
            return
        if os.path.exists(self.tmppath):
            os.remove(self.tmppath)

    def _delete_tmpdir(self):
        """Deletes the temporary directory."""
        if not self.tmpdir:
            return
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)

    def show_main(self):
        """Shows the main application."""
        self.mainwin.show()

    def run_loop(self):
        """Runs the main application loop."""
        if self.docpath:
            self._load_doc()
        self.MainLoop()

    def quit(self, event=None):
        """Exits the application."""
        self._delete_html()
        self._delete_tmpdir()
        self.mainwin.Destroy()

##==============================================================#
## SECTION: Function Definitions                                #
##==============================================================#

def path2url(path):
    """Converts a local path to a valid file URL. Taken from
    `http://stackoverflow.com/a/14298190/789078`."""
    path = os.path.abspath(path)
    return urlparse.urljoin("file:", urllib.pathname2url(path))

def findfile(pattern, path):
    """Finds a file matching the given pattern in the given path. Taken from
    `http://stackoverflow.com/questions/1724693/find-a-file-in-python`."""
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


##==============================================================#
## SECTION: Main Body                                           #
##==============================================================#

if __name__ == '__main__':
    app = DoctrineApp()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        app.docpath = str(sys.argv[1])
    app.show_main()
    app.run_loop()
