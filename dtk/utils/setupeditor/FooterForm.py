import wx
import wx.lib.dialogs
from dtk.utils.setupeditor.utils import get_file_path

try:
    from agw import hyperlink as hl
except ImportError:     # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.hyperlink as hl

class FooterPanel(wx.Panel):
    """
    """

    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox_path = self.get_path_box(font)
        vbox.Add(vbox_path, flag=wx.EXPAND)

        self.SetSizer(vbox)

    def get_path_box(self, font):

        vbox_path = wx.BoxSizer(wx.VERTICAL)

        st_local = wx.StaticText(self, label='Local Path')
        st_local.SetFont(font)
        st_local.SetForegroundColour('sea green')
        vbox_path.Add(st_local, flag=wx.LEFT | wx.RIGHT, border=10)

        self.local_hyperlink = hl.HyperLinkCtrl(self, wx.ID_ANY, get_file_path(True), URL="")
        self.local_hyperlink.SetFont(font)
        self.local_hyperlink.SetColours("BLUE", "BLUE", "BLUE")
        self.local_hyperlink.EnableRollover(True)
        self.local_hyperlink.Bind(hl.EVT_HYPERLINK_LEFT, self.onLocalHyperLink)
        self.local_hyperlink.SetToolTip(wx.ToolTip("Click to view file"))
        self.local_hyperlink.AutoBrowse(False)
        self.local_hyperlink.UpdateLink()
        vbox_path.Add(self.local_hyperlink, flag=wx.LEFT | wx.RIGHT, border=10)

        vbox_path.Add((-1, 10))

        st_global = wx.StaticText(self, label='Global Path')
        st_global.SetFont(font)
        st_global.SetForegroundColour('sea green')
        vbox_path.Add(st_global, flag=wx.LEFT | wx.RIGHT, border=10)

        self.global_hyperlink = hl.HyperLinkCtrl(self, wx.ID_ANY, get_file_path(False), URL="")
        self.global_hyperlink.SetFont(font)
        self.global_hyperlink.SetColours("GOLD", "GOLD", "GOLD")
        self.global_hyperlink.EnableRollover(True)
        self.global_hyperlink.Bind(hl.EVT_HYPERLINK_LEFT, self.onGlobalHyperLink)
        self.global_hyperlink.SetToolTip(wx.ToolTip("Click to view file"))
        self.global_hyperlink.AutoBrowse(False)
        self.global_hyperlink.UpdateLink()
        vbox_path.Add(self.global_hyperlink, flag=wx.LEFT | wx.RIGHT, border=10)

        return vbox_path

    def onLocalHyperLink(self, event):
        ini_file = get_file_path(True)
        with open(ini_file, "r") as f:
            txt = f.read()

        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, txt, "LOCAL INI FIle", size=(500, 700),
                                                   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        dlg.ShowModal()
        dlg.Destroy()

    def onGlobalHyperLink(self, event):
        ini_file = get_file_path(False)
        with open(ini_file, "r") as f:
            txt = f.read()

        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, txt, "GLOBAL INI FIle", size=(500, 700),
                                                   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        dlg.ShowModal()
        dlg.Destroy()