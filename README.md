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

From a command-prompt, run the following from the current directory:
```
python -m pip install --upgrade pip
pip install -e . --find-links=./install
```

Also on Windows, please add the path to the `dtk` folder to your `PYTHONPATH` System environment variable. For example: `C:\github\dtk-tools\dtk`.

If you plan to run simulations on COMPS, you will also need the pyCOMPS package. Available [here](https://github.com/InstituteforDiseaseModeling/pyCOMPS).

#### Setup

To configure your user-specific paths and settings for local and HPC job submission, edit the properties in `dtk_setup.cfg`.

One can verify the proper system setup by navigating to the `test` directory and running the unit tests contained therein, e.g. by executing `nosetests` if one has the [`nose`](http://nose.readthedocs.org/en/latest/index.html) package installed.

Simulation job management is handled through the various `dtk` command-line options, e.g. `dtk run example_sweep` or `dtk analyze example_plots`.  For a full list of options, execute `dtk --help`.  Many example configurations for simulation sweeps and analysis processing may be found in the `examples` directory.

#### Dependencies

* [`numpy`](https://pypi.python.org/pypi/numpy) (Windows compilation issues discussed in Installation section above)
* [`psutil`](https://pypi.python.org/pypi/psutil) for process ID lookup of local simulations with the `dtk status` command
* statistical analysis with [`pandas`](https://pypi.python.org/pypi/pandas)
* plotting of output with [`matplotlib`](https://pypi.python.org/pypi/matplotlib).

Recommended optional dependencies: 
* [`seaborn`](http://stanford.edu/~mwaskom/software/seaborn/) for statistical data visualization (requires scipy)
* [`statsmodels`](https://pypi.python.org/pypi/statsmodels) for statistical estimation and inference (requires scipy)
* `scipy` (e.g. from [scipy-0.15.1-cp27-none-win_amd64.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs))
* `nose` for running test suite

32- and 64-bit Windows binaries may be downloaded [here](http://www.lfd.uci.edu/~gohlke/pythonlibs).

Interoperability with the Java layer of COMPS requires installation of the COMPSJavaInterop package.  [More detailed instructions](https://github.com/InstituteforDiseaseModeling/pyCOMPS/blob/master/README.md) can be found within the [`pyCOMPS`](https://github.com/InstituteforDiseaseModeling/pyCOMPS) repository.
