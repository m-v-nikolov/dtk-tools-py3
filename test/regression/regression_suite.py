from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.regression import RegressionSuiteBuilder

test_names=['27_Vector_Sandbox',
            '10_Vector_Namawala_Oviposition']

cb = DTKConfigBuilder()
builder = RegressionSuiteBuilder(test_names)

run_sim_args =  { 'config_builder' : cb,
                  'exp_builder'    : builder,
                  'exp_name'       : 'Regression Suite' }