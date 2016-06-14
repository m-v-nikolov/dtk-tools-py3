import os

import npyscreen
import sys

from ConfigEditionForm import ConfigEditionForm
from dtk.utils.setupui.MainMenuForm import MainMenuForm


class SetupApplication(npyscreen.NPSAppManaged):
    """
    Main application for the dtk setup command.
    Forms available:
    - MAIN: Display the menu
    - DEFAULT_SELECTION: Form to select the default blocks
    - EDIT: Form to edit/create a block
    """

    def onStart(self):
        self.addForm('MAIN', MainMenuForm, name='dtk-tools v0.3.5')
        self.addForm('EDIT', ConfigEditionForm, name='Block creation/edition form')

    def change_form(self, name):
        # Switch forms.  NB. Do *not* call the .edit() method directly (which
        # would lead to a memory leak and ultimately a recursion error).
        # Instead, use the method .switchForm to change forms.
        self.switchForm(name)

