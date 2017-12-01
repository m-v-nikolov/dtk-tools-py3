import json
import os
import fasteners

from simtools.Utilities.BetterConfigParser import BetterConfigParser
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
            return None

    @classmethod
    @fasteners.interprocess_locked(os.path.join(current_dir, '.setup_parser_init_lock'))
    def init(cls, selected_block=None, **kwargs):
        """
        Initialize the SetupParser singleton
        :param selected_block:
        :param kwargs: See __init__ for parameter list
        :return: Nothing.
        """
        # Do not allow reinitialization except if we pass a singleton, just take it
        if SetupParser.initialized and not kwargs.get('singleton'):
            raise SetupParser.AlreadyInitialized("Cannot re-initialize the SetupParser class")

        if kwargs.get('singleton', None):
            cls.singleton = kwargs.get('singleton')
        else:
            if not kwargs.get('old_style_instantiation', None):
                kwargs['old_style_instantiation'] = False
            cls.singleton = SetupParser(selected_block=selected_block, **kwargs)
        cls.initialized = True
        cls.singleton.validate()

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


class SetupParser(metaclass=SetupParserMeta):
    """
    Parse user settings and directory locations
    from setup configuration file: simtools.ini

    SetupParser is a singleton whose values can only be set once. It should be accessed directly as a class and never
    instantiated. This is to provide a homogeneous, unchanging view of its configuration.
    """

    class MissingIniFile(Exception): pass

    class MissingIniBlock(Exception): pass

    class AlreadyInitialized(Exception): pass

    class NotInitialized(Exception):
        DEFAULT_MSG = "SetupParser must first be called with .init() ."

        def __init__(self, msg=None):
            self.msg = msg if msg else self.DEFAULT_MSG

        def __str__(self):
            return self.msg

    class InvalidBlock(Exception): pass

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
        :param overrides: The values in this dict supersede those returned by the ConfigParser object in .get()
        :param is_testing: Allows bypassing of interactive login to COMPS if True. No login attempt is made in this case.
        """
        if old_style_instantiation is None:
            self.old_style_instantiation(selected_block=selected_block, setup_file=setup_file,
                                         commissioning_directory=commissioning_directory, overrides=overrides,
                                         is_testing=is_testing)

        self.selected_block = (selected_block or self.default_block).upper()
        self.setup_file = setup_file
        self.commissioning_directory = commissioning_directory
        self.commissioning_file = os.path.join(commissioning_directory, self.ini_filename) if commissioning_directory else None

        local_file = os.path.join(os.getcwd(), self.ini_filename)
        self.local_file = local_file if os.path.exists(local_file) else None
        self.overrides = overrides

        # Identify which ini file will overlay the default ini, if any, and verify the selected file's existence
        if not os.path.exists(self.default_file):
            raise self.MissingIniFile("Default ini file does not exist: %s . Please run 'python setup.py' again." % self.default_file)

        self.overlay_path = self._select_and_verify_overlay(local_file=self.local_file, provided_file=self.setup_file,
                                                            commissioning_file=self.commissioning_file)

        # Load the default file
        self.setup = self.config_parser_from_file(self.default_file)

        # Apply the overlay if one was found
        if self.overlay_path:
            overlay = self.config_parser_from_file(self.overlay_path)
            self.setup = self._overlay_setup_and_resolve_inheritance(overlay, self.setup)

        # Verify that we have the requested block in our overlain result
        if not self.setup.has_section(self.selected_block):
            raise self.MissingIniBlock("Selected block: %s does not exist in ini file overlay.\nOverlay path: %s"
                                       % (self.selected_block, self.overlay_path))

        # If the selected block is type=HPC, take care of HPC initialization
        if self.setup.get(self.selected_block, 'type') == "HPC" and not is_testing:
            from simtools.Utilities.COMPSUtilities import COMPS_login
            COMPS_login(self.setup.get(self.selected_block, 'server_endpoint'))

    def validate(self):
        """
        Validate the configuration.
        """
        # Make sure we dont have both collection and local path specified
        from simtools.AssetManager.SimulationAssets import SimulationAssets
        for ctype, local_path in SimulationAssets.SETUP_MAPPING.items():
            if self.get("base_collection_id_{}".format(ctype)) and self.get(local_path):
                print("Both the base_collection_id_{} and the {} attributes are specified in the simtools.ini file.".format(ctype, local_path))
                print("Please empty the value of one or the other as the tools cannot determine which one to use.")
                print("simtools.ini location: {}".format(self.overlay_path or self.default_file))
                exit()

    def config_parser_from_file(self, ini_file):
        """
        Create a config parser from a file.
        :param ini_file: The full path of the ini file to load
        :return: a configured ConfigParser with additional variables
        """
        if not os.path.exists(ini_file):
            raise Exception('No file found at %s' % ini_file)

        ret = BetterConfigParser()
        ret.read(ini_file)
        ret.set('DEFAULT', 'user', LocalOS.username)
        return ret

    def old_style_instantiation(self, selected_block, setup_file, commissioning_directory, overrides, is_testing):
        msg = "SetupParser(arguments) is deprecated. Please update your code to use SetupParser.init(arguments) " + \
              "exactly once. You may then use familiar SetupParser methods on the class, " + \
              "e.g. SetupParser.get('some_item')"
        logger.warning(msg)
        print(msg)

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
            raise cls.MissingIniBlock("Override setup block '%s' does not exist in the setup overlay." % block)

    def _merge_inherited_options(self, parser, current_block):
        """
        Merges options in the full block inheritance chain for current_block, with preference to keeping closer-to-the-tail
        (to current_block) values. Does NOT modify the provided parser.
        :param parser: Parser from which to obtain block information.
        :param current_block: The block to resolve/merge inherited options for.
        :return: the 'type' value for current_block and its full set of properly-merged options.
        """
        if not parser.has_option(current_block, 'type'):
            raise self.InvalidBlock('All simtools.ini blocks must have a \'type\'. Missing in block: %s' % current_block)

        block_type = parser.get(current_block, 'type')
        is_root_block = (current_block == block_type)

        if is_root_block:
            merged_options = {}
        else:
            # e.g. terminate recursion on block 'HPC' with type 'HPC'
            # continue down the inheritance chain
            parent = block_type
            if not parser.has_section(parent):
                raise self.InvalidBlock('simtools.ini block: %s is of type: %s, but there is no such block.'
                                        % (current_block, parent))
            block_type, merged_options = self._merge_inherited_options(parser, current_block=parent)

        # merge this current block's info on top of any results from deeper recursion results
        #
        # we absolutely must not let default values apply to any block EXCEPT 'name == type' blocks e.g. HPC/LOCAL
        # Inheritance takes care of the rest.
        # ... in other words ...
        # root blocks are allowed to report default values here, and all blocks are allowed to report non-default
        # values
        exclusion = not is_root_block
        for item in parser.items(section=current_block, exclude_default_value_items=exclusion):
            merged_options[item[0]] = item[1]
        return block_type, merged_options

    def resolve_type_inheritance(self, parser):
        """
        Merges simtools.ini block inheritance chains for a given block, setting its parser values. The 'type'
        key/parameter is INVERSELY inherited from the deepest member of block's inheritance chain.

        e.g. Resolves the type inheritance:
        [R]      [S]       [T]       [T RESULTS]
        type = R type = R  type = S  type = R
        a = 1                        a = 1
        b = 2    b = 3               b = 3
                 c = 4     c = 5     c = 5
        d = 6              d = 7     d = 7
        e = 8    e = 9     e = 10    e = 10
        :param parser: a parser object with blocks to modify/resolve inheritance for
        :return: the provided parser object
        """
        available_sections = parser.sections()
        for section in available_sections:
            # Recursively discover and apply/merge block keys
            block_type, merged_options = self._merge_inherited_options(parser=parser, current_block=section)

            # apply merged/inherited options
            for option,value in merged_options.items():
                parser.set(section, option, value)

            # reverse-apply 'type' (keep deepest-level value)
            parser.set(section, 'type', block_type)
        return parser

    def _overlay_setup_and_resolve_inheritance(self, master, slave):
        """
        Overlays the master ConfigParser on another the slave one and returns the result.
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

        :param master: The ConfigParser to overlay
        :param slave: The ConfigParger to overlay on
        :return Resulting ConfigParser
        """
        # Handle the defaults
        for item in master.defaults():
            slave.set('DEFAULT', item, master.get('DEFAULT', item))

        # Overlays all sections of master on slave
        for section in master.sections():
            if not master.has_option(section, 'type'):
                raise self.InvalidBlock(
                    'All simtools.ini blocks must have a \'type\'. Missing in block: %s' % section)
            section_type = master.get(section, 'type')
            is_root_section = (section == section_type)

            # The overlaid section doesnt exist in the setup -> create it
            if not slave.has_section(section):
                # Create the section
                slave.add_section(section)

            # Override the items
            #
            # we absolutely must not let default values apply to any block EXCEPT 'name == type' blocks e.g. HPC/LOCAL
            # Inheritance takes care of the rest.
            # ... in other words ...
            # root blocks are allowed to report default values here, and all blocks are allowed to report non-default
            # values
            exclusion = not is_root_section
            for item in master.items(section=section, exclude_default_value_items=exclusion):
                slave.set(section, item[0], item[1])

        slave = self.resolve_type_inheritance(slave)
        return slave

    @classmethod
    def get(cls, parameter, default=None, block=None):
        return cls._get_guts(parameter, 'get', default, block)

    @classmethod
    def getboolean(cls, parameter, default=None, block=None):
        return cls._get_guts(parameter, 'getboolean', default, block)

    @classmethod
    def set(cls, section, parameter, value):
        return cls.singleton.setup.set(section, parameter, value)

    @classmethod
    def _get_guts(cls, parameter, get_method, default="default_value", block=None):
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
                if default is not "default_value":
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

    class TemporaryBlock(object):
        """
            Used for running a bit of code with a different selected block
            and ensuring a return to the original selected block
        """
        def __init__(self, temporary_block):
            self.temporary_block = temporary_block

        def __enter__(self):
            self.original_block = SetupParser.selected_block
            SetupParser.override_block(self.temporary_block)

        def __exit__(self, exc_type, exc_val, exc_tb):
            SetupParser.override_block(self.original_block)

    class TemporarySetup(object):
        """
            Used for running a bit of code with a different selected block and ini path
        """
        def __init__(self, temporary_block=None, temporary_path=None):
            self.temporary_block = temporary_block or SetupParser.default_block
            # Replace the temporary path with the current setup_file if it is not passed or not existing
            if not temporary_path or not os.path.exists(temporary_path):
                temporary_path = SetupParser.setup_file if hasattr(SetupParser, 'setup_file') else None

            self.temporary_setup = SetupParser(selected_block=temporary_block,
                                               setup_file=temporary_path,
                                               old_style_instantiation=True)

        def get(self, parameter, default=None):
            try:
                return self.temporary_setup.setup.get(self.temporary_block, parameter)
            except:
                return default

        def getboolean(self, parameter):
            return self.temporary_setup.setup.getboolean(self.temporary_block, parameter)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
