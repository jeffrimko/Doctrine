import os
import sys

import PySide
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from asciidocapi import AsciiDocAPI

os.environ['ASCIIDOC_PY'] = r"asciidoc\asciidoc.py"

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Set up window.
        # self.setWindowTitle("Doctrine")
        self.resize(800, 600)

        # Set up `File` menu.
        self.menu_file = QMenu("&File")
        self.actn_open = QAction("&Open", self.menu_file)
        self.actn_reload = QAction("&Reload", self.menu_file)
        self.actn_display = QAction("&Display in browser", self.menu_file)
        self.actn_quit = QAction("&Quit", self.menu_file)
        self.menu_file.addAction(self.actn_open)
        self.menu_file.addAction(self.actn_reload)
        self.menu_file.addAction(self.actn_display)
        self.menu_file.addAction(self.actn_quit)

        self.menu_navi = QMenu("&Navigation")
        self.actn_frwd = QAction("&Forward", self.menu_navi)
        self.actn_back = QAction("&Backward", self.menu_navi)
        self.menu_navi.addAction(self.actn_frwd)
        self.menu_navi.addAction(self.actn_back)

        # Set up main menu bar.
        self.menubar = QMenuBar()
        self.menubar.addMenu(self.menu_file)
        self.menubar.addMenu(self.menu_navi)
        self.setMenuBar(self.menubar)

        self.webview = WebView()
        self.setCentralWidget(self.webview)

    def show_open_file(self, filter_="All Files (*)"):
        f,_ = QFileDialog.getOpenFileName(self, filter=filter_)
        return str(f)

class WebView(QWidget):
    def __init__(self):
        super(WebView, self).__init__()
        self.view = QWebView(self)

        self.setupInspector()

        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(splitter)

        splitter.addWidget(self.view)
        splitter.addWidget(self.inpsect)

    def setupInspector(self):
        page = self.view.page()
        page.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        self.inpsect = QWebInspector(self)
        self.inpsect.setPage(page)

        shortcut = QShortcut(self)
        shortcut.setKey(QKeySequence("F12"))
        shortcut.activated.connect(self.toggleInspector)
        self.inpsect.setVisible(False)

    def toggleInspector(self):
        self.inpsect.setVisible(not self.inpsect.isVisible())

class WebPage(QWebPage):
    """
    Makes it possible to use a Python logger to print javascript console messages
    """
    def __init__(self, logger=None, parent=None):
        super(WebPage, self).__init__(parent)
        if not logger:
            logger = logging
        self.logger = logger

    def javaScriptConsoleMessage(self, msg, lineNumber, sourceID):
        self.logger.warning("JsConsole(%s:%d): %s" % (sourceID, lineNumber, msg))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
