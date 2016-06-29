import curses

import npyscreen
import operator

from dtk.utils.setupui.utils import get_all_blocks


class BlockSelectionPopup(npyscreen.ActionFormMinimal):
    """
    Form representing the popup to select a block to edit
    """
    OK_BUTTON_TEXT = "Cancel"
    DEFAULT_LINES = 25
    DEFAULT_COLUMNS = 80
    SHOW_ATX = 10
    SHOW_ATY = 2

    def on_ok(self):
        self.exit_editing()

    def h_select_hpc_block(self,item):
        """
        Called when the user select a HPC block to edit
        Store the selected block in self.value and exit
        """
        self.block = self.hpc_selection.values[self.hpc_selection.entry_widget.cursor_line]
        self.exit_editing()

    def h_select_local_block(self, item):
        """
        Called when the user select a LOCAL block to edit
        Store the selected block in self.value and exit
        """
        self.block = self.local_selection.values[self.local_selection.entry_widget.cursor_line]
        self.exit_editing()

    def create(self):
        """
        Initialization of the form
        """
        self.block = None
        # Add some explanation text
        self.add(npyscreen.MultiLineEdit, max_height=3, editable=False,
                 value="Please choose the block to edit.\r\nThe (*) next to a name indicates the block is stored in the local ini file.", color='CURSOR')

        # Retrieve the blocks
        local_blocks = get_all_blocks(True)
        global_blocks = get_all_blocks(False)

        # Add the (*) for local blocks
        map(lambda  key: operator.setitem(local_blocks,key,["%s (*)" % a for a in local_blocks[key]]), local_blocks.keys())

        # Merge the global blocks inside of the local_blocks
        map(lambda key: operator.setitem(local_blocks, key, local_blocks[key] + global_blocks[key]), local_blocks.keys())

        # Add the local blocks selection
        self.local_selection = self.add(npyscreen.TitleMultiLine,name="LOCAL blocks:", max_height=8, scroll_exit=True,
                                        values = sorted(local_blocks['LOCAL']))

        # Add the HPC block selection
        self.hpc_selection = self.add(npyscreen.TitleMultiLine, name="HPC blocks:", max_height=8,
                                      scroll_exit=True, rely=14, values= sorted(local_blocks['HPC']))

        self.local_selection.add_handlers({curses.ascii.CR: self.h_select_local_block})
        self.hpc_selection.add_handlers({curses.ascii.CR: self.h_select_hpc_block})
