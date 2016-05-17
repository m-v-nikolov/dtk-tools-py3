import npyscreen

from utils.setupui.BlockSelectionPopup import BlockSelectionPopup
from utils.setupui.ConfigTypePopup import ConfigTypePopup
from utils.setupui.MenuForm import MenuForm


class ConfigSelectionForm(npyscreen.FormBaseNew, MenuForm):
    """
    Form representing the main menu of the application.
    Displays the title and a menu allowing to access the different features.
    """

    def create(self):
        """
        Initialization of the form.
        """

        # Display the ASCII title
        self.add(npyscreen.FixedText, editable=False, value=" ____    ______  __  __          ______                ___ ")
        self.add(npyscreen.FixedText, editable=False, value="/\\  _`\\ /\\__  _\\/\\ \\/\\ \\        /\\__  _\\              /\\_ \\")
        self.add(npyscreen.FixedText, editable=False, value="\\ \\ \\/\\ \\/_/\\ \\/\\ \\ \\/'/'       \\/_/\\ \\/   ___     ___\\//\\ \\     ____  ")
        self.add(npyscreen.FixedText, editable=False, value=" \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ , <    _______\\ \\ \\  / __`\\  / __`\\\\ \\ \\   /',__\\ ")
        self.add(npyscreen.FixedText, editable=False, value="  \\ \\ \\_\\ \\ \\ \\ \\ \\ \\ \\\\`\\ /\\______\\\\ \\ \\/\\ \\L\\ \\/\\ \\L\\ \\\\_\\ \\_/\\__, `\\")
        self.add(npyscreen.FixedText, editable=False, value="   \\ \\____/  \\ \\_\\ \\ \\_\\ \\_\\/______/ \\ \\_\\ \\____/\\ \\____//\\____\\/\\____/")
        self.add(npyscreen.FixedText, editable=False, value="    \\/___/    \\/_/  \\/_/\\/_/          \\/_/\\/___/  \\/___/ \\/____/\\/___/")
        self.add(npyscreen.FixedText, editable=False, value="Configuration script for dtk-tools", relx=9)

        # Create the menu
        menu = self.add(npyscreen.SelectOne, max_height=5, value=[0],
                      values=["CHANGE THE GLOBAL DEFAULT BLOCKS",
                              "CHANGE THE LOCAL DEFAULT BLOCKS",
                              "NEW CONFIGURATION BLOCK",
                              "EDIT CONFIGURATION BLOCK",
                              "QUIT"], scroll_exit=True, rely=12)
        self.set_menu_handlers(menu, self.h_select_menu)

        # Add handlers to quick the app when Ctrl+C is pushed
        self.add_handlers({'^C': self.h_quit})

    def h_quit(self, item=None):
        """
        Function called when Ctrl+c pushed -> exit the program:
        """
        npyscreen.blank_terminal()
        exit()

    def h_select_menu(self, item):
        """
        Callback when a menu item is selected.
        Depending on the selected item redirect to correct form.
        :param item: The selected item
        """
        # Extract the value
        val = self.menu.value[0]

        # CHANGE THE GLOBAL DEFAULT BLOCKS selected
        # Set the type to global and display the default selection form
        if val == 0:
            self.parentApp.getForm('DEFAULT_SELECTION').type = "GLOBAL"
            self.parentApp.change_form('DEFAULT_SELECTION')
            return

        # CHANGE THE LOCAL DEFAULT BLOCKS selected
        # Set the type to local and display the default selection form
        if val == 1:
            self.parentApp.getForm('DEFAULT_SELECTION').type = "LOCAL"
            self.parentApp.change_form('DEFAULT_SELECTION')
            return

        # NEW CONFIGURATION BLOCK selected
        # Display the popup to choose between HPC and LOCAL
        # Pass the choice to the creation form
        if val == 2:
            popup = ConfigTypePopup()
            popup.edit()
            if popup.value:
                self.parentApp.getForm('EDIT').type = popup.value
                self.parentApp.change_form('EDIT')
            return

        # EDIT CONFIGURATION BLOCK selected
        # Display the popup to select the block to edit
        # Pass the selected block to the edition form
        if val == 3:
            popup = BlockSelectionPopup()
            popup.edit()
            return

        # QUIT selected
        # simply exit
        self.h_quit()

