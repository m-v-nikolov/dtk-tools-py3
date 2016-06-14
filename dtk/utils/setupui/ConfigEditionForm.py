import npyscreen

from dtk.utils.setupui.SaveLocationPopup import SaveLocationPopup
from dtk.utils.setupui.utils import add_block, get_block, delete_block
from simtools.SetupParser import SetupParser

class IntegerSlider(npyscreen.Slider):
    def translate_value(self):
        stri = "%s / %s" % (int(self.value), int(self.out_of))
        if isinstance(stri, bytes):
            stri = stri.decode(self.encoding, 'replace')
        l = (len(str(self.out_of))) * 2 + 4
        stri = stri.rjust(l)
        return stri

class ConfigEditionForm(npyscreen.FormMultiPageAction):
    """
    Form allowing edition/creation of a configuration block.
    Two important variables:
    - self.schema: holds the INI validation schema definition
    - self.type: are we working with LOCAL or HPC block
    - self.global_defaults: are we editing the global defaults?
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
        self.helps = dict()
        self.global_defaults = False

        # The sliders will be int
        npyscreen.TitleSlider._entry_type = IntegerSlider

    def beforeEditing(self):
        """
        Before editing, clear all widgets and create the form again.
        We are clearing out everything because the type may have changed so new fields needs to be created.

        If the type=HPC, there are more fields to display so are creating a new form page.
        If the type=LOCAL, everything can fit on one page.
        """
        # Empty the form
        self._clear_all_widgets()
        self.fields = dict()
        self.helps = dict()

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

        # Overrides event to react to toggle of the service assets checkbox
        if self.type == 'HPC':
            self.fields['use_comps_asset_svc'].whenToggled = self.h_asset_svc_toggled
            # Also call it once to hide/show the fields
            self.h_asset_svc_toggled()

        # If we are editing global default -> make name it readonly
        if self.global_defaults:
            self.fields['name'].editable = False
            self.fields['name'].update()


    def on_cancel(self):
        """
        Cancel is pushed -> simply return to the main menu
        """
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        """
        Save is pushed -> save the configuration and return to main menu
        """

        if self.block:
            # Add/edit the block
            block_name = add_block(block_type=self.type, local=self.block['location'] == 'LOCAL', fields=self.fields)
            message = "local" if self.block['location'] == 'LOCAL' else "global"
            npyscreen.notify_confirm("The configuration block %s has been modified successfully in the %s INI file." % (block_name, message), title='Success!')
        else:
            # Ask the location
            popup = SaveLocationPopup()
            popup.edit()

            # Add the block
            block_name = add_block(block_type=self.type, local=popup.local, fields=self.fields)
            message = "local" if popup.local else "global"
            npyscreen.notify_confirm("The configuration block %s has been saved successfully in the %s INI file." % (block_name, message), title='Success!')

        self.parentApp.switchFormPrevious()

    def set_block(self,block):
        if block:
            self.block = get_block(block)
            self.type = self.block['type']
            self.global_defaults = block in ('LOCAL','HPC')
        else:
            self.block = None
            self.global_defaults = False

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
                # Simple text box for string and url
                widget_class = npyscreen.TitleText
                additionnal_params['value'] = value

            elif type == "int":
                # Slider for int
                widget_class = npyscreen.TitleSlider
                additionnal_params['out_of'] = field['max']
                additionnal_params['lowest'] = field['min']
                additionnal_params['value'] = 0 if not value else float(value)

            elif type == "file" or type == "directory":
                # If we are working with HPC block -> no browsing of directory so display simple strings
                if self.type == "HPC":
                    widget_class = npyscreen.TitleText
                else:
                    # File picker for file and directory
                    widget_class = npyscreen.TitleFilenameCombo
                    additionnal_params['select_dir'] = type != "file"
                additionnal_params['value'] = value

            elif type == "bool":
                # Checkbox for bool
                widget_class = npyscreen.Checkbox
                additionnal_params['value'] = value == '1'

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
            self.helps[field['name']] = h

            nexty = h.rely + 2

        return nexty


    def h_asset_svc_toggled(self):
        asset_svc = self.fields['use_comps_asset_svc'].value
        self.fields['exe_path'].hidden = asset_svc
        self.fields['dll_path'].hidden = asset_svc
        self.helps['exe_path'].hidden = asset_svc
        self.helps['dll_path'].hidden = asset_svc




