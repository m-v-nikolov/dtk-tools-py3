import os

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.generic.geography import convert_filepaths
from .sweep import Builder

class RegressionSuiteBuilder(Builder):

    def __init__(self, names):
        self.regression_path=os.path.join( DTKSetupParser().get('BINARIES','dll_path'),
                                           '..','..','Regression' )
        self.mod_generator=(self.add_test(n) for n in names)

    def add_test(self,test_name):
        m=Builder.ModList()

        def configure(cb):
            Builder.metadata.update({'Config_Name': test_name})
            test=DTKConfigBuilder.from_files(
                   os.path.join(self.regression_path,test_name,'config.json'),
                   os.path.join(self.regression_path,test_name,'campaign.json'))
            convert_filepaths(test.config['parameters'])
            cb.copy_from(test)

        m.append(configure)

        return m