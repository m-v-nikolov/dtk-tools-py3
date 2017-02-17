import wx
from wx.lib.wordwrap import wordwrap
from dtk.utils.setupeditor.utils import get_file_path
from FooterForm import FooterPanel
from ConfigEditForm import ConfigEditPanel
from ConfigOptionForm import ConfigOptionPanel
import wx.aui
import os
import re

try:
    from agw import aquabutton as AB
except ImportError:     # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.aquabutton as AB


class SetupEditor(wx.Frame):

    def __init__(self, title=None):
        wx.Frame.__init__(self, None, wx.ID_ANY, title, size=(1000, 850))
        self.SetMinSize((1000, 850))
        # self.Bind(wx.EVT_CLOSE, self.OnCloseClick)
        self.set_icon()

        # self.panel_flash = None
        self.panel_config = None
        self.panel_edit = None
        self.panel_path = None
        self.panel_footer = None

        self.toolbar = None
        self.statusbar = None
        self.panel_view = None
        self.panel_content = None
        self.btn_save = None
        self.btn_delete = None
        self.bmp_plus = None
        self.bmp_save = None

        self.allowAuiFloating = False
        self.init()

        self.Layout()

    def set_icon(self):
        demoPath = os.path.dirname(__file__)
        img_path = os.path.join(demoPath, "dtk_logo.jpg")
        bmp = wx.Image(name=img_path).Scale(64, 64).ConvertToBitmap()

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(wx.Bitmap(img_path, wx.BITMAP_TYPE_ANY))
        icon.CopyFromBitmap(bmp)
        self.SetIcon(icon)

    def cleanup_controls(self):
        boxes = self.GetChildren()
        for box in boxes:
            box.Destroy()

    def init(self):
        self.define_menubar()
        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -1])
        statusText = "Welcome to DTK Configuration Editor!"
        self.statusbar.SetStatusText(statusText, 0)
        self.SetStatusBar(self.statusbar)

        self.panel_config = ConfigOptionPanel(self)
        self.panel_view = wx.Panel(self, -1)
        self.panel_edit = ConfigEditPanel(self.panel_view)

        self.panel_content = wx.TextCtrl(self.panel_view, name='content', style=wx.TE_MULTILINE | wx.TE_RICH2)
        self.panel_content.SetEditable(False)
        self.panel_content.SetBackgroundColour('grey')

        vbox_view = wx.BoxSizer(wx.VERTICAL)
        vbox_view.Add(self.panel_edit, proportion=1, flag=wx.EXPAND)
        vbox_view.Add(self.panel_content, proportion=1, flag=wx.EXPAND)
        self.panel_view.SetSizer(vbox_view)

        self.panel_footer = panel_footer = wx.Panel(self, -1)
        self.panel_path = FooterPanel(panel_footer)

        vbox_footer = wx.BoxSizer(wx.HORIZONTAL)
        vbox_footer.Add(self.panel_path,  proportion=1, flag=wx.EXPAND | wx.ALIGN_LEFT)

        p = wx.Panel(self.panel_footer, -1)
        hbox_buttons = self.define_buttons_box(p)
        p.SetSizer(hbox_buttons)
        vbox_footer.Add(p, proportion=1, flag=wx.EXPAND | wx.ALIGN_RIGHT)

        panel_footer.SetSizer(vbox_footer)

        self.toolbar = self.define_toolbar()
        self.SetToolBar(self.toolbar)

        self._mgr = wx.aui.AuiManager(self)
        self._mgr.AddPane(self.panel_config,
                          wx.aui.AuiPaneInfo().
                          Left().BestSize((500, -1)).
                          MinSize((240, -1)).
                          CaptionVisible(False).
                          CloseButton(False).
                          Name("DemoTree"))
        self._mgr.AddPane(self.panel_view, wx.CENTER)
        self._mgr.AddPane(self.panel_footer,
                          wx.aui.AuiPaneInfo().
                          Bottom().BestSize((-1, 100)).
                          MinSize((-1, 100)).
                          CaptionVisible(False).
                          Fixed().
                          CloseButton(False).
                          Name("PathWindow"))

        # tell the manager to 'commit' all the changes just made
        self._mgr.Update()

    def define_menubar(self):
        # Prepare the menu bar
        menuBar = wx.MenuBar()

        # 1st menu from left
        menu1 = wx.Menu()
        menu1.Append(101, "&Open...", "Open Configuration File")
        menu1.AppendSeparator()
        menu1.Append(102, "&Close", "Close this frame")
        # Add menu to the menu bar
        menuBar.Append(menu1, "&File")

        # 2nd menu from left
        menu2 = wx.Menu()
        menu2.Append(201, "Setup UI")

        # Append 2nd menu
        menuBar.Append(menu2, "&About")

        self.SetMenuBar(menuBar)

        # Menu events
        self.Bind(wx.EVT_MENU, self.open_file, id=101)
        self.Bind(wx.EVT_MENU, self.close_window, id=102)
        self.Bind(wx.EVT_MENU, self.about_setup_ui, id=201)

    def open_file(self, event):
        print 'Open configuration file'

        print"OnButton_file: %s\n" % os.getcwd()

        wildcard = "Python source (*.py)|*.py|" \
                   "Text files (*.txt)|*.txt|" \
                   "INI files (*.ini)|*.ini|" \
                   "Json files (*.json)|*.json|" \
                   "Config file (*.config)|*.config|" \
                   "All files (*.*)|*.*"

        dlg = wx.FileDialog(
            None, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
        )

        config_file = None
        if dlg.ShowModal() == wx.ID_OK:
            config_file = dlg.GetPath()

        dlg.Destroy()

        if config_file is None:
            return

        with open(config_file, "r") as f:
            txt = f.read()

        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, txt, os.path.basename(config_file), size=(500, 700),
                                                   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        dlg.ShowModal()
        dlg.Destroy()

    def close_window(self, event):
        self.OnCloseClick(event)

    def get_setup(self):
        file_setup = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "setup.py"))

        begin = False
        setup_list = []
        with open(file_setup, "r") as f:
            for line in f:
                line = line.strip()
                ok = re.match(r'^.*setup\(.*$', line)
                if ok:
                    # print line
                    begin = True
                    setup_list.append(line)
                elif begin and re.match(r'^def handle_init.*:$', line):
                    break
                elif begin:
                    if len(line) > 0:
                        setup_list.append(line)

        setup_str = '\n'.join(setup_list)
        setup_str = setup_str.replace('setup', 'dict')
        setup_str = setup_str.replace('find_packages()', "'find_packages()'")

        setup_dict = eval(setup_str)
        return setup_dict

    def build_authors(self, setup_dict):
        author_list = setup_dict['author'].split(',')
        email_list = setup_dict['author_email'].split(',')

        m = zip(author_list, email_list)
        f = ['%s (%s)' % (a, e) for (a, e) in m]

        return f

    def about_setup_ui(self, event):
        setup_dict = self.get_setup()

        licenseText = "Completely and totally open source!"

        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = "DTK Setup UI"
        info.Version = setup_dict['version']
        info.Copyright = "Copyright (C) 2017 IDM"
        info.Description = wordwrap(setup_dict['description'], 350, wx.ClientDC(self))
        info.WebSite = (setup_dict['version'], "DTK GITHUB Page")
        info.Developers = ['\n'.join(self.build_authors(setup_dict))]
        info.License = wordwrap(licenseText, 500, wx.ClientDC(self))

        demoPath = os.path.dirname(__file__)
        img_path = os.path.join(demoPath, "dtk_logo.jpg")
        bmp = wx.Image(name=img_path).Scale(64, 64).ConvertToBitmap()

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(wx.Bitmap(img_path, wx.BITMAP_TYPE_ANY))
        icon.CopyFromBitmap(bmp)
        info.SetIcon(icon)

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)

    def define_buttons_box(self, parent=None):
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(10)

        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)

        # use AB.AquaButton
        tsize = (32, 32)
        bmp_delete = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR, tsize)
        bmp_cut = wx.ArtProvider.GetBitmap(wx.ART_CUT, wx.ART_OTHER, tsize)
        self.bmp_plus = bmp_plus = wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_TOOLBAR, tsize)
        bmp_new = wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, tsize)
        self.bmp_save = bmp_save = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_OTHER, tsize)
        bmp_close = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR, tsize)

        bsize = (20, 20)
        self.btn_delete = btn_delete = AB.AquaButton(self.panel_footer if not parent else parent, -1, bmp_cut,
                                                     "Delete Block", bsize)
        self.btn_save = btn_save = AB.AquaButton(self.panel_footer if not parent else parent, -1, bmp_save, "Save Block", bsize)
        btn_close = AB.AquaButton(self.panel_footer if not parent else parent, -1, bmp_close, "Close", bsize)

        self.btn_delete.SetForegroundColour(wx.BLACK)
        self.btn_save.SetForegroundColour(wx.BLACK)
        btn_close.SetForegroundColour(wx.BLACK)

        self.btn_delete.SetFont(font)
        self.btn_save.SetFont(font)
        btn_close.SetFont(font)

        self.btn_delete.SetMinSize(bsize)
        self.btn_save.SetMinSize(bsize)
        btn_close.SetMinSize(bsize)

        hbox_buttons.Add(btn_delete, proportion=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, border=10)
        hbox_buttons.Add(btn_save, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        hbox_buttons.Add(btn_close, proportion=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border=10)

        self.Bind(wx.EVT_BUTTON, self.OnDeleteClick, self.btn_delete)
        self.Bind(wx.EVT_BUTTON, self.OnSaveClick, self.btn_save)
        self.Bind(wx.EVT_BUTTON, self.OnCloseClick, btn_close)

        return hbox_buttons

    def define_toolbar(self):
        """
        Returns toolbar
        """
        toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        tsize = (32, 32)
        new_bmp = wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_TOOLBAR, tsize)
        save_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tsize)
        delete_bmp = wx.ArtProvider.GetBitmap(wx.ART_CUT, wx.ART_TOOLBAR, tsize)
        close_bmp = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR, tsize)

        toolbar.SetToolBitmapSize(tsize)

        # trick: display tool buttons to the right...
        st = wx.StaticText(toolbar, label='', size=(800, -1))
        toolbar.AddControl(st)

        toolbar.AddSimpleTool(1, new_bmp, 'Create Block', '')
        toolbar.AddSimpleTool(2, save_bmp, 'Save Block', '')
        toolbar.AddSimpleTool(3, delete_bmp, 'Delete Block', '')
        toolbar.AddSeparator()
        toolbar.AddSimpleTool(4, close_bmp, 'Exit', '')
        toolbar.Realize()

        self.Bind(wx.EVT_TOOL, self.OnToolCreateClick, id=1)
        self.Bind(wx.EVT_TOOL, self.OnToolSaveClick, id=2)
        self.Bind(wx.EVT_TOOL, self.OnToolDeleteClick, id=3)
        self.Bind(wx.EVT_TOOL, self.OnToolCloseClick, id=4)

        return toolbar

    def OnToolCreateClick(self, event):
        option = self.panel_config.get_option()

        if option['FILE'] == 'LOCAL':
            if option['TYPE'] == 'LOCAL':
                self.panel_config.tree.SelectItem(self.panel_config.local_file_local_root)
            elif option['TYPE'] == 'HPC':
                self.panel_config.tree.SelectItem(self.panel_config.local_file_hpc_root)
            else:
                self.panel_config.tree.SelectItem(self.panel_config.local_file_local_root)      # default
        elif option['FILE'] == 'GLOBAL':
            if option['TYPE'] == 'LOCAL':
                self.panel_config.tree.SelectItem(self.panel_config.global_file_local_root)
            elif option['TYPE'] == 'HPC':
                self.panel_config.tree.SelectItem(self.panel_config.global_file_hpc_root)
            else:
                self.panel_config.tree.SelectItem(self.panel_config.global_file_local_root)     # default

    def OnToolSaveClick(self, event):
        option = self.panel_config.get_option()

        if option['BLOCK']:
            self.save_block()
        else:
            self.create_block()

    def OnToolDeleteClick(self, event):
        self.delete_block()

    def OnToolCloseClick(self, event):
        self.Destroy()

    def OnCloseClick(self, event):
        self.Destroy()

    def OnSaveClick(self, event):
        option = self.panel_config.get_option()
        block_name = self.panel_edit.get_block_name()

        if block_name in ("", "DEFAULT", "NODE_GROUP", "PRIORITY"):
            print "The block needs to have a valid name!"
            return

        # save block
        self.panel_edit.OnSaveClick(event)

        if option['BLOCK']:
            self.panel_edit.refresh(option)

            # update status
            self.statusbar.SetStatusText('Block has been saved successfully!', 0)
        else:
            # refresh
            self.panel_config.Hide()
            self.panel_config.cleanup_controls()
            self.panel_config.build_tree_view()
            # self.Layout()
            self.panel_config.reset(option)
            self.refresh()
            self.panel_config.Show()
            self.Layout()

            option.update({'BLOCK': block_name})
            item = self.panel_config.locate_item(option)
            self.panel_config.set_selection(item)

            # update status
            self.statusbar.SetStatusText('Block has been created successfully!', 0)

    def save_block(self):
        option = self.panel_config.get_option()
        block_name = self.panel_edit.get_block_name()

        # save block
        self.panel_edit.save_create_block()

        # refresh ui
        self.panel_edit.refresh(option)

        # update status
        self.statusbar.SetStatusText("'%s' Block has been saved successfully!" % block_name, 0)

    def create_block(self):
        option = self.panel_config.get_option()
        block_name = self.panel_edit.get_block_name()

        # save block
        self.panel_edit.save_create_block()
        # refresh
        self.panel_config.Hide()
        self.panel_config.cleanup_controls()
        self.panel_config.build_tree_view()
        self.panel_config.reset(option)

        self.refresh()
        self.panel_config.Show()
        self.Layout()

        option.update({'BLOCK': block_name})
        item = self.panel_config.locate_item(option)
        self.panel_config.set_selection(item)

        # update status
        self.statusbar.SetStatusText('Block has been created successfully!', 0)

    def OnDeleteClick(self, event):
        self.delete_block()

    def delete_block(self):
        option = self.panel_config.get_option()
        question = "Are you sure you want to delete the block: %s" % option['BLOCK']
        dlg = wx.MessageDialog(self, question, 'Confirm deletion', wx.YES_NO | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_NO:
            return

        self.panel_edit.delete_block(option)

        # update status
        self.statusbar.SetStatusText('Block has been deleted successfully!', 0)

        # refresh
        self.panel_config.Hide()
        self.panel_config.cleanup_controls()
        self.panel_config.build_tree_view()
        self.panel_config.reset(option)
        self.panel_config.Show()
        self.refresh()
        self.Layout()

    def EvtRadioBox(self, event):
        self.refresh()

    def set_status(self, option):
        tip = self.panel_config.get_tooptip(option)
        # self.statusbar.SetStatusText(tip, 0)

        try:
            self.statusbar.SetStatusText(tip, 0)
        except:
            exit()

    def refresh(self):
        if self.panel_edit is None:
            return

        option = self.panel_config.get_option()
        self.panel_edit.refresh(option)
        self.set_status(option)
        self.refresh_toolbar(option)
        self.refresh_buttons(option)

    def refresh_buttons(self, option):
        if option:
            self.btn_save.Enable()

            ini_file = get_file_path(option['FILE'] == 'LOCAL')
            with open(ini_file, "r") as f:
                c = f.read()
                self.panel_content.SetValue(c)

            if option['TYPE']:
                self.btn_save.Show()
                if option['BLOCK']:
                    self.btn_save.SetLabel('Save Block')
                    self.btn_save.SetBitmapLabel(self.bmp_save)
                    self.btn_delete.Enable()
                    if option['BLOCK'] in ['LOCAL', 'HPC']:
                        self.btn_delete.Disable()
                    else:
                        self.btn_delete.Enable()
                else:
                    self.btn_save.SetLabel('Save Block')
                    self.btn_save.SetBitmapLabel(self.bmp_save)
                    self.btn_delete.Disable()
                self.panel_edit.Show()
                self.panel_content.Hide()
            else:
                self.btn_save.Disable()
                self.btn_delete.Disable()
                self.panel_edit.Hide()
                self.panel_content.Show()

            self.panel_view.Layout()
        else:
            self.btn_save.SetLabel('Save')
            self.btn_save.Disable()

    def refresh_toolbar(self, option):
        if option:
            if option['TYPE']:
                self.toolbar.EnableTool(2, True)
                if option['BLOCK']:
                    self.toolbar.EnableTool(3, True)

                    if option['BLOCK'] in ['LOCAL', 'HPC']:
                        self.toolbar.EnableTool(3, False)
                    else:
                        self.toolbar.EnableTool(3, True)
                else:
                    self.toolbar.EnableTool(3, False)
            else:
                self.toolbar.EnableTool(2, False)
                self.toolbar.EnableTool(3, False)
        else:
            pass

    def ShowTip(self):
        pass
