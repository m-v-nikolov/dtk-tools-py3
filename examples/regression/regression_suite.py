import os
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.RegressionSuiteBuilder import RegressionSuiteBuilder
from dtk.interventions.empty_campaign_cff import empty_campaign

test_names=['27_Vector_Sandbox',
            '10_Vector_Namawala_Oviposition']

cb = DTKConfigBuilder(config={'parameters':{}},campaign=empty_campaign)
builder = RegressionSuiteBuilder(test_names)

run_sim_args =  { 'config_builder' : cb,
                  'exp_builder'    : builder,
                  'exp_name'       : 'Regression Suite' }