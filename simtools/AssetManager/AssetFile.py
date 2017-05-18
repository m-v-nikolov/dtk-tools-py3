import hashlib
import os

class AssetFile(object):
    """
    This class represents a single file in an AssetCollection.
    """
    def __init__(self, filename):
        """
        :param filename: MUST be relative to the expected simulation Assets dir. e.g. SIM_DIR/Assets/<<<a/b/c.json>>>
        """
        self.filename = os.path.realpath(os.path.abspath(filename)) # local filename
        self.name = os.path.basename(filename)            # the (base)name of the file in the SIM_DIR/Assets dir
        self.assets_filename = filename                   # relative filename in the SIM_DIR/Assets dir
        self.assets_directory = os.path.dirname(filename) # directory of file in SIM_DIR/Assets
        self.checksum = hashlib.md5(open(self.filename, 'rb').read()).digest() # from stackoverflow :)
