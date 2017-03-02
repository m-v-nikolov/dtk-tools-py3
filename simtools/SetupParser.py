import json
import os
import sys
from ConfigParser import ConfigParser

from dtk.utils.ioformat.OutputMessage import OutputMessage

class SetupParser:
    """
    Parse user settings and directory locations
    from setup configuration file: simtools.ini
    """
    selected_block = None
    setup_file = None
    default_ini = os.path.join(os.path.dirname(__file__), 'simtools.ini')

    def __init__(self, selected_block=None, setup_file=None, force=False, fallback='LOCAL', quiet=False, working_directory=None):
        """
        Build a SetupParser.
        The selected_block and setup_file will be stored in class variables and will only be replaced in subsequent
        instances if the force parameter is True.

        If no setup_file is specified, the SetupParser will look in the current working directory for a simtools.ini
        file. If a file is specified, then this file is used and simtools.ini in the working directory is ignored.

        The global defaults (simtools/simtools.ini) are always loaded first before any overlay is applied.

        If the current selected_block cannot be found in the global default or overlay, then the fallback block is used.

        :param selected_block: The current block we want to use
        :param setup_file: The current overlay file we want to use
        :param force: Force the replacement of selected_block and setup_file in the class variable
        :param fallback: Fallback block if the selected_block cannot be found
        """
        # print selected_block
        # from simtools import utils
        # print utils.caller_name()

        # Test if the default ini exist
        if not os.path.exists(self.default_ini):
            OutputMessage("The default simtools.ini file does not exist in %s. Please run 'python setup.py' again!" % self.default_ini,'warning')
            exit()

        # Store the selected_block in the class only if passed
        if selected_block and (not SetupParser.selected_block or force):
            SetupParser.selected_block = selected_block
        elif not SetupParser.selected_block and not selected_block:
            # There's no block stored and none passed -> assume the fallback
            SetupParser.selected_block = fallback

        if setup_file and (not SetupParser.setup_file or force):
            # Only add the file if it exists
            if os.path.exists(setup_file):
                SetupParser.setup_file = setup_file
            else:
                if not quiet:
                    OutputMessage('The setup file (%s) do not exist anymore, ignoring...' % setup_file, 'warning')

        # First, always load the defaults
        self.setup = ConfigParser()
        self.setup.read(self.default_ini)

        # Only care for HPC/LOCAL -> all the other sections will be added when overlaying the default file
        for sec in self.setup.sections():
            if sec not in ('HPC', 'LOCAL'):
                self.setup.remove_section(sec)

        # Add the user to the default
        if sys.platform == 'win32':
            user = os.environ['USERNAME']
        else:
            import pwd
            user = pwd.getpwuid(os.geteuid())[0]
        self.setup.set('DEFAULT', 'user', user)

        # Overlay the default file to itself to ensure all blocks outside of HPC/LOCAL have all their params set
        cp = ConfigParser()
        cp.read(self.default_ini)
        cp.set('DEFAULT','user',user)
        self.overlay_setup(cp)

        # Then overlays the eventual setup_file passed or simtools.ini in working dir
        overlay_path = None
        if self.setup_file and os.path.exists(self.setup_file):
            overlay_path = self.setup_file
        elif not working_directory and os.path.exists(os.path.join(os.getcwd(), 'simtools.ini')):
            overlay_path = os.path.join(os.getcwd(), 'simtools.ini')
        elif working_directory and os.path.exists(os.path.join(working_directory, 'simtools.ini')):
            overlay_path = os.path.join(working_directory, 'simtools.ini')

        # If we found an overlay applies it
        if overlay_path:
            overlay = ConfigParser()
            overlay.read(overlay_path)

            # Add the user just in case if not specified already
            if not overlay.has_option('DEFAULT','user'):
                overlay.set('DEFAULT','user',user)

            # Overlay
            self.overlay_setup(overlay)

        # Test if we now have the block we want
        if not self.setup.has_section(self.selected_block):
            setup_file_path = overlay_path if overlay_path else os.path.join(os.path.dirname(__file__), 'simtools.ini')
            if not quiet:
                OutputMessage("Selected setup block %s not present in the file (%s).\n Reverting to %s instead!" % (selected_block, setup_file_path, fallback), 'warning')
            # The current block was not found... revert to the fallback
            return self.override_block(fallback)

        # If the selected block is type=HPC, take care of HPC initialization
        if self.get('type') == "HPC":
            from simtools.Utilities.COMPSUtilities import COMPS_login
            COMPS_login(self.get('server_endpoint'))

    def override_block(self,block):
        """
        Overrides the selected block.
        Basically call the constructor with force=True
        :param block: New block we want to use
        """
        self.__init__(selected_block=block, force=True)

    def overlay_setup(self,cp):
        """
        Overlays a ConfigParser on the current self.setup ConfigParser.
        Overlays all the blocks found there.

        We need to do the overlay in two stages.
        1. Overlay HPC/LOCAL blocks to change the defaults
        2. Overlay the other custom sections

        This two steps allows the user to redefine defaults HPC/LOCAL in the overlay file.

        Examples:
            Lets assumes a global defaults with the following::

                [LOCAL]
                p1 = 1
                p3 = 3

                [HPC]
                p1 = 2

            And an overlay like::

                [LOCAL]
                p1 = 3

                [CUSTOM]
                type=LOCAL
                p2 = 10

            If we use the `CUSTOM` block, it will end up having::

                p1 = 3
                p2 = 10
                p3 = 3

            Because we will first overlay the custom LOCAL to the global LOCAL and then overlay the CUSTOM block.

        :param cp: The ConfigParser to overlay
        """
        # Overlay the LOCAL/HPC to the default ones
        for section in cp.sections():
            if section in ('HPC','LOCAL'):
                for item in cp.items(section):
                    self.setup.set(section, item[0], item[1])

        # Then overlay all except the LOCAL/HPC ones (already did before)
        for section in cp.sections():
            if section in ("LOCAL", "HPC"):
                continue

            # The overlaid section doesnt exist in the setup -> create it
            if not self.setup.has_section(section):
                # Create the section
                self.setup.add_section(section)

                # Depending on the type grab the default from HPC or LOCAL
                for item in self.setup.items(cp.get(section, 'type')):
                    self.setup.set(section, item[0], item[1])

            # Override the items
            for item in cp.items(section):
                self.setup.set(section, item[0], item[1])

    def get(self, parameter, default=None):
        if not self.has_option(parameter):
            if default: return default
            else: raise ValueError("%s block does not have the option %s!" % (self.selected_block, parameter))
        return self.setup.get(self.selected_block,parameter)

    def has_option(self,option):
        return self.setup.has_option(self.selected_block,option)

    def set(self, parameter, value):
        self.setup.set(self.selected_block, parameter, value)

    def items(self):
        return self.setup.items(self.selected_block)

    def getboolean(self, parameter, default=None):
        if not self.has_option(parameter):
            if default != None: return default
            else: raise ValueError("%s block does not have the option %s!" % (self.selected_block, parameter))
        return self.setup.getboolean(self.selected_block, parameter)

    def lookup_param(self, section, parameter):
        # Save the current block
        previous_selected_block = self.selected_block
        sp = SetupParser(selected_block=section, force=True)
        result = sp.get(parameter, None)
        SetupParser.selected_block = previous_selected_block
        return result

    def load_schema(self):
        json_schema = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_schema.json")))
        self.schema = json_schema
        return json_schema