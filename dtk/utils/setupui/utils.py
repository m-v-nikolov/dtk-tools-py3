import os
from ConfigParser import ConfigParser


def get_file_handler(local, mode):
    if local:
        file_handler = open(os.path.join(os.getcwd(), "config.ini"), mode)
    else:
        file_handler = open(os.path.join(os.path.dirname(__file__), "..", "..","..", "simtools", 'simtools.cfg'), mode)

    return file_handler


def add_block(local, fields):
    # Get the file handler
    file_handler = get_file_handler(local,'a')

    # Prepare the section name
    section = fields['name'].value
    section = section.replace(' ', '_').upper()
    del fields['name']

    # Create a config parser to help
    config = ConfigParser()
    config.add_section(section)

    # Add the type
    config.set(section, 'type', "HPC" if not local else "LOCAL")

    # Add the different config item to the section providing they are not None or 0
    for id, widget in fields.iteritems():
        if widget.value and widget.value != 0:
            config.set(section, id, widget.value)

    config.write(file_handler)

    return section