Python CalibTool v1.0
Jaline Gerardin, Feb 2015
Revised Apr 2015 for most recent version of trunk and refactored
Python DTK tools

Requires Python 2.7, NumPy, Matplotlib, SciPy (for likelihood
calculators and IMIS), Edward's python tools (for malaria
simulations), COMPS-enabled shell (for HPC jobs via Edward's python
tools)

1. Overview 
2. Running CalibTool 
3. Adding a new malaria site or analyzer 
4. Modifying updater for new parameter sampling method
5. Running outside Edward's python tools



1. Overview

The Python CalibTool is a modular toolkit for parameter
optimization. It consists of 4 parts :

    1. simulation runner
    2. analyzer
    3. parameter updater
    4. visualizer

The simulation runner takes a list of parameter sets and site
configurations and runs simulations locally or on HPC. It checks for
job status periodically. As written, the simulation runner requires
sim_type = 'MALARIA_SIM' in calibtool settings and depends on Edward's
python toolkit for running the dtk.

The analyzer retrieves output data and calculates a score for each
parameter set. Individual analyzer types are specified in calibtool
settings and are listed for each simulated site.

The parameter updater uses the scores calculated by the analyzer to
select parameters to be sampled on the next iteration. Currently IMIS
and a dummy updater are available for this function.

The visualizer constructs plots of calibration progress and is
currently called for each iteration. It generates a plot of score vs
parameter value for each parameter under consideration. It also calls
site-specific visualizers, which I have been using to visually compare
reference data with simulation data.

These four modules are called by calibration_manager.py. For easy
resuming of interrupted calibrations, each module (other than the
visualizer) checks whether it has already been completed. The
simulation runner checks only whether jobs have been submitted, not
run to completion.



2. Running CalibTool

Run from the command line as follows:
% python ./calibration_manager.py

The primary point of user manipulation is load_settings.py, which sets
up a dictionary including locations of local working directories, HPC
settings, local simulation settings, which sites to simulate, which
analyzers should be run for each site, any relative weights for each
site, iterative settings such as number of samples and max number of
iterations, and the file where the names and boundaries of sampled
parameters are listed. 

Parameters to be sampled over should be specified as follows in json
format:
{
    'Parameter_Name_1' : {
        'max' : max_value,
	'min' : min_value,
	'type' : PARAM_TYPE
	},
    ...
}
where PARAM_TYPE is a string specifying linear vs log sampling, and if
the parameter must be an integer. For example, a parameter to be
sampled over log space should have type 'log', a parameter sampled
over linear space but as an integer should have type 'linear_int',
etc.

load_settings.py also contains setup details for each
analyzer type. This includes the reporter from which data should be
gathered, relevant fields, and any other analyzer-specific settings
that will be needed for parsing and calculating likelihoods.

Each calibration experiment MUST have a unique name.

When setting up a new calibration experiment, load_settings.py will
save settings and analyzers to json files.

To resume a partially-completed calibration, set settings['expname']
in load_settings.py to the name of the calibration, then run
calibration_manager.py as normal. It is not necessary to cross-check
all remaining settings since load_settings.py will be loading the
settings.json and analyzers.json files from the appropriate experiment
directory.



3. Adding a new malaria site or analyzer

Addition of a new site requires editing 3 scripts in calibtool.

In load_settings.py, add the new site name to
settings['sites']. Select from an existing analyzer, or see below on
adding a new analyzer. If the site shouldn't be weighted 1 relative to
other sites, note the weight of each analyzer for the site in
settings['weight_by_site'].

In load_comparison_data.py, add the reference data for the site to the
datastruct dictionary.

Malaria simulations with Edward's python tools also require setting up
simulation settings for each geography. A json file containing
information on each geography's config, campaign, and reporter
settings is specified in load_settings(). In this file, add the new
site's information. If the new site uses a campaign other than input
EIR, health seeking, or challenge bite, a new line should be added to
set_geographies_campaigns() in geographies_calibration.py.

Addition of a new analyzer requires editing at least 2 scripts and
writing one new script.

In load_settings.py, in load_analyzers(), add setup info for the new
analyzer.

In analyzers.py, in analyze_malaria_sim(), add an elif for the new
analyzer.

Write the new analyzer to be called from analyzers.py. The
LL_calculators.py script contains a variety of likelihood calculators
to be called, or a new one can be added if needed. The new analyzer
should return a log likelihood.

If visualizers are desired, add an elif to visualizer.py's
visualize_malaria_sim() to call the new visualizer for the new
analyzer.



4. Modifying updater for new parameter sampling method

The script containing instructions for selecting the next round of
parameters is next_parameters.py. Any new updater should be called
from update_params() in this script using a keyword specified here and
in the calibration manager.

next_parameters.py includes a box_prior_generator() that generates a
prior function from the list of parameters and ranges specified by the
user.



5. Running outside Edward's python tools

Modify run_one_simulation() in calibration_manager.py appropriately
for new method of running sims. If you're running outside the python
tools, it's likely you're using new sites and analyzers, so update
geographies and initial parameter sampling files as well as
load_settings.py, load_comparison_data.py, analyzers.py, and
visualize.py accordingly. If IMIS is still being used, there is no
need to modify next_parameters.py as long as analyzer output continues
to be stored in the same format.
