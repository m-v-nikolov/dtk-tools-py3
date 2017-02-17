import wx
from SetupSplash import MySplashScreen


class SetupApplication:
    def __init__(self):
        pass

    def run(self):
        self.main()

        # self.main3()

    def main(self):
        # show splash first
        app = MyApp(False)
        app.MainLoop()


    def main3(self):
        from MainForm import SetupEditor

        app = wx.App()
        frame = SetupEditor(title='DTK Setup Configuration Editor')
        frame.Center()
        frame.refresh()
        frame.Show()
        app.MainLoop()


class MyApp(wx.App):
    def OnInit(self):
        wx.App.__init__(self)
        self.SetAppName("DTK Setup")

        # Create and show the splash screen.  It will then create and
        # show the main frame when it is time to do so.  Normally when
        # using a SplashScreen you would create it, show it and then
        # continue on with the applicaiton's initialization, finally
        # creating and showing the main application window(s).  In
        # this case we have nothing else to do so we'll delay showing
        # the main frame until later (see ShowMain above) so the users
        # can see the SplashScreen effect.
        splash = MySplashScreen()
        splash.Show()

        return True
