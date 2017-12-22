# Execute directly: 'python example_optimization.py'
# or via the calibtool.py script: 'calibtool run example_optimization.py'

from calibtool.algorithms.OptimTool import OptimTool
from calibtool.algorithms.OptimToolPSPO import OptimToolPSPO
from calibtool.algorithms.OptimToolSPSA import OptimToolSPSA

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser

from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.plotters.OptimToolSPSAPlotter import OptimToolSPSAPlotter

try:
    from malaria.study_sites.DielmoCalibSite import DielmoCalibSite
except ImportError as e:
    message = "The malaria package needs to be installed before running this example...\n" \
              "Please run `dtk get_package malaria -v HEAD` to install"
    raise ImportError(message)

SetupParser.default_block = 'HPC'

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

sites = [DielmoCalibSite()]

plotters = [LikelihoodPlotter(combine_sites=True),
            SiteDataPlotter(num_to_plot=5, combine_sites=True),  # 10
            OptimToolSPSAPlotter()]  # OTP must be last because it calls gc.collect()

# Antigen_Switch_Rate (1e-10 to 1e-8, log)
# Falciparum_PfEMP1_Variants (900 to 1700, linear int)
# Falciparum_MSP_Variants (5 to 50, linear int)

# The following params can be changed by stopping 'calibool', making a modification, and then resuming.
# Things you can do:
# * Change the min and max, but changing the guess of an existing parameter has no effect
# * Make a dynamic parameter static and vise versa
# * Add and remove (needs testing) parameters
params = [
    {
        'Name': 'Clinical Fever Threshold High',
        'Dynamic': True,
        # 'MapTo': 'Clinical_Fever_Threshold_High', # <-- DEMO: Custom mapping, see map_sample_to_model_input below
        'Guess': 1.75,
        'aprioriHessian': -1,  # set zero if there is no information of Hessian
        'Min': 0.5,
        'Max': 2.5
    },
    {
        'Name': 'MSP1 Merozoite Kill Fraction',
        'Dynamic': False,  # <-- NOTE: this parameter is frozen at Guess
        'MapTo': 'MSP1_Merozoite_Kill_Fraction',
        'Guess': 0.65,
        'aprioriHessian': -1,  # set zero if there is no information of Hessian
        'Min': 0.4,
        'Max': 0.7
    },
    {
        'Name': 'Falciparum PfEMP1 Variants',
        'Dynamic': True,
        'MapTo': 'Falciparum_PfEMP1_Variants',
        'Guess': 1500,
        'aprioriHessian': -1,  # set zero if there is no information of Hessian
        'Min': 1,  # 900 [0]
        'Max': 5000  # 1700 [1e5]
    },
    {
        'Name': 'Min Days Between Clinical Incidents',
        'Dynamic': False,  # <-- NOTE: this parameter is frozen at Guess
        'MapTo': 'Min_Days_Between_Clinical_Incidents',
        'Guess': 25,
        'aprioriHessian': -1,  # set zero if there is no information of Hessian
        'Min': 1,
        'Max': 50
    },
]


def constrain_sample(sample):
    # Convert Falciparum MSP Variants to nearest integer
    if 'Min Days Between Clinical Incidents' in sample:
        sample['Min Days Between Clinical Incidents'] = int(round(sample['Min Days Between Clinical Incidents']))

    return sample


def map_sample_to_model_input(cb, sample):
    tags = {}

    # Can perform custom mapping, e.g. a trivial example
    if 'Clinical Fever Threshold High' in sample:
        value = sample.pop('Clinical Fever Threshold High')
        tags.update(cb.set_param('Clinical_Fever_Threshold_High', value))

    for p in params:
        if 'MapTo' in p:
            if p['Name'] not in sample:
                print("Warning: {} not in sample, perhaps resuming previous iteration".format(p['Name']))
                continue
            value = sample.pop(p['Name'])
            tags.update(cb.set_param(p['Name'], value))

    for name, value in sample.items():
        print("UNUSED PARAMETER: {}".format(name))
    assert (len(sample) == 0)  # All params used

    # Run for 10 years with a random random number seed
    tags.update(cb.set_param('Simulation_Duration', 3650+1))  # 10*365
    tags.update(cb.set_param('Run_Number', random.randint(0, 1e6)))

    return tags


optimtool = OptimToolPSPO(params=params,
                          constrain_sample_fn=constrain_sample,  # <-- WILL NOT BE SAVED IN ITERATION STATE
                          comps_per_iteration=4  # <-- computations per iteration, includes center repeats.
                          )
calib_manager = CalibManager(name='ExampleOptimizationSPSA',  # <-- Please customize this name
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sites=sites,
                             next_point=optimtool,
                             sim_runs_per_param_set=1,  # <-- Replicates
                             max_iterations=3,  # <-- Iterations
                             plotters=plotters)

run_calib_args = {}

if __name__ == "__main__":
    SetupParser.init()
    calib_manager.run_calibration()
