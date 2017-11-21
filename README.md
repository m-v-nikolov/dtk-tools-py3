Documentation available: http://institutefordiseasemodeling.github.io/dtk-tools

The `dtk` package is intended to strengthen and simplify the interaction between researchers and the [EMOD model](https://institutefordiseasemodeling.github.io/EMOD/).

Modules contained in this package are intended to:
- Empower the user to configure diverse simulations and arbitrarily complex campaigns built up from a standardized library of configuration fragments and utility functions;
- Facilitate transparent switching between local and remote HPC commissioning, job-status queries, and output analysis;
- Enable the configuration of arbitrary collections of simulations (e.g. parameteric sweeps) through an extensible library of builder classes;
- Collect a library of post-processing analysis functionality, e.g. filtering, mapping, averaging, plotting.

#### Installation

To install the dtk-tools, first clone the repository:
```
git clone https://github.com/InstituteforDiseaseModeling/dtk-tools.git
```

Make sure you have **Python 3.6 x64** installed (available [here](https://www.python.org/downloads/)).

From a command-prompt, run the following from the **dtk-tools** directory:
```
python setup.py
```

**Note:** If `pip` command is not found on your system, make sure to add the Python scripts directory (by default in Windows: `C:\Python27\Scripts`)
to your `PATH` environment variable.

To test if dtk-tools is correctly installed on your machine issue a:
```
dtk -h
```
If the command succeed and present you with the details of the dtk command you are all set!


#### MAC users ####
Please refer to [MacOSX install instructions](http://institutefordiseasemodeling.github.io/dtk-tools/gettingstarted.html#id6) for more information.

#### CentOS7 users
Please refer to [CentOS install instructions](http://institutefordiseasemodeling.github.io/dtk-tools/gettingstarted.html#id3) for more information.


#### Setup

To configure your user-specific paths and settings for local and HPC job submission, please create a `simtools.ini` file in
the same folder that contains your scripts or modify the master `simtools.ini` at `dtk-tools/simtools/simtools.ini`

Simulation job management is handled through the various `dtk` command-line options, e.g. `dtk run example_sweep` or `dtk analyze example_plots`.  For a full list of options, execute `dtk --help`.  Many example configurations for simulation sweeps and analysis processing may be found in the `examples` directory.
