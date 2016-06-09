import npyscreen

from dtk.utils.setupui.SaveLocationPopup import SaveLocationPopup
from dtk.utils.setupui.utils import add_block, get_block, delete_block
from simtools import SetupParser


class ConfigEditionForm(npyscreen.FormMultiPageAction):
    """
    Form allowing edition/creation of a configuration block.
    Two important variables:
    - self.schema: holds the INI validation schema definition
    - self.type: are we working with LOCAL or HPC block
    """
    # Rename the buttons
    OK_BUTTON_TEXT = "Save"
    CANCEL_BUTTON_TEXT = "Return to menu"

    def create(self):
        """
        Initialization of the form.
        Load the schema and initialize the type.
        """
        self.schema = SetupParser().load_schema()
        self.type = "LOCAL"
        self.fields = dict()

    def beforeEditing(self):
        """
        Before editing, clear all widgets and create the form again.
        We are clearing out everything because the type may have changed so new fields needs to be created.

        If the type=HPC, there are more fields to display so are creating a new form page.
        If the type=LOCAL, everthing can fit on one page.
        """
        # Empty the form
        self._clear_all_widgets()
        self.fields = dict()

        # Add explanation
        self.add(npyscreen.MultiLineEdit, editable=False, max_height=4,
                 value="In this form, you will be able to specify the values for the different field of the configuration.\r\n"
                       "Leaving a field blank will accept the global defaults.\r\n"
                       "To exit the selection of file/folder press 'ESC'.")

        # Display a name field
        definitions = [
            {"type": "string", "label": "Block name", "help": "Name for the configuration block.", "name": "name"}]
        y = self.create_fields(definitions)

        # No matter what create the common fields
        y = self.create_fields(self.schema['COMMON'], starting_y=y)

        # If HPC, create a new page
        if self.type == "HPC":
            self.add_page()
            y = 2

        # Then display the extra fields depending on the type
        self.create_fields(self.schema[self.type], starting_y=y)

        # Go to first page
        self.switch_page(0)

    def on_cancel(self):
        """
        Cancel is pushed -> simply return to the main menu
        """
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        """
        Save is pushed -> save the configuration and return to main menu
        """
        if not self.block:
            # Ask the location only if the bloc
            popup = SaveLocationPopup()
            popup.edit()

        if self.block:
            # We had a block, delete it first before adding
            delete_block(self.block['name'], self.block['location'] == 'LOCAL')
            block_name = add_block(block_type=self.type, local=self.block['location'] == 'LOCAL', fields=self.fields)
            message = "local" if self.block['location'] == 'LOCAL' else "global"
            npyscreen.notify_confirm("The configuration block %s has been modified successfully in the %s INI file." % (block_name, message), title='Success!')
        else:
            # Add the block
            block_name = add_block(block_type=self.type, local=popup.local, fields=self.fields)
            message = "local" if popup.local else "global"
            npyscreen.notify_confirm("The configuration block %s has been saved successfully in the %s INI file." % (block_name, message), title='Success!')
        self.parentApp.switchFormPrevious()

    def set_block(self,block):
        self.block = get_block(block)
        self.type = self.block['type']

    def create_fields(self, definitions, starting_y=6):
        """
        Create form fields based on a list of field definition (held in the definitions list) and starting
        at a y position given by starting_y.
        The field types can be:
        - string/url: will display a text field
        - int: Will display a slider
        - file/directory: will display a file picker (with or without the directory constraint)
        - bool: will display a checkbox
        - radio: will display a list of choices (select one only)

        The field also need a name and a help text to go along with them.
        Depending on the type extra parameters are searched in the schema.
        For example for a "int" type, the slider will also look for a "min" and "max" parameters.

        :param definitions: List of field definition to display
        :param starting_y: Starting y position
        :return: The final y position
        """
        nexty = starting_y
        additionnal_params = {}

        # Browse through the definitions and create the correct widget class
        for field in definitions:
            type = field['type']
            # Retrieve the current value if present
            value = self.block[field['name']] if self.block and self.block.has_key(field['name']) else None

            if type == "string" or type == "url":
                # Simpla text box for string and url
                widget_class = npyscreen.TitleText
                additionnal_params['value'] = value

            elif type == "int":
                # Slider for int
                widget_class = npyscreen.TitleSlider
                additionnal_params['out_of'] = field['max']
                additionnal_params['lowest'] = field['min']
                additionnal_params['value'] = 0 if not value else float(value)


            elif type == "file" or type == "directory":
                # File picker for file and directory
                widget_class = npyscreen.TitleFilenameCombo
                additionnal_params['select_dir'] = type != "file"
                additionnal_params['value'] = value

            elif type == "bool":
                # Checkbox for bool
                widget_class = npyscreen.Checkbox
                additionnal_params['value'] = bool(value)

            elif type == "radio":
                # List of choices for radio
                widget_class = npyscreen.TitleSelectOne
                additionnal_params['values'] = field['choices']
                additionnal_params['max_height'] = len(field['choices'])+1
                additionnal_params['return_exit'] = True
                additionnal_params['select_exit'] = True
                additionnal_params['scroll_exit'] = True
                additionnal_params['value'] = None if not value else field['choices'].index(value)

            # When we have the class and the additional_params, create the widget
            w = self.add(widget_class, w_id=field['name'], name=field['label'] + ":", use_two_lines=False, rely=nexty,
                     begin_entry_at=len(field['label']) + 2, **additionnal_params)

            self.fields[field['name']] = w

            # Add the help text
            h = self.add(npyscreen.FixedText,  editable=False, value=field['help'], color='CONTROL')

            nexty = h.rely + 2

        return nexty





