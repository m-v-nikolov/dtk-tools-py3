# Execute directly: 'python example_optimization.py'
# or via the calibtool.py script: 'calibtool run example_optimization.py'
import copy
import math
import random

from malaria.reports.MalariaReport import add_habitat_report
from scipy.special import gammaln

from calibtool.CalibManager import CalibManager
from calibtool.algorithms.OptimTool import OptimTool
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPlotter import OptimToolPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.reports.CustomReport import BaseVectorStatsReport
from dtk.vector.species import set_larval_habitat
from simtools.SetupParser import SetupParser

try:
    from malaria.study_sites.MagudeEntoCalibSite import MagudeEntoCalibSite
except ImportError as e:
    message = "The malaria package needs to be installed before running this example...\n" \
                "Please run `dtk get_package malaria -v HEAD` to install"
    raise ImportError(message)

# Which simtools.ini block to use for this calibration
SetupParser.default_block = 'LOCAL'

# Start from a base MALARIA_SIM config builder
# This config builder will be modify by the different sites defined below
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
# cb.set_collection_id('a7f64605-2a05-e811-9415-f0921c16b9e5') # COMPS


# List of sites we want to calibrate on
specs = ['funestus']
sites = [MagudeEntoCalibSite()]

# The default plotters used in an Optimization with OptimTool
plotters = [LikelihoodPlotter(combine_sites=True),
            SiteDataPlotter(num_to_plot=5, combine_sites=True),
            OptimToolPlotter()  # OTP must be last because it calls gc.collect()
]

params1 = [
    {
        'Name': '%s%i' %(species, i),
        'Dynamic': True,
        'Guess': 0.5,
        'Min': 0.1,
        'Max': 40,
}
    for species in specs
    for i in range(1, 13)
]

params2 = [
    {
        'Name': '%s_max' %(species),
        'Dynamic': True,
        'Guess': 5,
        'Min': 2,
        'Max': 6,
    }
    for species in specs
]

params = params1 + params2
hab_type = {'gambiae': 'TEMPORARY_RAINFALL', 'funestus': 'WATER_VEGETATION'}
hab_val = {'gambiae': 2.2e7, 'funestus': 2e6}


def map_sample_to_model_input(cb, sample):
    tags = {}

    for species in specs:
        # Updating Spline values
        hab = {species: {
            hab_type[species]: hab_val[species],
            "LINEAR_SPLINE": {
                "Capacity_Distribution_Per_Year": {
                    "Times": [0.0, 30.417, 60.833, 91.25, 121.667, 152.083, 182.5, 212.917, 243.333, 273.75, 304.167,
                              334.583],
                    "Values": [0.0, 0.0, 0.0, 0.0, 0.2, 1.0, 1.0, 1.0, 0.5, 0.2, 0.0, 0.0]
                },
                "Max_Larval_Capacity": 1e8
            }}}
        for i in range(1, 13):
            name = '%s%i' %(species, i)
            if name in sample:
                splinevalue = sample.pop(name)

                hab[species]['LINEAR_SPLINE']['Capacity_Distribution_Per_Year']['Values'][i-1] = splinevalue
                tags.update({name: splinevalue})

        # Updating max habitat values
        max_habitat_name = '%s_max' % species
        if max_habitat_name in sample:
            maxvalue = sample.pop(max_habitat_name)
            hab[species]['LINEAR_SPLINE']['Max_Larval_Capacity'] = pow(10, maxvalue)
            tags.update({max_habitat_name: maxvalue})

        set_larval_habitat(cb, hab)

    for name,value in sample.items():
        print('UNUSED PARAMETER:'+name)
    assert( len(sample) == 0 ) # All params used

    # For testing only, the duration should be handled by the site !! Please remove before running in prod!
    tags.update(cb.set_param("Simulation_Duration", 2*365))
    tags.update(cb.set_param('Run_Number', 0))

    return tags

cb.update_params({'Demographics_Filenames': ['Calibration/single_node_demographics.json'],

                      'Antigen_Switch_Rate': pow(10, -9.116590124),
                      'Base_Gametocyte_Production_Rate': 0.06150582,
                      'Base_Gametocyte_Mosquito_Survival_Rate': 0.002011099,
                      'Base_Population_Scale_Factor': 1,

                      "Birth_Rate_Dependence": "FIXED_BIRTH_RATE",
                      "Climate_Model": 'CLIMATE_CONSTANT',

                      "Death_Rate_Dependence": "NONDISEASE_MORTALITY_BY_AGE_AND_GENDER",
                      "Disable_IP_Whitelist": 1,

                      "Enable_Vital_Dynamics": 1,
                      "Enable_Birth": 1,
                      'Enable_Default_Reporting': 1,
                      'Enable_Demographics_Other': 1,
                      # 'Enable_Property_Output': 1,

                      'Falciparum_MSP_Variants': 32,
                      'Falciparum_Nonspecific_Types': 76,
                      'Falciparum_PfEMP1_Variants': 1070,
                      'Gametocyte_Stage_Survival_Rate': 0.588569307,

                      'MSP1_Merozoite_Kill_Fraction': 0.511735322,
                      'Max_Individual_Infections': 3,
                      'Nonspecific_Antigenicity_Factor': 0.415111634,

                      'x_Temporary_Larval_Habitat': 1,
                      'logLevel_default': 'ERROR',

                      "Vector_Species_Names": specs
                      })

# Just for fun, let the numerical derivative baseline scale with the number of dimensions
volume_fraction = 0.05   # desired fraction of N-sphere area to unit cube area for numerical derivative (automatic radius scaling with N)
num_params = len([p for p in params if p['Dynamic']])
r = math.exp(1/float(num_params)*(math.log(volume_fraction) + gammaln(num_params/2.+1) - num_params/2.*math.log(math.pi)))

optimtool = OptimTool(params,
    mu_r = r,           # <-- radius for numerical derivatve.  CAREFUL not to go too small with integer parameters
    sigma_r = r/10.,    # <-- stdev of radius
    center_repeats=1, # <-- Number of times to replicate the center (current guess).  Nice to compare intrinsic to extrinsic noise
    samples_per_iteration=2  # 32 # <-- Samples per iteration, includes center repeats.  Actual number of sims run is this number times number of sites.
)


# cb.add_reports(BaseVectorStatsReport(type='ReportVectorStats', stratify_by_species=1))

calib_manager = CalibManager(name='TestPandas',    # <-- Please customize this name
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sites=sites,
                             next_point=optimtool,
                             sim_runs_per_param_set=1,  # <-- Replicates
                             max_iterations=2,          # <-- Iterations
                             plotters=plotters)


run_calib_args = {
    "calib_manager":calib_manager
}

if __name__ == "__main__":
    SetupParser.init()
    cm = run_calib_args["calib_manager"]
    cm.run_calibration()
