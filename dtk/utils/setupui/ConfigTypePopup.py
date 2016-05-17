import npyscreen

from utils.setupui.MenuForm import MenuForm


class ConfigTypePopup(npyscreen.ActionFormMinimal, MenuForm):
    """
    Form representing the popup to select a configuration type (HPC/LOCAL)
    """
    DEFAULT_LINES = 9
    DEFAULT_COLUMNS = 60
    SHOW_ATX = 10
    SHOW_ATY = 2
    OK_BUTTON_TEXT = "Cancel"

    def on_ok(self):
        """
        If we click on "Cancel" exit the form
        The function is on_ok because ActionFormMinimal is a one button form (usually OK) where we renamed OK into Cancel
        """
        self.exit_editing()

    def create(self):
        """
        Initialization of the form
        """
        # Initialize the value
        self.value = None

        # Change the form color
        self.color = 'STANDOUT'

        # Add some explanation text
        self.add(npyscreen.MultiLineEdit, max_height=2, editable=False, value = "Please choose the type of configuration:", color='CURSOR')

        # And a menu
        menu = self.add(npyscreen.SelectOne, max_height=3, value=[0],
                 values=["HPC CONFIGURATION",
                         "LOCAL CONFIGURATION"], scroll_exit=False)

        self.set_menu_handlers(menu, self.h_select_menu)

    def h_select_menu(self, item):
        """
        Called when the user select an item
        Store the selected value in self.value and exit
        """
        self.value = "HPC" if self.menu.value[0] == 0 else "LOCAL"
        self.exit_editing()
