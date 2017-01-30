Documentation available: http://institutefordiseasemodeling.github.io/dtk-tools

The `dtk` package is intended to strengthen and simplify the interaction between researchers and the [DTK model](http://idmod.org/idmdoc/).

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

Make sure you have Python 2.7 installed (available [here](https://www.python.org/downloads/)).

From a command-prompt, run the following from the **dtk-tools** directory:
```
python setup.py 
```

Add the path to `dtk_tools` to your `PYTHONPATH` environment variable.

**Note:** If `pip` command is not found on your system, make sure to add the Python scripts directory (by default in Windows: `C:\Python27\Scripts`)
to your `PATH` environment variable.

To test if dtk-tools is correctly installed on your machine issue a:
```
dtk -h
```
If the command succeed and present you with the details of the dtk command you are all set!


#### MAC users ####
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

Install pyCOMPS (wheel available [here](https://github.com/InstituteforDiseaseModeling/PythonDependencies/raw/master/pyCOMPS-1.0-py2.py3-none-any.whl])
```
pip install pyCOMPS-1.0-py2.py3-none-any.whl
```

Navigate inside the `dtk-tools` folder and install dtk-tools:
```
python setup.py
```

#### Linux users
Linux users, you need to install:
- python-snappy
- snappy-dev
- LAPACK
In order for the tools to work.

Remark: the command ```python setup.py``` from previous step will do these installation for you!

#### Setup

To configure your user-specific paths and settings for local and HPC job submission, run the `dtk setup` command.
The command will display an interface allowing you to:

* Change the default `LOCAL` configuration (Configuration used by default for all simulations and running on your local computer)
* Change the default `HPC` configuration (Configuration used if you append a `--HPC` to a command and that will run on HPC environment)
* Add a new configuration block (If you wish to create a configuration block that you can later reference by `--BLOCK_NAME`)
* Edit the configuration blocks

In this interface, the **default configurations** refers to the configuration blocks accessible everywhere in your environment (by default `LOCAL` and `HPC`).
The **local configurations** refers to the configurations stored in the `simtools.ini` file in your current working directory (the directory from where you call the `dtk setup` command) and are
accessible only to commands ran there. 

Note that it is possible to have a local configuration called `LOCAL` or `HPC` which will overrides the global defaults. 

One can verify the proper system setup by navigating to the `test` directory and running the unit tests contained therein, e.g. by executing `nosetests` if one has the [`nose`](http://nose.readthedocs.org/en/latest/index.html) package installed.

Simulation job management is handled through the various `dtk` command-line options, e.g. `dtk run example_sweep` or `dtk analyze example_plots`.  For a full list of options, execute `dtk --help`.  Many example configurations for simulation sweeps and analysis processing may be found in the `examples` directory.

#### Dependencies

All dependencies are automatically installed by the `pip install -e .` command but you 64-bit Windows binaries may be downloaded [here](http://www.lfd.uci.edu/~gohlke/pythonlibs).

Interoperability with the Java layer of COMPS requires installation of the pyCOMPS package.  [More detailed instructions](https://github.com/InstituteforDiseaseModeling/pyCOMPS/blob/master/README.md) can be found within the [`pyCOMPS`](https://github.com/InstituteforDiseaseModeling/pyCOMPS) repository.

<a href="https://zenhub.com"><img src="https://raw.githubusercontent.com/ZenHubIO/support/master/zenhub-badge.png"></a>
