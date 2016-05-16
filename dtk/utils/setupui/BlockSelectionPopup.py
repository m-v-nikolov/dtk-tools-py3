import npyscreen


class BlockSelectionPopup(npyscreen.ActionFormMinimal):
    OK_BUTTON_TEXT = "Cancel"
    DEFAULT_LINES = 20
    DEFAULT_COLUMNS = 80
    SHOW_ATX = 10
    SHOW_ATY = 2

    def on_ok(self):
        self.exit_editing()

    def create(self):
        self.add(npyscreen.MultiLineEdit, max_height=3, editable=False,
                 value="Please choose the block to edit.\r\nThe (*) next to a name indicates the block is stored in the local ini file.", color='CURSOR')
        self.add(npyscreen.TitleMultiLine,name="LOCAL blocks:", max_height=5,
                        values=["BLOCK 1",
                                "BLOCK 2 (*)",
                                "CUSTOM 1",
                                "CUSTOM 2",
                                "CUSTOM 2",
                                "CUSTOM 2",
                                "CUSTOM 2",
                                ], scroll_exit=True)

        self.add(npyscreen.TitleMultiLine, name="HPC blocks:", max_height=5,
                 values=["BLOCK 4",
                         "BLOCK 5 (*)",
                         "BLOCK 6 (*)"
                         ], scroll_exit=True, rely=11)

        self.add_handlers({'^C': self.h_quit})

    def h_quit(self, item=None):
        exit()