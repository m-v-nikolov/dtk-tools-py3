import npyscreen


class DefaultBlockSelectionForm(npyscreen.ActionFormV2):
    """
    Form allowing the user to select default blocks.
    self.type holds GLOBAL or LOCAL and define if we are editing the default in the GLOBAL config file
    or on the local directory ini.
    """

    # First rename the Ok and Cancel buttons
    OK_BUTTON_TEXT = "Save"
    CANCEL_BUTTON_TEXT = "Return to menu"

    def on_cancel(self):
        """
        Called when the "Return to menu" button is clicked
        Return to menu -> Go back to the previous form
        """
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        """
        Called when the "Save" button is clicked
        Save the default, display a message and return to the main menu
        """
        npyscreen.notify_confirm("The defaults have been saved!", title='Success!')
        self.parentApp.switchFormPrevious()

    def create(self):
        """
        Initialization of the form
        """
        # By default assume we are editing the GLOBAL defaults
        self.type="GLOBAL"

        # Add some text to explain
        self.add(npyscreen.MultiLineEdit, editable=False, max_height=2, value="On this page you can change the default block used by default for both LOCAL and\r\nHPC configurations.")
        self.notice = self.add(npyscreen.MultiLineEdit, color='STANDOUT', editable=False, max_height=1)

        # List the LOCAL blocks
        local = self.add(npyscreen.TitleSelectOne, rely=6, return_exit=True, select_exit=True, scroll_exit = True,
                         name="Default LOCAL configuration:", use_two_lines=False, begin_entry_at=30, max_height=5, values=['MY_BLOCK','BLOCK2','BLOCK5'])

        # List the HPC blocks
        hpc = self.add(npyscreen.TitleSelectOne,  rely=local.rely+2+len(local.values), return_exit=True, select_exit=True, scroll_exit = True,
                 name="Default HPC configuration:", use_two_lines=False, begin_entry_at=30, max_height=5, values=['MY_BLOCK','BLOCK2','BLOCK5'])

    def beforeEditing(self):
        """
        Before editing the form, change the notice text depending on the type of defaults we are changing

        """
        if self.type == "GLOBAL":
            self.notice.value = "You are currently changing the GLOBAL defaults."
        else:
            self.notice.value = "You are currently changing the LOCAL defaults."