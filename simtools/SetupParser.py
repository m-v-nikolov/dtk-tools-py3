import json
import os
import fasteners
from ConfigParser import ConfigParser
from simtools.Utilities.LocalOS import LocalOS
from simtools.Utilities.General import init_logging

current_dir = os.path.dirname(os.path.realpath(__file__))
logger = init_logging("SetupParser")


class SetupParserMeta(type):
    # The center of the SetupParser universe, the singleton.
    singleton = None
    initialized = False

    # redirect all attribute calls to the singleton once initialized
    def __getattr__(cls, item):
        if cls.initialized:
            return getattr(cls.singleton, item)
        else:
            if item == '__test__':  # fix for nosetests...
                return None
            raise SetupParser.NotInitialized("Missing attribute: %s" % item)

    @classmethod
    @fasteners.interprocess_locked(os.path.join(current_dir, '.setup_parser_init_lock'))
    def init(cls, selected_block=None, **kwargs):
        """
        Initialize the SetupParser singleton
        :param selected_block:
        :param kwargs: See __init__ for parameter list
        :return: Nothing.
        """
        if SetupParser.initialized:  # do not allow re-initialization
            raise SetupParser.AlreadyInitialized("Cannot re-initialize the SetupParser class")
        if kwargs.get('singleton', None):
            cls.singleton = kwargs.get('singleton')
        else:
            if not kwargs.get('old_style_instantiation', None):
                kwargs['old_style_instantiation'] = False
            cls.singleton = SetupParser(selected_block=selected_block, **kwargs)
        cls.initialized = True

    @classmethod
    @fasteners.interprocess_locked(os.path.join(current_dir, '.setup_parser_init_lock'))  # shared with .init()
    def _uninit(cls):
        """
        This is for testing only. Please, please, please don't ever use it! It is the inverse
        method of init().
        :return:
        """
        cls.singleton = None
        cls.initialized = False


class SetupParser(object):
    """
    Parse user settings and directory locations
    from setup configuration file: simtools.ini

    SetupParser is a singleton whose values can only be set once. It should be accessed directly as a class and never
    instantiated. This is to provide a homogeneous, unchanging view of its configuration.
    """

    __metaclass__ = SetupParserMeta

    class MissingIniFile(Exception):
        pass

    class MissingIniBlock(Exception):
        pass

    class AlreadyInitialized(Exception):
        pass

    class NotInitialized(Exception):
        DEFAULT_MSG = "SetupParser must first be called with .init() ."

        def __init__(self, msg=None):
            self.msg = msg if msg else self.DEFAULT_MSG

        def __str__(self):
            return self.msg

    ini_filename = 'simtools.ini'
    default_file = os.path.join(os.path.dirname(__file__), ini_filename)
    default_block = 'LOCAL'

    def __init__(self, selected_block=None, setup_file=None, commissioning_directory=None, overrides={},
                 is_testing=False, old_style_instantiation=None):
        """
        This should only be used to initialize the SetupParser singleton.
        Provides access to the selected_block of the resultant ini config overlay. Overlays are performed by merging
        the selected overlay ini file onto the default ini file.

        Overlay file selection priority:
        1. setup_file, if provided
        2. current/local working directory ini file, if it exists
        3. ini in commissioning_directory, if provided
        4. No overlay (defaults only)

        If the selected_block cannot be found in the resultant ini overlay, an exception will be thrown.

        :param selected_block: The current block we want to use
        :param setup_file: If provided, this ini file will overlay the default UNLESS commissioning_directory was
                           also provided.
        :param commissioning_directory: If provided, the ini file within it will always overlay the default ini file.
        :overrides: The values in this dict supersede those returned by the ConfigParser object in .get()
        :is_testing: Allows bypassing of interactive login to COMPS if True. No login attempt is made in this case.
        """
        if old_style_instantiation is None:
            msg = "SetupParser(arguments) is deprecated. Please update your code to use SetupParser.init(arguments) " + \
                  "exactly once. You may then use familiar SetupParser methods on the class, " + \
                  "e.g. SetupParser.get('some_item')"
            logger.warning(msg)
            print msg

            if not selected_block:
                raise Exception("Use of deprecated initializer of SetupParser too generic. Please specify which block"
                                "to select via argument 'block', e.g. SetupParser(block='LOCAL')")

            if SetupParser.initialized:
                if selected_block != SetupParser.selected_block:
                    SetupParser.override_block(block=selected_block)
            else:
                kwargs = {'selected_block': selected_block,
                          'setup_file': setup_file,
                          'commissioning_directory': commissioning_directory,
                          'overrides': overrides,
                          'is_testing': is_testing,
                          'old_style_instantiation': True
                          }
                SetupParser.init(**kwargs)

        self.selected_block = selected_block or self.default_block
        self.setup_file = setup_file
        self.commissioning_directory = commissioning_directory
        self.commissioning_file = os.path.join(commissioning_directory, self.ini_filename) if commissioning_directory else None

        local_file = os.path.join(os.getcwd(), self.ini_filename)
        self.local_file = local_file if os.path.exists(local_file) else None
        self.overrides = overrides

        # Identify which ini file will overlay the default ini, if any, and verify the selected file's existence
        if not os.path.exists(self.default_file):
            raise self.MissingIniFile("Default ini file does not exist: %s . Please run 'python setup.py' again." % self.default_file)

        overlay_path = self._select_and_verify_overlay(local_file=self.local_file, provided_file=self.setup_file,
                                                       commissioning_file=self.commissioning_file)

        # Load the default and overlay it onto itself to explicitly resolve the type=LOCAL/HPC tags to key/values
        # from the literal LOCAL/HPC blocks.
        self.setup = ConfigParser()
        self.setup.read(self.default_file)

        for sec in self.setup.sections():
            if sec not in ('HPC', 'LOCAL'):
                self.setup.remove_section(sec)

        cp = ConfigParser()
        cp.read(self.default_file)
        self._overlay_setup(cp)

        # Apply the overlay if one was found
        if overlay_path:
            overlay = ConfigParser()
            overlay.read(overlay_path)
            self._overlay_setup(overlay)

        # Add the user just in case it wasn't specified already
        self.setup.set('DEFAULT', 'user', LocalOS.username)

        # Verify that we have the requested block in our overlain result
        if not self.setup.has_section(self.selected_block):
            raise self.MissingIniBlock("Selected block: %s does not exist in ini file overlay." % self.selected_block)

        # If the selected block is type=HPC, take care of HPC initialization
        if self.setup.get(self.selected_block, 'type') == "HPC" and not is_testing:
            from simtools.Utilities.COMPSUtilities import COMPS_login
            COMPS_login(self.setup.get(self.selected_block, 'server_endpoint'))

    @classmethod
    def override_block(cls, block):
        """
        Overrides the selected block. Use with care, and definitely not in a multi-threaded situation.
        :param block: New block we want to use
        """
        logger.warning("SetupParser.override_block is deprecated.")
        if cls.singleton.setup.has_section(block):
            cls.singleton.selected_block = block
        else:
            raise cls.MissingIniBlock("Override setup block '%s' does not exist in the setup overlay.")

    def _overlay_setup(self, cp):
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
            if section in ('HPC', 'LOCAL'):
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

    @classmethod
    def get(cls, parameter, default=None, block=None):
        return cls._get_guts(parameter, 'get', default, block)

    @classmethod
    def getboolean(cls, parameter, default=None, block=None):
        return cls._get_guts(parameter, 'getboolean', default, block)

    @classmethod
    def _get_guts(cls, parameter, get_method, default=None, block=None):
        """
        An in-common access method for get() and getboolean()
        :param parameter: The parameter value to get
        :param get_method: The method on cls.instance.setup to call ('get' or 'getboolean')
        :param default: If parameter not present and this is not None, return default.
        :param block: The block name to get parameter from. Default is the current selected block.
        :return: The value of parameter in selected block (or default, if provided and parameter not in block)
        """
        if not cls.initialized:
            raise cls.NotInitialized()

        # Get the block, either passed to the function or the default
        block = block or cls.singleton.selected_block

        override = cls.singleton.overrides.get(parameter)
        if override:
            value = override
        else:
            if not cls.singleton.has_option(parameter):
                if default is not None:
                    return default
                else:
                    raise ValueError("%s block does not have the option %s" % (block, parameter))
            value = getattr(cls.singleton.setup, get_method)(block, parameter)
        return value

    @classmethod
    def has_option(cls, option, block=None):
        if not cls.initialized:
            raise cls.NotInitialized()

        block = cls.singleton.selected_block if block is None else block  # set the default
        return cls.singleton.setup.has_option(block, option)

    @classmethod
    def items(cls, block=None):
        if not cls.initialized:
            raise cls.NotInitialized()

        block = cls.singleton.selected_block if block is None else block  # set the default
        return cls.singleton.setup.items(block)

    @classmethod
    def _select_and_verify_overlay(cls, **kwargs):
        """
        Wrapper to _select_overlay() that checks existence of the selected overlay file and raises if it is missing.
        :param kwargs: identical to those of _select_overlay()
        :return: The path of the selected overlay file.
        """
        overlay_file = cls._select_overlay(**kwargs)
        if overlay_file and not os.path.exists(overlay_file):
            cls.MissingIniFile("Selected overlay ini file does not exist: %s" % overlay_file)
        return overlay_file

    @classmethod
    def _select_overlay(cls, local_file=None, provided_file=None, commissioning_file=None):
        """
        Determines which of the up to 3 specified ini files should be used for overlaying on the defaults.
        :param local_file: a current working dir ini file
        :param provided_file: a ini file provided to SetupParser
        :param commissioning_file: the ini file in the directory this experiment was commissioned from
        :return: The path of the selected overlay file.
        """
        if provided_file:
            overlay_file = provided_file
        elif local_file:
            overlay_file = local_file
        elif commissioning_file:
            overlay_file = commissioning_file
        else:
            overlay_file = None
        return overlay_file

    @classmethod
    def load_schema(cls):
        json_schema = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_schema.json")))
        cls.singleton.schema = json_schema
        return json_schema

    # used for running a bit of code with a different selected block and ensuring a return to the original selected block
    class TemporaryBlock(object):
        def __init__(self, temporary_block):
            self.temporary_block = temporary_block

        def __enter__(self):
            self.original_block = SetupParser.selected_block
            SetupParser.override_block(self.temporary_block)

        def __exit__(self, exc_type, exc_val, exc_tb):
            SetupParser.override_block(self.original_block)
