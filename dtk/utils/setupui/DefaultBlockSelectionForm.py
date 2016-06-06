import npyscreen

from dtk.utils.setupui.utils import get_all_blocks, get_default_blocks, change_defaults


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
        # Retrieve the default chosen
        local_default = self.local_selection.get_selected_objects()[0] if len(self.local_selection.value) > 0 else None
        hpc_default = self.hpc_selection.get_selected_objects()[0] if len(self.hpc_selection.value) > 0 else None

        # Change the defaults in the file
        change_defaults(self.local, local_default, hpc_default)

        npyscreen.notify_confirm("The defaults have been saved!", title='Success!')
        self.parentApp.switchFormPrevious()

    def create(self):
        """
        Initialization of the form
        """
        # By default assume we are editing the GLOBAL defaults
        self.local = False

        # Add some text to explain
        self.add(npyscreen.MultiLineEdit, editable=False, max_height=2, value="On this page you can change the default block used by default for both LOCAL and\r\nHPC configurations.")
        self.notice = self.add(npyscreen.MultiLineEdit, color='STANDOUT', editable=False, max_height=1)

        # List the LOCAL blocks
        self.local_selection = self.add(npyscreen.TitleSelectOne, rely=6, return_exit=True, select_exit=True, scroll_exit=True,
                         name="Default LOCAL configuration:", use_two_lines=False, begin_entry_at=30, max_height=8)

        # List the HPC blocks
        self.hpc_selection = self.add(npyscreen.TitleSelectOne, rely=16, return_exit=True, select_exit=True, scroll_exit=True,
                 name="Default HPC configuration:", use_two_lines=False, begin_entry_at=30, max_height=8)

        # Extra action buttons
        self.remove_local = self.add(
            npyscreen.MiniButtonPress,
            name="Remove LOCAL default",
            rely=0 - self.__class__.OK_BUTTON_BR_OFFSET[0],
            relx=2,
            use_max_space=True,
            color='DANGER',
            when_pressed_function=self.h_remove_default
        )

        self.remove_hpc =self.add(
            npyscreen.MiniButtonPress,
            name="Remove HPC default",
            rely=0 - self.__class__.OK_BUTTON_BR_OFFSET[0],
            relx=25,
            use_max_space=True,
            color='DANGER',
            when_pressed_function=self.h_remove_default
        )

    def h_remove_default(self):
        if self.remove_local.value:
            change_defaults(self.local, local_default=True, remove=True)
            self.local_selection.value = None
        elif self.remove_hpc.value:
            change_defaults(self.local, hpc_default=True, remove=True)
            self.hpc_selection.value = None

    def beforeEditing(self):
        """
        Before editing the form, change the notice text depending on the type of defaults we are changing.
        """
        if self.local:
            self.notice.value = "You are currently changing the LOCAL defaults."
        else:
            self.notice.value = "You are currently changing the GLOBAL defaults."

        # Unselect all
        self.local_selection.value = self.hpc_selection.value = None

        # Get all the sections
        sections = get_all_blocks(self.local)
        self.local_selection.values = sorted(sections['LOCAL'])
        self.hpc_selection.values = sorted(sections['HPC'])

        # Handles if there are no blocks found for a given category
        if len(self.local_selection.values) == 0:
            self.local_selection.editable = False
            self.local_selection.values.append("No LOCAL blocks found")
        else:
            self.local_selection.editable = True

        if len(self.hpc_selection.values) == 0:
            self.hpc_selection.editable = False
            self.hpc_selection.values.append("No HPC blocks found")
        else:
            self.hpc_selection.editable = True

        # Get the current defaults
        local_default, hpc_default = get_default_blocks(self.local)

        if local_default:
            self.local_selection.value = [self.local_selection.values.index(local_default)]
        if hpc_default:
            self.hpc_selection.value = [self.hpc_selection.values.index(hpc_default)]

