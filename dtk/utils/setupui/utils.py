import os
from ConfigParser import ConfigParser

from simtools.SetupParser import SetupParser


def get_file_path(local):
    """
    Get the file path for either the local ini or the global ini.
    Create the file if it doesnt exist.

    :param local: If true, opens the local ini file, if false opens the global one
    :return: Complete file path to the ini file
    """
    if local:
        local_path = os.path.join(os.getcwd(), "simtools.ini")
        if not os.path.exists(local_path):
            open(local_path,'w').close()
        return local_path

    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "simtools", 'simtools.ini'))


def get_block(block):
    """
    Retrieve a block.
    Returns a dictionary with the block info
    :param block: block name. If the name contains (*) look into the local ini file
    :return: dictionary containing the block info
    """
    # Retrieve the cleanup name
    block_name = block.replace(' (*)', '')

    # Set the location
    location = "LOCAL" if "(*)" in block else "GLOBAL"

    # The SetupParser will ignore any CWD overlay file if a setup_file is passed
    # So if we want a block in the global default, just pass the global default as setup overlay
    # to bypass the CWD simtools.ini
    sp = SetupParser(selected_block=block_name, force=True, setup_file=get_file_path(location == "LOCAL"))

    # Transform into a dictionary
    ret = {a: b for (a, b) in sp.setup.items(block_name, True)}

    # set the name and location
    ret['name'] = block_name
    ret['location'] = location

    # Returns a dict with the info
    return ret


def get_all_blocks(local):
    """
    Returns a dictionary containing the blocks in the local or global file.
    ```
        {
            'HPC': ["HPC_BLOCK_1", "HPC_BLOCK_2"],
            'LOCAL': ["LOCAL_BLOCK_1"]
        }
    ```
    :param local: If true, reads the local ini file, if false reads the global ini file
    :return: Dictionary of blocks categorized on type
    """
    config = ConfigParser()
    config.read(get_file_path(local))

    ret = {'LOCAL': [], 'HPC': []}
    for section in config.sections():
        # If the section has no type, it is probably av overlay. Check in the global
        if not config.has_option(section, 'type'):
            if not local:
                # We are in the global file and we don't have type, it is an error... assume local
                current_type = 'LOCAL'
            else:
                global_config = ConfigParser()
                global_config.read(get_file_path(False))

                # If the global config doesnt have the block type either, its an error assumes LOCAL else get
                # the correct block type
                current_type = global_config.get(section,"type") if global_config.has_section(section) and global_config.has_option(section,'type') else "LOCAL"
        else:
            # Normal behavior
            current_type = config.get(section, 'type')

        # Append it to the correct return section
        ret[current_type].append(section)

    return ret


def delete_block(block, local):
    """
    Delete the block passed in the local or global file
    :param block: The block to remove
    :param local: local ini file or global ini file
    :return:
    """
    config = ConfigParser()
    config.read(get_file_path(local))

    if config.has_section(block):
        config.remove_section(block)

    with open(get_file_path(local), 'w') as file_handler:
        config.write(file_handler)


def add_block(block_type, local, fields):
    """
    Add a block to a local (or global) config file

    :param local: If true, add to the local ini, if false add to the global default
    :param block_type: Block type (LOCAL or HPC)
    :param fields: Dictionary containing the form widgets with user inputs
    :return: the section name
    """
    config = ConfigParser()
    config.read(get_file_path(local))

    # Prepare the section name
    section = fields['name'].value
    section = section.replace(' ', '_').upper()
    del fields['name']

    # The SetupParser will ignore any CWD overlay file if a setup_file is passed
    # So if we want a block in the global default, just pass the global default as setup overlay
    # to bypass the CWD simtools.ini
    sp = SetupParser(selected_block=section, force=True, setup_file=get_file_path(local), fallback=block_type, quiet=True)

    # Add section if doesnt exist
    if not config.has_section(section):
        config.add_section(section)

    # Add the type
    config.set(section, 'type', block_type)

    # Add the different config item to the section providing they are not None or 0
    for widget_id, widget in fields.iteritems():
        if widget.hidden:
            continue

        if widget.value and widget.value != 0:
            value = widget.value

            # Special case of widget.value (choices and checkboxes)
            if isinstance(widget.value, list):
                value = widget.get_selected_objects()[0]
            elif isinstance(widget.value, bool):
                value = 1 if widget.value else 0
            elif isinstance(widget.value, float):
                value = int(widget.value)

            # Only add if different from the SetupParser value
            # Allow to only record the differences and make cleaner files
            if str(sp.get(widget_id)) != str(value):
                config.set(section, widget_id, value)

    with open(get_file_path(local), 'w') as file_handler:
        config.write(file_handler)

    return section
