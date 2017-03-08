import os
import wx
from dtk.utils.setupeditor.utils import add_block, get_block, delete_block
from simtools.SetupParser import SetupParser
import wx.lib.scrolledpanel as scrolled


class ConfigEditPanel(scrolled.ScrolledPanel):
    """"""

    def __init__(self, parent):
        """Constructor"""
        scrolled.ScrolledPanel.__init__(self, parent=parent)

        self.parent = parent
        self.schema = SetupParser().load_schema()
        self.block = None
        self.type = "LOCAL"
        self.global_defaults = True

        self.fields = dict()
        self.labels = dict()
        self.helps = dict()

        self.SetAutoLayout(1)

    def cleanup_controls(self):
        boxes = self.GetChildren()
        for box in boxes:
            box.Destroy()

        self.SetAutoLayout(1)

    def populate_editor(self):

        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        # Display a name field
        definitions = [
            {"type": "string", "label": "Block name", "help": "Name for the configuration block.", "name": "name"}]

        # Display a name field
        box1 = self.create_fields(definitions)
        # No matter what create the common fields
        box2 = self.create_fields(self.schema['COMMON'])
        # Then display the extra fields depending on the type
        box3 = self.create_fields(self.schema[self.type])

        # main vertial box
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(box1, flag=wx.EXPAND)
        vbox.Add(box2, flag=wx.EXPAND)
        vbox.Add(box3, flag=wx.EXPAND)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)
        self.SetupScrolling()

        # If we are editing global default -> make name it readonly
        if self.fields['name'].GetValue() in ['LOCAL', 'HPC']:
            self.fields['name'].SetEditable(False)
            self.fields['name'].SetBackgroundColour('grey')

    def EvtCheckBox(self, event):
        cb = event.GetEventObject()
        self.h_asset_svc_toggled()
        self.Layout()
        self.SetupScrolling(scroll_x=True, scroll_y=True, scrollToTop=False)
        self.ScrollChildIntoView(cb)

    def onFocus(self, event):
        cb = event.GetEventObject()
        print '%s got focus' % cb.GetName()
        if self.helps[cb.GetName()]:
            self.helps[cb.GetName()].Show()
            self.Layout()
            self.SetupScrolling(scroll_x=True, scroll_y=True, scrollToTop=False)

        self.ScrollChildIntoView(cb)

        # workaround for wx.Choice. Otherwise, it won't expand!
        event.Skip()

    def onKillFocus(self, event):
        cb = event.GetEventObject()
        print '%s leave focus' % cb.GetName()
        if self.helps[cb.GetName()]:
            self.helps[cb.GetName()].Hide()
            self.Layout()
            self.SetupScrolling(scroll_x=True, scroll_y=True, scrollToTop=False)

        self.ScrollChildIntoView(cb)

        event.Skip()

    def onMouseOver(self, event):
        cb = event.GetEventObject()
        self.helps[cb.GetName()].Show()
        self.Layout()

    def onMouseLeave(self, event):
        cb = event.GetEventObject()
        self.helps[cb.GetName()].Hide()
        self.Layout()

    def refresh(self, option):
        self.Hide()
        self.cleanup_controls()
        self.fields = dict()
        self.labels = dict()
        self.helps = dict()

        if option is None:
            pass
        else:
            self.set_block(option)

            try:
                self.populate_editor()
            except:
                # print 'DTK Setup Editor catch exception, existing...'
                # exc_info = sys.exc_info()
                # print exc_info
                exit()

            if option['BLOCK']:
                pass
            else:
                if option['TYPE'] and option['TYPE'] == 'HPC':
                    self.fields['use_comps_asset_svc'].SetValue(1)
                    self.fields['compress_assets'].SetValue(1)
                    self.h_asset_svc_toggled()

        self.Show()

    def OnButton_file(self, evt):
        ob = evt.GetEventObject()
        wildcard = "Python source (*.py)|*.py|" \
                   "Compiled Python (*.pyc)|*.pyc|" \
                   "SPAM files (*.spam)|*.spam|" \
                   "Egg file (*.egg)|*.egg|" \
                   "All files (*.*)|*.*"

        dlg = wx.FileDialog(
            None, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
        )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            ctl = self.fields[ob.GetName()]
            ctl.SetValue(path)

        dlg.Destroy()

    def OnButton_dir(self, evt):
        ob = evt.GetEventObject()
        dlg = wx.DirDialog(None, "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE
                           )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            ctl = self.fields[ob.GetName()]
            ctl.SetValue(path)

        dlg.Destroy()

    def set_block(self, option):
        self.global_defaults = option['FILE'] == 'LOCAL'
        if option['BLOCK']:
            self.type = option['TYPE']
            self.block = get_block(option['BLOCK'], self.global_defaults)
        else:
            if option['TYPE']:
                self.type = option['TYPE']
                self.block = None
            else:
                pass

    def delete_block(self, option):
        delete_block(option['BLOCK'], option['FILE'] == 'LOCAL')

        # Display message box
        wx.MessageBox("The block %s has been removed from the %s ini file." % (option['BLOCK'], option['FILE']), 'Confirmation')

    def OnSaveClick(self, event):
        self.save_create_block()

    def save_create_block(self):
        self.save_to_file(self.global_defaults)

    def get_block_name(self):
        value = self.fields['name'].GetStringSelection() if isinstance(self.fields['name'], wx.RadioBox) else self.fields['name'].GetValue()
        block_name = value.upper().replace(' ', '_')
        return block_name

    def save_to_file(self, local_file):
        value = self.fields['name'].GetStringSelection() if isinstance(self.fields['name'], wx.RadioBox) else self.fields['name'].GetValue()
        block_name = value.upper().replace(' ', '_')

        if block_name in ("", "DEFAULT", "NODE_GROUP", "PRIORITY"):
            print "The block needs to have a valid name!"
            return

        if self.block:
            message = "LOCAL" if self.block['location'] == 'LOCAL' else "GLOBAL"
        else:
            message = "LOCAL" if local_file else "GLOBAL"

        # Add/edit the block
        block_name = add_block(block_type=self.type, local=local_file, fields=self.fields)
        # Display message box
        wx.MessageBox("The configuration block %s has been saved successfully in the %s INI file." % (block_name, message), 'Confirmation')

    def h_asset_svc_toggled(self):
        """
        When the comps asset service is toggled, hide/show the exe_path/dll_path
        """
        asset_svc = True
        if 'use_comps_asset_svc' in self.fields:
            asset_svc = self.fields['use_comps_asset_svc'].GetValue()

        if asset_svc:
            self.fields['exe_path'].Hide()
            self.fields['dll_path'].Hide()
            self.labels['exe_path'].Hide()
            self.labels['dll_path'].Hide()
            self.Layout()
        else:
            self.fields['exe_path'].Show()
            self.fields['dll_path'].Show()
            self.labels['exe_path'].Show()
            self.labels['dll_path'].Show()
            self.Layout()

    def define_help_panel(self, info):
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        bmp_kill = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR, (15, 15))

        panel_help = wx.Panel(self, -1)

        st = wx.StaticText(panel_help, label=info)
        st.SetFont(font)
        st.SetForegroundColour('brown')

        # wx.BORDER_NONE only works for BitmapButton
        btn_kill = wx.BitmapButton(panel_help, id=wx.ID_ANY, bitmap=bmp_kill,
                                      size=(bmp_kill.GetWidth(), bmp_kill.GetHeight()), style=wx.BORDER_NONE)

        vbox_help = wx.BoxSizer(wx.HORIZONTAL)
        vbox_help.Add(st, proportion=1, flag=wx.EXPAND)
        vbox_help.Add(btn_kill, proportion=0, flag=wx.EXPAND | wx.ALIGN_RIGHT)
        panel_help.SetSizer(vbox_help)

        return panel_help

    def create_fields(self, definitions):
        """
        """
        # main vertical box
        vbox = wx.BoxSizer(wx.VERTICAL)
        b = 5
        color = 'dark green'
        hlp_color = 'brown'
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        # Browse through the definitions and create the correct wx controls
        for field in definitions:
            field_type = field['type']

            hlp = None
            lbl = None
            ctl = None

            # Retrieve the current value if present
            value = self.block[field['name']] if self.block and self.block.has_key(field['name']) else None
            info = field['help'] if field['help'] else ''

            vbox2 = wx.BoxSizer(wx.VERTICAL)
            if field_type == "string" or field_type == "url":

                vbox3 = wx.BoxSizer(wx.VERTICAL)

                st = wx.StaticText(self, label=field['label'])
                st.SetForegroundColour(color)
                st.SetFont(font)
                vbox3.Add(st, flag=wx.LEFT, border=b)

                panel_help = self.define_help_panel(info)
                vbox3.Add(panel_help, proportion=1, flag=wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT | wx.LEFT, border=b)

                if field['name'] == 'environment':
                    envList = ['Belegost', 'LSHTMcloud', 'NDcloud', 'UCIcloud']
                    ch = wx.Choice(self, -1, (100, 50), choices=envList)
                    if value:
                        ch.SetStringSelection(value)
                    else:
                        ch.SetStringSelection('Belegost')

                    ch.SetToolTip(wx.ToolTip(info))
                    ctl = ch
                    vbox3.Add(ch, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=b)

                else:
                    tc = wx.TextCtrl(self)
                    tc.SetValue(value if value else '')
                    tc.SetToolTip(wx.ToolTip(info))
                    ctl = tc
                    vbox3.Add(tc, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=b)

                vbox2.Add(vbox3, proportion=0, flag=wx.EXPAND)

                hlp = panel_help
                lbl = st

            elif field_type == "int":
                vbox3 = wx.BoxSizer(wx.VERTICAL)

                # Slider for int
                st = wx.StaticText(self, -1, field['label'], (45, 15))
                st.SetForegroundColour(color)
                st.SetFont(font)
                vbox3.Add(st, flag=wx.LEFT, border=b)

                panel_help = self.define_help_panel(info)
                vbox3.Add(panel_help, proportion=1, flag=wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT | wx.LEFT, border=b)

                spt = wx.SpinCtrl(self, -1, "", (30, 50))
                spt.SetFont(font)
                spt.SetRange(int(field['min']), int(field['max']))
                spt.SetValue(int(value) if value else int(field['default']))
                spt.SetToolTip(wx.ToolTip(info))

                vbox3.Add(spt, proportion=1, flag=wx.LEFT | wx.RIGHT, border=b)
                vbox2.Add(vbox3, flag=wx.EXPAND)

                ctl = spt
                lbl = st
                hlp = panel_help

            elif field_type == "file" or field_type == "directory":
                # If we are working with HPC block -> no browsing of directory so display simple strings
                if self.type == "HPC":
                    vbox3 = wx.BoxSizer(wx.VERTICAL)
                    st = wx.StaticText(self, label=field['label'])
                    st.SetForegroundColour(color)
                    st.SetFont(font)
                    vbox3.Add(st, flag=wx.LEFT, border=b)

                    panel_help = self.define_help_panel(info)
                    vbox3.Add(panel_help, proportion=1, flag=wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT | wx.LEFT, border=b)

                    tc = wx.TextCtrl(self, name=field['name'])
                    tc.SetValue(value if value else '')
                    vbox3.Add(tc, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=b)
                    vbox2.Add(vbox3, flag=wx.EXPAND)

                    tc.SetToolTip(wx.ToolTip(info))
                    ctl = tc
                    lbl = st
                    hlp = panel_help

                else:
                    # File picker for file and directory
                    vbox3 = wx.BoxSizer(wx.VERTICAL)
                    st = wx.StaticText(self, label=field['label'])
                    st.SetForegroundColour(color)
                    st.SetFont(font)
                    vbox3.Add(st, flag=wx.LEFT, border=b)

                    panel_help = self.define_help_panel(info)
                    vbox3.Add(panel_help, proportion=1, flag=wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT | wx.LEFT, border=b)

                    hbox = wx.BoxSizer(wx.HORIZONTAL)
                    tc = wx.TextCtrl(self, name=field['name'])
                    tc.SetValue(value if value else '')

                    btn = wx.Button(self, -1, "...")
                    btn.SetName(field['name'])

                    hbox.Add(tc, proportion=1, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=b)
                    hbox.Add(btn, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=b)

                    vbox2.Add(vbox3, flag=wx.EXPAND)
                    vbox2.Add(hbox, flag=wx.EXPAND)

                    if field_type == "file":
                        self.Bind(wx.EVT_BUTTON, self.OnButton_file, btn)
                    elif field_type == "directory":
                        self.Bind(wx.EVT_BUTTON, self.OnButton_dir, btn)

                    tc.SetToolTip(wx.ToolTip(info))
                    ctl = tc
                    lbl = st
                    hlp = panel_help

            elif field_type == "bool":
                # Checkbox for bool
                vbox3 = wx.BoxSizer(wx.VERTICAL)

                panel_help = self.define_help_panel(info)
                vbox3.Add(panel_help, proportion=1, flag=wx.EXPAND | wx.ALIGN_LEFT | wx.RIGHT | wx.LEFT, border=b)

                ck = wx.CheckBox(self, label=field['label'])
                self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, ck)

                ck.SetFont(font)
                ck.SetValue(value == '1')
                ck.SetToolTip(wx.ToolTip(info))
                vbox3.Add(ck, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=b)
                vbox2.Add(vbox3, flag=wx.EXPAND)

                ctl = ck
                hlp = panel_help

            elif field_type == "radio":
                vbox3 = wx.BoxSizer(wx.VERTICAL)

                rb = wx.RadioBox(self, -1, field['label'], wx.DefaultPosition,
                                 size=wx.DefaultSize, choices=field['choices'],
                                 majorDimension=len(field['choices']), style=wx.RA_SPECIFY_ROWS)
                rb.SetFont(font)
                rb.SetSelection(0 if not value else field['choices'].index(value))
                vbox3.Add(rb, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=b)

                vbox2.Add(vbox3, flag=wx.EXPAND)

                rb.SetToolTip(wx.ToolTip(info))
                ctl = rb

            if lbl:
                lbl.SetForegroundColour('sea green')

            # default
            if hlp:
                hlp.Hide()
                hlp.SetFont(font)
                hlp.SetForegroundColour(hlp_color)

            if ctl:
                ctl.SetName(field['name'])

                if field['name'] not in ['environment', 'compress_assets', 'use_comps_asset_svc']:
                    ctl.Bind(wx.EVT_SET_FOCUS, self.onFocus)
                    ctl.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)

            self.fields[field['name']] = ctl
            self.labels[field['name']] = lbl
            self.helps[field['name']] = hlp

            vbox.Add(vbox2, flag=wx.EXPAND)

        return vbox