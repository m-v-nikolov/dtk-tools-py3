import npyscreen

from utils.setupui.MenuForm import MenuForm


class ConfigTypePopup(npyscreen.FormBaseNew, MenuForm):
    DEFAULT_LINES = 9
    DEFAULT_COLUMNS = 60
    SHOW_ATX = 10
    SHOW_ATY = 2

    def create(self):
        self.color = 'STANDOUT'
        self.add(npyscreen.MultiLineEdit, max_height=2, editable=False, value = "Please choose the type of configuration:", color='CURSOR')
        menu = self.add(npyscreen.SelectOne, max_height=3, value=[0],
                 values=["HPC CONFIGURATION",
                         "LOCAL CONFIGURATION"], scroll_exit=False)

        self.set_menu_handlers(menu)

    def h_select_menu(self, item):
        self.value = "HPC" if self.menu.value[0] == 0 else "LOCAL"
        self.exit_editing()
