# Execute directly: "python example_optimization_PBnB.py"
# or via the calibtool.py script: "calibtool run example_optimization_PBnB.py"

import random

try:
    from malaria.study_sites.DielmoCalibSite import DielmoCalibSite
except ImportError as e:
    message = "The malaria package needs to be installed before running this example...\n" \
              "Please run `dtk get_package malaria -v HEAD` to install"
    raise ImportError(message)

from calibtool.CalibManager import CalibManager
from calibtool.algorithms.PBnB.OptimTool_PBnB import OptimTool_PBnB, par
from calibtool.plotters.LikelihoodPlotter import LikelihoodPlotter
from calibtool.plotters.OptimToolPBnBPlotter import OptimToolPBnBPlotter
from calibtool.plotters.SiteDataPlotter import SiteDataPlotter
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser

SetupParser.default_block = "HPC"

cb = DTKConfigBuilder.from_defaults("MALARIA_SIM")

sites = [DielmoCalibSite()]

plotters = [LikelihoodPlotter(combine_sites=True),
            SiteDataPlotter(num_to_plot=5, combine_sites=True),
            OptimToolPBnBPlotter()]

params = [
    {
        "Name": "Clinical Fever Threshold High",
        "Dynamic": True,
        # "MapTo": "Clinical_Fever_Threshold_High", # <-- DEMO: Custom mapping, see map_sample_to_model_input below
        "Guess": 1.75,
        "Min": 0.5,
        "Max": 2.5
    },
    {
        "Name": "Falciparum PfEMP1 Variants",
        "Dynamic": True,
        "MapTo": "Falciparum_PfEMP1_Variants",
        "Guess": 1500,
        "Min": 1,  # 900 [0]
        "Max": 5000  # 1700 [1e5]
    },
]


def map_sample_to_model_input(cb, sample):
    tags = {}

    # Can perform custom mapping, e.g. a trivial example
    if "Clinical Fever Threshold High" in sample:
        value = sample.pop("Clinical Fever Threshold High")
        tags.update(cb.set_param("Clinical_Fever_Threshold_High", value))

    for p in params:
        if "MapTo" in p:
            if p["Name"] not in sample:
                print("Warning: {} not in sample, perhaps resuming previous iteration".format(p["Name"]))
                continue
            value = sample.pop(p["Name"])
            tags.update(cb.set_param(p["Name"], value))

    for name, value in sample.items():
        print("UNUSED PARAMETER: {}".format(name))
    assert (len(sample) == 0)  # All params used

    # Run for 10 years with a random random number seed
    tags.update(cb.set_param("Simulation_Duration", 3650+1))  # 10*365
    tags.update(cb.set_param("Run_Number", random.randint(0, 1e6)))

    return tags

name = "Example_Optimization_PBnB" # <-- Please customize this name

optimtool_PBnB = OptimTool_PBnB(params,
                                s_running_file_name=name,
                                s_problem_type="deterministic",  # deterministic or noise
                                f_delta=par.f_delta,  # <-- to determine the quantile for the target level set
                                f_alpha=par.f_alpha,  # <-- to determine the quality of the level set approximation
                                i_k_b=par.i_k_b,  # <-- maximum number of inner iterations
                                i_n_branching=par.i_n_branching,  # <-- number of branching subregions
                                i_c=par.i_c,  # <--  increasing number of sampling points ofr all
                                i_replication=par.i_replication,  # <-- initial number of replication
                                i_stopping_max_k=par.i_stopping_max_k,  # <-- maximum number of outer iterations
                                i_max_num_simulation_per_run=par.i_max_num_simulation_per_run,
                                # <-- maximum number of simulations per iteration
                                f_elite_worst_sampling_para=par.f_elite_worst_sampling_para)  # <-- parameters that determine the number of simulation runs for elite and worst subregions

calib_manager = CalibManager(name=name,
                             config_builder=cb,
                             map_sample_to_model_input_fn=map_sample_to_model_input,
                             sites=sites,
                             next_point=optimtool_PBnB,
                             sim_runs_per_param_set=1,  # <-- Replicates
                             max_iterations=30,  # <-- Iterations
                             plotters=plotters)

run_calib_args = {'calib_manager': calib_manager}

if __name__ == "__main__":
    SetupParser.init()
    calib_manager.run_calibration()
