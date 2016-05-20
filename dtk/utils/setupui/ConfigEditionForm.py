import npyscreen

from simtools import SetupParser


class ConfigEditionForm(npyscreen.FormMultiPageAction):
    """
    Form allowing edition/creation of a configuration block.
    Two important variables:
    - self.schema: holds the INI validation schema definition
    - self.type: LOCAL or HPC to display the correct associated fields
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

    def beforeEditing(self):
        """
        Before editing, clear all widgets and create the form again.
        We are clearing out everything because the type may have changed so new fields needs to be created.

        If the type=HPC, there are more fields to display so are creating a new form page.
        If the type=LOCAL, everthing can fit on one page.
        """
        # Empty the form
        self._clear_all_widgets()

        # Add explanation
        self.add(npyscreen.MultiLineEdit, editable=False, max_height=4,
                 value="In this form, you will be able to specify the values for the different field of the configuration.\r\n"
                       "Leaving a field blank will accept the global defaults.\r\n"
                       "To exit the selection of file/folder press 'ESC'.")

        # Display a name field
        y = 6
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
        npyscreen.notify_confirm("The configuration has been saved successfully.", title='Success!')
        self.parentApp.switchFormPrevious()

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

            if type == "string" or type == "url":
                # Simpla text box for string and url
                widget_class = npyscreen.TitleText

            elif type == "int":
                # Slider for int
                widget_class = npyscreen.TitleSlider
                additionnal_params['out_of'] = field['max']
                additionnal_params['lowest'] = field['min']

            elif type == "file" or type == "directory":
                # File picker for file and directory
                widget_class = npyscreen.TitleFilenameCombo
                additionnal_params['select_dir'] = type != "file"

            elif type == "bool":
                # Checkbox for bool
                widget_class = npyscreen.Checkbox

            elif type == "radio":
                # List of choices for radio
                widget_class = npyscreen.TitleSelectOne
                additionnal_params['values'] = field['choices']
                additionnal_params['max_height'] = len(field['choices'])+1
                additionnal_params['return_exit'] = True
                additionnal_params['select_exit'] = True
                additionnal_params['scroll_exit'] = True

            # When we have the class and the addtional_params, create the widget
            w = self.add(widget_class, w_id=field['name'], name=field['label'] + ":", use_two_lines=False, rely=nexty,
                     begin_entry_at=len(field['label']) + 2, **additionnal_params)

            # Add the help text
            h = self.add(npyscreen.FixedText,  editable=False, value=field['help'], color='CONTROL')

            nexty = h.rely + 2

        return nexty





