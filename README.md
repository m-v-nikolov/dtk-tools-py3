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

From a command-prompt (as admin), run the following from the **dtk-tools** directory:
```
python -m pip install --upgrade pip
pip install -e . 
```

To test if dtk-tools is correctly installed on your machine issue a:
```
dtk -h
```
If the command succeed and present you with the details of the dtk command you are all set!

**Note:** If you run into issues updating numpy on Windows, under the dtk-tools\install folder try:

```
pip install numpy-1.11.0+mkl-cp27-cp27m-win_amd64.whl
```

**Note:** EMOD DTK is required to work with dtk-tools. You can download the quick start at: https://github.com/InstituteforDiseaseModeling/EMOD-QuickStart

If you plan to run simulations on COMPS, you will also need the pyCOMPS package. Available [here](https://github.com/InstituteforDiseaseModeling/pyCOMPS).

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
