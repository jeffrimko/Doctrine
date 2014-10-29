"""This script implements the GUI view layer of the Doctrine application."""

##==============================================================#
## COPYRIGHT 2014, REVISED 2014, Jeff Rimko.                    #
##==============================================================#

##==============================================================#
## SECTION: Imports                                             #
##==============================================================#

import os

import wx
import wx.html2

##==============================================================#
## SECTION: Global Definitions                                  #
##==============================================================#

# Default window size.
WIN_SZ = (800, 600)

##==============================================================#
## SECTION: Class Definitions                                   #
##==============================================================#

class MainPanel(wx.Panel):
    """The main panel of the application."""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.webview = wx.html2.WebView.New(self)
        sizer.Add(self.webview, 1, wx.EXPAND, 10)
        self.SetSizer(sizer)

class MainWindow(wx.Frame):
    """The main window of the application."""
    def __init__(self, parent, title):
        """This function defines initialization logic of the main window."""
        self.parent = parent
        wx.Frame.__init__(self,
                self.parent,
                title=title)

        # Set up `File` menu.
        filemenu = wx.Menu()
        self.fm_open = filemenu.Append(wx.ID_OPEN, "&Open")
        self.fm_dispbw = filemenu.Append(-1, "&Display in browser")
        self.fm_reload = filemenu.Append(-1, "&Reload")
        self.fm_quit = filemenu.Append(wx.ID_EXIT, "&Quit", "Quit application")

        navmenu = wx.Menu()
        self.nm_backward = navmenu.Append(-1, "Backward")
        self.nm_forward = navmenu.Append(-1, "Forward")

        # Set up main menu bar.
        self.menubar = wx.MenuBar()
        self.menubar.Append(filemenu, '&File')
        self.menubar.Append(navmenu, '&Navigate')
        self.SetMenuBar(self.menubar)

        # Set up main web view.
        self.mainpanel = MainPanel(self)

        self.SetSize(WIN_SZ)

    def show_open_file(self, wildcard):
        """Shows the open file dialog with the given wildcard."""
        dialog = wx.FileDialog(None, "Choose a file", os.getcwd(), "", wildcard, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            return dialog.GetPath()
        return None

    def show(self):
        """Shows the main window."""
        self.Show(True)

##==============================================================#
## SECTION: Main Body                                           #
##==============================================================#

if __name__ == '__main__':
    # Demo of GUI.
    app = wx.App(False)
    frame = MainWindow(None, "demo")
    frame.Show()
    app.MainLoop()
