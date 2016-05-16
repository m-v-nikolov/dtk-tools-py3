import npyscreen


class DefaultBlockSelectionForm(npyscreen.ActionFormV2):

    OK_BUTTON_TEXT = "Save"
    CANCEL_BUTTON_TEXT = "Return to menu"

    def on_cancel(self):
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        npyscreen.notify_confirm("The defaults have been saved!", title='Success!')
        self.parentApp.switchFormPrevious()

    def create(self):
        self.type="GLOBAL"
        self.add(npyscreen.MultiLineEdit, editable=False, max_height=2, value="On this page you can change the default block used by default for both LOCAL and\r\nHPC configurations.")
        self.notice = self.add(npyscreen.MultiLineEdit, color='STANDOUT', editable=False, max_height=1)

        # List the blocks
        local = self.add(npyscreen.TitleSelectOne, rely=6, return_exit=True, select_exit=True, scroll_exit = True,
                         name="Default LOCAL configuration:", use_two_lines=False, begin_entry_at=30, max_height=5, values=['MY_BLOCK','BLOCK2','BLOCK5'])

        self.add(npyscreen.TitleSelectOne,  rely=local.rely+2+len(local.values), return_exit=True, select_exit=True, scroll_exit = True,
                 name="Default HPC configuration:", use_two_lines=False, begin_entry_at=30, max_height=5, values=['MY_BLOCK','BLOCK2','BLOCK5'])

    def beforeEditing(self):
        if self.type == "GLOBAL":
            self.notice.value = "You are currently changing the GLOBAL defaults."
        else:
            self.notice.value = "You are currently changing the LOCAL defaults."