import hashlib
import os

from COMPS.Data.AssetCollectionFile import AssetCollectionFile as COMPSAssetCollectionFile

# ck4, deprecate this class in favor of direct access to COMPS AssetCollectionFile
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
        self.assets_directory = os.path.dirname(filename) # directory of file inside SIM_DIR/Assets
        self.checksum = hashlib.md5(open(self.filename, 'rb').read()).digest() # from stackoverflow :) # ck4, needed?

    # @classmethod
    # def from_COMPSAssetFile(cls, comps_asset_file):
    #     """
    #     Creates an AssetFile object from a COMPS Asset File object. Not all fields can be filled completely as a COMPS
    #     asset file may not exist locally on disk.
    #     :return: AssetFile object equivalent
    #     """
    #     # ck4, need to set everything needed to make this a superset of COMPSAssetFile
    #     raise Exception("unimplemented") # ck4
    #
    #
    # @classmethod
    # def to_COMPSAssetFile(cls, asset_file):
    #     """
    #     Creates an COMPS AssetFile object from an Asset File object
    #     :return: COMPS AssetFile object equivalent
    #     """
    #     return COMPSAssetCollectionFile(file_name=asset_file.name, relative_path=asset_file.filename)
