import npyscreen

from utils.setupui.BlockSelectionPopup import BlockSelectionPopup
from utils.setupui.ConfigTypePopup import ConfigTypePopup
from utils.setupui.MenuForm import MenuForm


class ConfigSelectionForm(npyscreen.FormBaseNew, MenuForm):
    def create(self):
        self.add(npyscreen.FixedText, editable=False, value=" ____    ______  __  __          ______                ___ ")
        self.add(npyscreen.FixedText, editable=False, value="/\\  _`\\ /\\__  _\\/\\ \\/\\ \\        /\\__  _\\              /\\_ \\")
        self.add(npyscreen.FixedText, editable=False, value="\\ \\ \\/\\ \\/_/\\ \\/\\ \\ \\/'/'       \\/_/\\ \\/   ___     ___\\//\\ \\     ____  ")
        self.add(npyscreen.FixedText, editable=False, value=" \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ , <    _______\\ \\ \\  / __`\\  / __`\\\\ \\ \\   /',__\\ ")
        self.add(npyscreen.FixedText, editable=False, value="  \\ \\ \\_\\ \\ \\ \\ \\ \\ \\ \\\\`\\ /\\______\\\\ \\ \\/\\ \\L\\ \\/\\ \\L\\ \\\\_\\ \\_/\\__, `\\")
        self.add(npyscreen.FixedText, editable=False, value="   \\ \\____/  \\ \\_\\ \\ \\_\\ \\_\\/______/ \\ \\_\\ \\____/\\ \\____//\\____\\/\\____/")
        self.add(npyscreen.FixedText, editable=False, value="    \\/___/    \\/_/  \\/_/\\/_/          \\/_/\\/___/  \\/___/ \\/____/\\/___/")
        self.add(npyscreen.FixedText, editable=False, value="Configuration script for dtk-tools", relx=9)

        menu = self.add(npyscreen.SelectOne, max_height=5, value=[0],
                      values=["CHANGE THE GLOBAL DEFAULT BLOCKS",
                              "CHANGE THE LOCAL DEFAULT BLOCKS",
                              "NEW CONFIGURATION BLOCK",
                              "EDIT CONFIGURATION BLOCK",
                              "QUIT"], scroll_exit=True, rely=12)

        self.set_menu_handlers(menu)

        self.add_handlers({'^C': self.h_quit})

    def h_quit(self, item=None):
        exit()

    def h_select_menu(self, item):
        if self.menu.value[0] == 0:
            self.parentApp.getForm('DEFAULT_SELECTION').type = "GLOBAL"
            self.parentApp.change_form('DEFAULT_SELECTION')
            return

        if self.menu.value[0] == 1:
            self.parentApp.getForm('DEFAULT_SELECTION').type = "LOCAL"
            self.parentApp.change_form('DEFAULT_SELECTION')
            return

        if self.menu.value[0] == 2:
            popup = ConfigTypePopup()
            popup.edit()
            self.parentApp.getForm('EDIT').type = popup.value
            self.parentApp.change_form('EDIT')
            return

        if self.menu.value[0] == 3:
            popup = BlockSelectionPopup()
            popup.edit()
            return

        elif self.menu.value[0] == 1 or self.menu.value[0] == 3 or self.menu.value[0] == 5:
            self.parentApp.getForm('EDIT').type = "LOCAL"
        else:
            self.parentApp.getForm('EDIT').type = "HPC"

        self.parentApp.change_form('EDIT')

