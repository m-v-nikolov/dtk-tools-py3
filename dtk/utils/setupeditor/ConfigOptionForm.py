import wx
from simtools.SetupParser import SetupParser
from dtk.utils.setupeditor.utils import get_all_blocks


class ConfigOptionPanel(wx.Panel):
    """
    """

    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent

        self.tree = None
        self.root = None
        self.local_file_root = None
        self.global_file_root = None
        self.previously_selected = None             # [TODO]: may not need
        self.schema = SetupParser().load_schema()

        self.build_tree_view()
        self.refresh()

    def cleanup_controls(self):
        boxes = self.GetChildren()
        for box in boxes:
            box.Destroy()

    def build_tree_view(self):
        font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        # Retrieve the blocks
        local_blocks = get_all_blocks(True)
        global_blocks = get_all_blocks(False)

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.tree = wx.TreeCtrl(self, -1, wx.DefaultPosition, (-1, -1),
                                style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_NO_LINES)

        isz = (16, 16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
        rootidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_GO_HOME, wx.ART_OTHER, isz))
        localidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz))
        hpcidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_HARDDISK, wx.ART_OTHER, isz))
        blockidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

        self.tree.AssignImageList(il)

        self.root = root = self.tree.AddRoot('CONFIGURATION')
        self.tree.SetItemPyData(root, None)
        self.tree.SetItemTextColour(root, 'GOLD')

        self.tree.SetItemImage(root, rootidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(root, rootidx, wx.TreeItemIcon_Expanded)

        self.local_file_root = local_file_root = self.tree.AppendItem(root, 'LOCAL INI FILE')
        self.tree.SetItemPyData(local_file_root, {'FILE': 'LOCAL', 'TYPE': None})
        self.global_file_root = global_file_root = self.tree.AppendItem(root, 'GLOBAL INI FILE')
        self.tree.SetItemPyData(global_file_root, {'FILE': 'GLOBAL', 'TYPE': None})

        self.tree.SetItemTextColour(local_file_root, wx.BLUE)
        self.tree.SetItemBold(local_file_root)
        self.tree.SetItemTextColour(global_file_root, 'GOLD')
        self.tree.SetItemBold(global_file_root)

        self.tree.SetItemImage(local_file_root, fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(local_file_root, fldridx, wx.TreeItemIcon_Expanded)
        self.tree.SetItemImage(global_file_root, fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(global_file_root, fldridx, wx.TreeItemIcon_Expanded)

        self.local_file_local_root = local_file_local_root = self.tree.AppendItem(local_file_root, 'LOCAL BLOCKS')
        self.tree.SetItemPyData(local_file_local_root, {'FILE': 'LOCAL', 'TYPE': 'LOCAL'})
        self.local_file_hpc_root = local_file_hpc_root = self.tree.AppendItem(local_file_root, 'HPC BLOCKS')
        self.tree.SetItemPyData(local_file_hpc_root, {'FILE': 'LOCAL', 'TYPE': 'HPC'})

        self.tree.SetItemTextColour(local_file_local_root, wx.NamedColour("sea green"))   # 'GREEN')
        self.tree.SetItemTextColour(local_file_hpc_root, 'RED')

        self.tree.SetItemImage(local_file_local_root, localidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(local_file_local_root, localidx, wx.TreeItemIcon_Expanded)
        self.tree.SetItemImage(local_file_hpc_root, hpcidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(local_file_hpc_root, hpcidx, wx.TreeItemIcon_Expanded)

        self.global_file_local_root = global_file_local_root = self.tree.AppendItem(global_file_root, 'LOCAL BLOCKS')
        self.tree.SetItemPyData(global_file_local_root, {'FILE': 'GLOBAL', 'TYPE': 'LOCAL'})
        self.global_file_hpc_root = global_file_hpc_root = self.tree.AppendItem(global_file_root, 'HPC BLOCKS')
        self.tree.SetItemPyData(global_file_hpc_root, {'FILE': 'GLOBAL', 'TYPE': 'HPC'})

        self.tree.SetItemTextColour(global_file_local_root, 'sea green')
        self.tree.SetItemTextColour(global_file_hpc_root, 'RED')

        self.tree.SetItemImage(global_file_local_root, localidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(global_file_local_root, localidx, wx.TreeItemIcon_Expanded)
        self.tree.SetItemImage(global_file_hpc_root, hpcidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(global_file_hpc_root, hpcidx, wx.TreeItemIcon_Expanded)

        # local file
        local = self.tree.AppendItem(local_file_local_root, 'LOCAL')
        self.tree.SetItemBold(local)
        self.tree.SetItemPyData(local, {'FILE': 'LOCAL', 'TYPE': 'LOCAL'})
        self.tree.SetItemImage(local, blockidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(local, blockidx, wx.TreeItemIcon_Expanded)

        for block in local_blocks['LOCAL']:
            if block != 'LOCAL':
                node = self.tree.AppendItem(local_file_local_root, block)
                self.tree.SetItemPyData(node, {'FILE': 'LOCAL', 'TYPE': 'LOCAL'})

                self.tree.SetItemImage(node, blockidx, wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(node, blockidx, wx.TreeItemIcon_Expanded)

        hpc = self.tree.AppendItem(local_file_hpc_root, 'HPC')
        self.tree.SetItemBold(hpc)
        self.tree.SetItemPyData(hpc, {'FILE': 'LOCAL', 'TYPE': 'HPC'})
        self.tree.SetItemImage(hpc, blockidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(hpc, blockidx, wx.TreeItemIcon_Expanded)

        for block in local_blocks['HPC']:
            if block != 'HPC':
                node = self.tree.AppendItem(local_file_hpc_root, block)
                self.tree.SetItemPyData(node, {'FILE': 'LOCAL', 'TYPE': 'HPC'})

                self.tree.SetItemImage(node, blockidx, wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(node, blockidx, wx.TreeItemIcon_Expanded)

        # global file
        local = self.tree.AppendItem(global_file_local_root, 'LOCAL')
        self.tree.SetItemBold(local)
        self.tree.SetItemPyData(local, {'FILE': 'GLOBAL', 'TYPE': 'LOCAL'})
        self.tree.SetItemImage(local, blockidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(local, blockidx, wx.TreeItemIcon_Expanded)

        for block in global_blocks['LOCAL']:
            if block != 'LOCAL':
                node = self.tree.AppendItem(global_file_local_root, block)
                self.tree.SetItemPyData(node, {'FILE': 'GLOBAL', 'TYPE': 'LOCAL'})

                self.tree.SetItemImage(node, blockidx, wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(node, blockidx, wx.TreeItemIcon_Expanded)

        hpc = self.tree.AppendItem(global_file_hpc_root, 'HPC')
        self.tree.SetItemBold(hpc)
        self.tree.SetItemPyData(hpc, {'FILE': 'GLOBAL', 'TYPE': 'HPC'})
        self.tree.SetItemImage(hpc, blockidx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(hpc, blockidx, wx.TreeItemIcon_Expanded)

        for block in global_blocks['HPC']:
            if block != 'HPC':
                node = self.tree.AppendItem(global_file_hpc_root, block)
                self.tree.SetItemPyData(node, {'FILE': 'GLOBAL', 'TYPE': 'HPC'})

                self.tree.SetItemImage(node, blockidx, wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(node, blockidx, wx.TreeItemIcon_Expanded)

        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.tree.Bind(wx.EVT_TREE_ITEM_GETTOOLTIP, self.OnToolTip)

        vbox.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(vbox)

        self.tree.ExpandAll()

    def reset(self, option):
        if option['FILE'] == 'LOCAL':
            self.tree.SelectItem(self.local_file_root)
        else:
            self.tree.SelectItem(self.global_file_root)

    def set_selection(self, item):
        self.tree.SelectItem(item)

    def locate_item(self, option):
        file_root = self.local_file_root if option['FILE'] == 'LOCAL' else self.global_file_root
        item, cookie = self.tree.GetFirstChild(file_root)

        root = None
        if item.IsOk():
            if option['TYPE'] in self.tree.GetItemText(item):
                root = item

        item, cookie = self.tree.GetNextChild(file_root, cookie)
        if item.IsOk():
            if option['TYPE'] in self.tree.GetItemText(item):
                root = item

        if root is None:
            return None
        else:
            return self.find_item(option['BLOCK'], root)

    def find_item(self, match, root):
        item, cookie = self.tree.GetFirstChild(root)

        while item.IsOk():
            if self.tree.GetItemText(item) == match:
                return item

            item, cookie = self.tree.GetNextChild(root, cookie)

        return None

    def OnToolTip(self, event):
        node = event.GetItem()
        option = self.tree.GetItemPyData(node)
        if option is None:
            tip = 'DTK Configurations'
        else:
            option.update({'LABEL': self.get_label_selection(node), 'BLOCK': self.get_block_selection(node)})
            tip = self.get_tooptip(option)

        event.SetToolTip(tip)

    def get_tooptip(self, option):
        tip = ''
        if option is None:
            tip = 'DTK Configurations'
        elif option['TYPE'] is None:
            tip = '%s INI File In Raw Format' % option['FILE']
        elif option['BLOCK'] is None:
            tip = 'Create New Blocks'
        else:
            if option['BLOCK'] in ['LOCAL', 'HPC']:
                tip = 'Modify Block'
            else:
                tip = 'Modify or Delete Block'

        return tip

    def change_selected_color(self, event):
        item = event.GetItem()
        if self.previously_selected:
            color = 'black'
            if self.previously_selected == self.local_file_root:
                color = 'blue'
            elif self.previously_selected == self.global_file_root:
                color = 'gold'
            elif self.previously_selected == self.local_file_local_root:
                color = 'sea green'
            elif self.previously_selected == self.local_file_hpc_root:
                color = 'red'
            elif self.previously_selected == self.global_file_local_root:
                color = 'sea green'
            elif self.previously_selected == self.global_file_hpc_root:
                color = 'red'

            self.tree.SetItemTextColour(self.previously_selected, color)

        self.previously_selected = item
        self.tree.SetItemTextColour(item, 'brown')

    def OnSelChanged(self, event):
        # self.change_selected_color(event)

        self.refresh()
        self.parent.EvtRadioBox(event)

    def get_label(self):
        item = self.tree.GetSelection()
        return self.get_label_selection(item)

    def get_label_selection(self, item):
        return self.tree.GetItemText(item)

    def get_type(self):
        item = self.tree.GetSelection()
        return self.get_type_selection(item)

    def get_type_selection(self, node):
        data = self.tree.GetItemPyData(node)
        return data['TYPE'] if data else None

    def get_block(self):
        item = self.tree.GetSelection()
        return self.get_block_selection(item)

    def get_block_selection(self, node):
        (child, cookie) = self.tree.GetFirstChild(node)
        return None if child.IsOk() else self.tree.GetItemText(node)

    def get_option(self):
        item = self.tree.GetSelection()
        if item is None:
            return None

        if not item.IsOk():
            return

        # print self.tree.GetItemText(item)
        data = self.tree.GetItemPyData(item)
        if data is None:
            return None

        data.update({'LABEL': self.get_label_selection(item), 'BLOCK': self.get_block_selection(item)})

        return data

    def refresh(self):
        pass

