import npyscreen

from simtools import SetupParser


class ConfigEditionForm(npyscreen.FormMultiPageAction):

    OK_BUTTON_TEXT = "Save"
    CANCEL_BUTTON_TEXT = "Return to menu"

    def on_cancel(self):
        self.parentApp.switchFormPrevious()

    def on_ok(self):
        npyscreen.notify_confirm("The configuration has been saved successfully.", title='Success!')
        self.parentApp.switchFormPrevious()

    def create_fields(self, definitions, starting_y=6):
        nexty = starting_y
        additionnal_params = {}

        for field in definitions:
            type = field['type']
            if type == "string" or type == "url":
                widget_class = npyscreen.TitleText

            elif type == "int":
                widget_class = npyscreen.TitleSlider
                additionnal_params['out_of'] = field['max']
                additionnal_params['lowest'] = field['min']

            elif type == "file" or type == "directory":
                widget_class = npyscreen.TitleFilenameCombo
                additionnal_params['select_dir'] = type != "file"

            elif type == "bool":
                widget_class = npyscreen.Checkbox

            elif type == "radio":
                widget_class = npyscreen.TitleSelectOne
                additionnal_params['values'] = field['choices']
                additionnal_params['max_height'] = len(field['choices'])+1
                additionnal_params['return_exit'] = True
                additionnal_params['select_exit'] = True
                additionnal_params['scroll_exit'] = True

            w = self.add(widget_class, w_id=field['name'], name=field['label'] + ":", use_two_lines=False, rely=nexty,
                     begin_entry_at=len(field['label']) + 2, **additionnal_params)

            # Add the help text
            h = self.add(npyscreen.FixedText,  editable=False, value=field['help'], color='CONTROL')

            nexty = h.rely + 2

        return nexty

    def create(self):
        # Load the schema
        self.schema = SetupParser().load_schema()
        self.type = "LOCAL"

    def beforeEditing(self):
        self._clear_all_widgets()
        self.add(npyscreen.MultiLineEdit, editable=False, max_height=4,value="In this form, you will be able to specify the values for the different field of the configuration.\r\n"
                                                            "Leaving a field blank will accept the global defaults.\r\n"
                                                            "To exit the selection of file/folder press 'ESC'.")
        # Display a name field
        y=6
        definitions = [{"type": "string", "label": "Block name", "help": "Name for the configuration block.", "name": "name"}]
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

