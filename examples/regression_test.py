import os
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.core.DTKSetupParser import DTKSetupParser

setup=DTKSetupParser()
regression_path=os.path.join( setup.get('BINARIES','dll_path'),
                              '..','..','Regression' )
test_name='27_Vector_Sandbox'

cb = DTKConfigBuilder.from_files(os.path.join(regression_path,test_name,'config.json'),
                                 os.path.join(regression_path,test_name,'campaign.json'))

run_sim_args =  { 'config_builder' : cb,
                  'exp_name'       : test_name }