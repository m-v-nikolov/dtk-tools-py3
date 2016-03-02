Python CalibTool v1.1
Jaline Gerardin, Nov 2015

Revised Nov 2015 for most recent version of refactored Python DTK
tools, improved handling of current simulation status, configuring
sampling over certain campaign parameters, configuring sampling over
drug and vector species parameters, averaging over multiple random
seeds, shifting from dicts to dataframes, and easier management of
study sites and analyzers.

Requires Python 2.7, NumPy, pandas, matplotlib, seaborn, SciPy (for
likelihood calculators and IMIS), python dtk tools (for malaria
simulations), COMPS (for HPC jobs via python dtk tools)

1. Overview 
2. Setting up and running CalibTool 
   a. Setting up CalibTool
   b. Setting up parameter sampling
   c. Setting up study sites
3. CalibTool outputs
4. Adding a new malaria site or analyzer 
5. Modifying updater for a new parameter sampling method
6. Running outside python dtk tools


*******************************************************************
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
sim_type = 'MALARIA_SIM' in calibtool settings and depends on the
python dtk toolkit for running the dtk. The user must specify "study
sites" to set up configs and campaigns as appropriate for their
calibration.

The analyzer retrieves output data and calculates a score for each
parameter set. Individual analyzer type(s) for each simulated study
site are specified by the user. A study site may have multiple
analyzers and several study sites may use the same analyzer. Analyzers
can be weighted for each site. Reference data necessary to calculate
scores must also be specified by the user.

The parameter updater uses the scores calculated by the analyzer to
select parameters to be sampled on the next iteration. Currently IMIS
and a dummy updater are available for this function.

The visualizer constructs plots of calibration progress. It generates
a plot of score vs parameter value for each parameter under
consideration. It also calls analyzer-specific visualizers to compare
reference data with simulation data.

These four modules are called by calibration_manager.py. Each module
(other than the visualizer, which currently always runs) checks
whether it has already been completed and resumes from the earliest
uncompleted step.


*******************************************************************
2. Setting up and running CalibTool

Run from the command line as follows:
% python ./calibration_manager.py OVERLAY_FILENAME

**************************************************
a. Setting up CalibTool

CalibTool requires a number of user-configurable settings, which are
specified by default in calibration_defaults.json. The user may
optionally provide overlays, also in json format.

expname : a name for this calibration experiment. If an expname has
already been run, CalibTool will resume the old experiment rather than
start a new one, so if you want to re-run from the beginning with the
same name, be sure to delete the old experiment directory.

sites : format { "sitename1" : ["analyzer1", "analyzer2", ...] ,
      	         "sitename2" : ["analyzer1", "analyzer3", ...], ... }
Specifies the study sites to be run in this calibration and the
analyzer(s) to be used for each study site. The site names and
analyzers must correspond to sites and analyzers set up in
study_sites.site* scripts. See section c "Setting up study sites"
for details on setting up study sites and analyzers.

run_location : "" for local simulation, "--hpc" for HPC (through
COMPS)

hpc_priority : HPC priority for COMPS

sim_type : "MALARIA_SIM" is currently the only sim type with
functionality

sim_runs_per_param_set : number of random seeds to run per site per
sampled parameter set

combine_site_likelihoods : 1 if yes, 0 if no. Set to 1 for classic
calibration with IMIS.

weight_by_site : format { "sitename1" : {"analyzer1" : weight1}, 
	       	 	  	      	{"analyzer2" : weight2"}, ...,
	       	 	  "sitename2" : {"analyzer3" : weight3}, ... }

num_to_plot : number of highest-likelihood parameter samples to plot
with visualizer

num_initial_samples : number of initial parameter samples

num_samples_per_iteration : number of samples per iteration

num_resamples : number of IMIS resamples per iteration

max_iterations : maximum number of iterations

initial_sampling_type : "LHC" for Latin hypercube, other types not
supported

initial_sampling_range_file : path of file specifying parameters over
which to sample. See part (b) below for how to set up this file.

dtk_path : path of python dtk tools

dtk_setup_config : path of dtk_setup.cfg file

calibtool_dir : path of calibtool script directory (where this README
is located)

working_dir : working directory where calibtool outputs will be stored

ERROR : a small number


**************************************************
b. Setting up parameter sampling

Parameters over which sampling will occur are specified in a .csv
file. Columns: "parameter" name of parameter, "max" maximum prior,
"min" minimum prior, "type" is "linear" for linear sampling over prior
range and "log" for log sampling over prior range; append "_int" to
type if DTK expects the parameter to be an int not float.

All un-nested config parameters are currently supported for sampling.

For nested config parameters, malaria drug params and vector species
params are supported:

For drug params, parameter names should be formatted as
DRUG.Drugname.DrugParameter, for example
DRUG.Artemether.Drug_Adherence_Rate

For vector species, VECTOR.Species.SpeciesParameter, for example
VECTOR.arabiensis.Acquire_Modifier; Required_Habitat_Factor is also
supported as, for example,
VECTOR.arabiensis.Required_Habitat_Factor.TEMPORARY_RAINFALL

For campaigns, habitat scaling by node is supported as
HABSCALE.nodeID, for example HABSCALE.114 to scale all habitats in
node 114.

Drug campaign coverage is supported as
CAMPAIGN.DRUG.CampaignCode.StartDay, for example
CAMPAIGN.DRUG.MSAT_AL.100 will administer MSAT with AL on day 100 with
coverage sampled as specified by "max", "min", and "type". The
campaign code must be defined in
dtk.interventions.malaria_drugs.add_drug_campaign.

At this time, no other campaign parameters are supported.


**************************************************
c. Setting up study sites

Study site configs, campaigns, analyzers, and reference data for
comparison are set up in study_sites.site* python scripts. Each site
named in the CalibTool settings field "sites" must have a
corresponding study_sites.site* script. study_sites.site_TEMPLATE.py
is available as a template for building new sites.

Within the study_sites.site* script, setup_functions lists
site-specific changes to the default config built by the dtk tools. As
set_geography() is not called at any point in building a site in
CalibTool, demographics and climate filenames must be specified in
setup_functions. Site-specific campaigns that are not under
calibration, such as baseline health-seeking or input EIR, should also
be listed in setup_functions as calls to the dtk tools functions that
set them up; same with specifying reporters. Campaign and reporter
setup functions should be imported from
study_sites.site_setup_functions.py.

analyzers is a dict of dicts that defines what analyzers are available
for each study site and configures settings for each analyzer,
including an analyzer name that must match an analyzer in the
analyzers/ directory, the DTK output to be parsed (Spatial Report,
Inset Chart, Summary Report, Survey Report), field(s) within the
reporter to be grabbed, likelihood function for comparing sim data to
reference data, and any other parameters needed for a custom analyzer.

reference data is a dict where each key is a type of data, for example
"prevalence_by_age" or "density_by_age_and_season". Analyzers access
reference data in a highly customized way, so there's a lot of
flexibility in how the reference data is set up.

See site_Dapelogo, site_Laye, and site_BFdensity for examples where
two sites share similar config, campaign, and analyzer setups but
different reference data.


*******************************************************************
3. CalibTool outputs

CalibTool stores outputs in the expname/ directory in the working
directory specified in the calibration settings json. For each
iteration, data is stored in expname/iterX where X is the iteration
number indexed from 0. Plots are dumped in expname/_plots/.

CalibTool saves the experiment's calibration settings in
expname/settings.json and analyzer settings in
expname/analyzers.json. If an experiment is resumed, the settings
stored here will be used.

A copy of the parameter sampling csv (initial sampling range file) is
copied to expname/iter0/.

CalibTool concatenates all sampled parameters and log likelihoods in
to expname/LL_all.csv after each iteration.

For each iteration X, CalibTool saves the following files in
expname/iterX/ :

imis.json : initial state of the IMIS object

params.csv : sampled values for all parameters under calibration

sim.json : python dtk tools simulation object

params_withpaths.csv : for each parameter set, lists output
directories of each simulation (site x random seed)

parsed_SITENAME.json : parsed data for each analyzer of each site,
ready to be used by analyzer scripts

SITENAME_ANALYZERNAME.json : (optional) output generated by analyzer,
to be used by visualizer

LL.csv : sampled parameters with log likelihoods and output
directories

LL_PARAMNAME.pdf : visualization of log likelihood vs sampled
parameter values


*******************************************************************
4. Adding a new malaria site or analyzer

Addition of a new site requires adding a site_NEWSITE.py script to
study_sites/. A site_TEMPLATE.py is available as starting
material. See part 2c, setting up study sites, for what needs to go in
site_NEWSITE.py.

Addition of a new analyzer requires adding an analyze_NEWANALYZER.py
script to analyzers/. An analyze_TEMPLATE is available as starting
material.

Each analyze_NEWANALYZER should return log likelihood for one
parameter set on one study site. If multiple comparisons to reference
data are necessary for each site, use multiple analyzers or handle all
comparisons within the same analyzer. For example, in
analyze_seasonal_monthly_density_cohort, the final log likelihood
score coming out of the analyzer combines 6 likelihoods: parasite and
gametocyte densities each at 3 seasons. Several likelihood calculators
are available in LL_calculators.py.

If a new reporter type is being used (not Spatial Report, Inset Chart,
Malaria Summary Report, or Malaria Survey Report), you will need to
update parsers_malaria.py to properly parse the new reporter.

New visualizations can be set up in the analyze_NEWANALYZER.py script.


*******************************************************************
5. Modifying updater for new parameter sampling method

The script containing instructions for selecting the next round of
parameters is next_parameters.py. Any new updater should be called
from update_params() in this script using a keyword specified here and
in the calibration manager.

next_parameters.py includes a box_prior_generator() that generates a
prior function from the list of parameters and ranges specified by the
user.



*******************************************************************
6. Running outside python dtk tools

Modify run_one_simulation() in calibration_manager.py appropriately
for new method of running sims. At this time, analyze.py and
visualize.py also require sim type to be MALARIA_SIM.

If IMIS is still being used, there is no need to modify
next_parameters.py as long as analyzer output continues to be stored
in the same format (LL.csv).
