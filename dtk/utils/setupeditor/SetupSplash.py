import os
import wx
from MainForm import SetupEditor


class MySplashScreen(wx.SplashScreen):
    """
Create a splash screen widget.
    """
    def __init__(self, parent=None):
        demoPath = os.path.dirname(__file__)
        img_path = os.path.join(demoPath, "dtk_flash.jpg")
        aBitmap = wx.Image(name=img_path).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 3000   # milliseconds
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 splashDuration, parent)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.fc = wx.FutureCall(3000, self.ShowMain)

        wx.Yield()

    def ShowMain(self):
        frame = SetupEditor(title='DTK Setup Configuration Editor')
        frame.Center()
        frame.refresh()
        frame.Show()

        if self.fc.IsRunning():
            self.Raise()

    def OnExit(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()

        # if the timer is still running then go ahead and show the
        # main frame now
        if self.fc.IsRunning():
            self.fc.Stop()
            self.ShowMain()




