Overview
-------------------------------------

The Python CalibTool is a modular toolkit for parameter
optimization. It consists of 4 parts :

    1. simulation runner
    2. analyzer
    3. parameter updater
    4. visualizer

The simulation runner takes a list of parameter sets and site
configurations and runs simulations locally or on HPC. It checks for
job status periodically. As written, the simulation runner requires
``sim_type = 'MALARIA_SIM'`` in calibtool settings and depends on Edward's
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