import os
from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder

# a class to build an suite of regression tests
class RegressionSuiteBuilder:

    def __init__(self, test_names):
        self.finished = False
        self.test_names = test_names
        self.test_idx = 0
        setup=DTKSetupParser()
        self.regression_path=os.path.join( setup.get('BINARIES','dll_path'),
                                           '..','..','Regression' )

    def next_sim(self, config_builder):
        test_name=self.test_names[self.test_idx]
        self.next_params = {'Config_Name': test_name}


        # TODO: Consider refactoring builders
        #       as generators that "yield" ConfigBuilder a object
        #       after getting a "send" of the base configuration.
        #       Replace "while not self.exp_builder.finished"
        #       with something like "for cb in self.exp_builder.next_sim()"

        test_config=DTKConfigBuilder.from_files(
                        os.path.join(self.regression_path,test_name,'config.json'),
                        os.path.join(self.regression_path,test_name,'campaign.json'))
        config_builder.update_params(test_config.config['parameters'])
        for e in test_config.campaign['Events']:
            config_builder.add_event(e)

        # TODO: The Geography concept is clunky and should probably just go

        for k,v in config_builder.config['parameters'].items():
            if 'Filename' in k:
                config_builder.set_param(k,'/'.join([config_builder.get_param('Geography'),v]))

        config_builder.update_params(self.next_params)

        self.test_idx += 1
        if self.test_idx == len(self.test_names):
            self.finished = True