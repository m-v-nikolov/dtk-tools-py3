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

Please refer to [MacOS install instructions](http://institutefordiseasemodeling.github.io/dtk-tools/gettingstarted.html#id6) for more information.

Tested with macOS Sierra (Version 10.12)

Make sure you have the Xcode Command Line Tools installed:
```
xcode-select --install
```

By default, MAC will install Python 2.7.10 for system use and users may not have certain permissions to upgrade some packages. We will leave the system Python unchanged and install our own Python instead:
```
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```
Refer to http://brew.sh/index.html

Install Python with the command:
```
brew install python
```

Install virtualenv:
```
pip install virtualenv
```

Then navigate inside the`dtk-tools` directory and create an IDM virtual environment:
```
virtualenv idm
```

Activate the virtual environment (you will have to do activate the virtual environment first before using dtk-tools):
```
source ./idm/bin/activate
```

Make sure you are in the virtual environment by checking if the prompt displays `(idm)` at the begining as shown:
```
(idm) my-computer:dtk-tools
```

Install pyCOMPS (wheel available [here](https://institutefordiseasemodeling.github.io/PythonDependencies/pyCOMPS-2.0.1-py2.py3-none-any.whl))
```
pip install pyCOMPS-2.0.1-py2.py3-none-any.whl
```

Navigate inside the `dtk-tools` folder and install dtk-tools:
```
python setup.py
```

Note: If you are encountering issues with TK on OSX (for example not being able to plot, or some matplotlib related issues), try:
```
brew install homebrew/dupes/tcl-tk
brew uninstall python
brew install python --with-brewed-tk
```

#### CentOS7 users
Please refer to [CentOS install instructions](http://institutefordiseasemodeling.github.io/dtk-tools/gettingstarted.html#id3) for more information.


#### Setup

To configure your user-specific paths and settings for local and HPC job submission, please create a `simtools.ini` file in
the same folder that contains your scripts or modify the master `simtools.ini` at `dtk-tools/simtools/simtools.ini`

Simulation job management is handled through the various `dtk` command-line options, e.g. `dtk run example_sweep` or `dtk analyze example_plots`.  For a full list of options, execute `dtk --help`.  Many example configurations for simulation sweeps and analysis processing may be found in the `examples` directory.
