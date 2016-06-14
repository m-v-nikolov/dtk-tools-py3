import npyscreen

from BlockSelectionPopup import BlockSelectionPopup
from ConfigTypePopup import ConfigTypePopup
from MenuForm import MenuForm
from dtk.utils.setupui.utils import get_file_path


class MainMenuForm(npyscreen.FormBaseNew, MenuForm):
    """
    Form representing the main menu of the application.
    Displays the title and a menu allowing to access the different features.
    """
    DEFAULT_X_OFFSET = 4

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
        self.add(npyscreen.FixedText, editable=False, value="Configuration Application", relx=9)

        # Create the menu
        self.add(npyscreen.TitleText, editable=False, name="MAIN MENU", rely=12)
        menu = self.add(npyscreen.SelectOne, max_height=6, value=[0],
                      values=["CHANGE THE DEFAULT LOCAL CONFIGURATION",
                              "CHANGE THE DEFAULT HPC CONFIGURATION",
                              "NEW CONFIGURATION BLOCK",
                              "EDIT CONFIGURATION BLOCKS",
                              "QUIT"], scroll_exit=True, rely=13)

        self.set_menu_handlers(menu, self.h_select_menu)

        # Add handlers to quick the app when Ctrl+C is pushed
        self.add_handlers({'^C': self.h_quit})

        # Add the paths for information
        self.add(npyscreen.TitleText, editable=False, name="Local ini path", value=get_file_path(True), use_two_lines = True, begin_entry_at=0, rely=19)
        self.add(npyscreen.TitleText, editable=False, name="Global ini path", value=get_file_path(False), use_two_lines = True, begin_entry_at=0, rely=22)

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

        # CHANGE THE DEFAULT LOCAL CONFIGURATION selected
        # Edit the global LOCAL block
        if val == 0:
            self.parentApp.getForm('EDIT').set_block('LOCAL')
            self.parentApp.change_form('EDIT')
            return

        # CHANGE THE DEFAULT HPC CONFIGURATION selected
        # Edit the global HPC block
        if val == 1:
            self.parentApp.getForm('EDIT').set_block('HPC')
            self.parentApp.change_form('EDIT')
            return

        # NEW CONFIGURATION BLOCK selected
        # Display the popup to choose between HPC and LOCAL
        # Pass the choice to the creation form
        if val == 2:
            popup = ConfigTypePopup()
            popup.edit()
            if popup.value:
                self.parentApp.getForm('EDIT').type = popup.value
                self.parentApp.getForm('EDIT').set_block(None)
                self.parentApp.change_form('EDIT')
            return

        # EDIT CONFIGURATION BLOCK selected
        # Display the popup to select the block to edit
        # Pass the selected block to the edition form
        if val == 3:
            popup = BlockSelectionPopup()
            popup.edit()
            if popup.block:
                self.parentApp.getForm('EDIT').set_block(popup.block)
                self.parentApp.change_form('EDIT')
            return

        # QUIT selected
        # simply exit
        self.h_quit()

