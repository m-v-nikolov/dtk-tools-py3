import os
from ConfigParser import ConfigParser

def get_file_path(local):
    """
    Get the file path for either the local ini or the global ini.
    :param local: If true, opens the local ini file, if false opens the global one
    :return: Complete file path to the ini file
    """
    if local:
        return os.path.join(os.getcwd(), "config.ini")
    return os.path.join(os.path.dirname(__file__), "..", "..","..", "simtools", 'simtools.cfg')

def get_default_blocks(local):
    config = ConfigParser()
    config.read(get_file_path(local))

    local_default = config.get('DEFAULT','local') if config.has_option('DEFAULT','local') else None
    hpc_default = config.get('DEFAULT','hpc') if config.has_option('DEFAULT','hpc') else None

    return local_default, hpc_default

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
    ret = {'LOCAL':[], 'HPC':[]}
    for section in  config.sections():
        # Ignore certain sections
        if section in ("DEFAULT","GLOBAL","BINARIES"): continue

        # Depending on the section type, append it to the correct return section
        if config.get(section, "type") == "HPC":
            ret['HPC'].append(section)
        else:
            ret['LOCAL'].append(section)

    return ret


def add_block(block_type, local, fields):
    """
    Add a block to a local (or global) config file
    :param local: If true, add to the local ini, if false add to the global default
    :param block_type: Block type (LOCAL or HPC)
    :param fields: Dictionary containing the form widgets with user inputs
    :return: the section name
    """
    # Get the file handler
    file_handler = open(get_file_path(local),'a')

    # Prepare the section name
    section = fields['name'].value
    section = section.replace(' ', '_').upper()
    del fields['name']

    # Create a config parser to help
    config = ConfigParser()
    config.add_section(section)

    # Add the type
    config.set(section, 'type', block_type)

    # Add the different config item to the section providing they are not None or 0
    for id, widget in fields.iteritems():
        if widget.value and widget.value != 0:
            value = widget.value

            # Special case of widget.value (choices and checkboxes)
            if isinstance(widget.value, list):
                value = widget.get_selected_objects()[0]
            elif isinstance(widget.value, bool):
                value = 1 if widget.value else 0

            config.set(section, id, value)

    config.write(file_handler)

    return section

def change_defaults(local, local_default=None, hpc_default=None, remove=False):
    """

    :param local:
    :param local_default:
    :param hpc_default:
    :param remove:
    :return:
    """
    # Create a config parser
    config = ConfigParser()
    config.read(get_file_path(local))

    if not remove:
        # Set the section
        if hpc_default:
            config.set('DEFAULT','HPC', hpc_default)
        if local_default:
            config.set('DEFAULT','LOCAL', local_default)
    else:
        if hpc_default:
            config.remove_option('DEFAULT','HPC')
        if local_default:
            config.remove_option('DEFAULT','LOCAL')

    # Write down the file
    with open(get_file_path(local),'w') as file_handler:
        config.write(file_handler)



if __name__ == '__main__':
    local,hpc = get_default_blocks(True)
    print hpc