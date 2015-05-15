The `dtk` package is intended to strengthen and simplify the interaction between researchers and the [DTK model](http://idmod.org/idmdoc/).

Modules contained in this package are intended to:
- Empower the user to configure diverse simulations and arbitrarily complex campaigns built up from a standardized library of configuration fragments and utility functions; 
- Facilitate transparent switching between local and remote HPC commissioning, job-status queries, and output analysis;
- Enable the configuration of arbitrary collections of simulations (e.g. parameteric sweeps) through an extensible library of builder classes; 
- Collect a library of post-processing analysis functionality, e.g. filtering, mapping, averaging, plotting.

#### Installation

With administrator privileges, run the following from the current directory:

`python setup.py install`

Or to do active development on the package:

`python setup.py develop`

On Windows, one may need to add the `Scripts` subdirectory of your local Python installation to the `%PATH%` [environment variable](https://www.java.com/en/download/help/path.xml) to have access to the `dtk` commandline utility.

#### Setup

To configure your user-specific paths and settings for local and HPC job submission, edit the properties in `dtk_setup.cfg`.

#### Dependencies

The `dtk status` command imports the [`psutil`](https://pypi.python.org/pypi/psutil) package for process ID lookup of local simulations. HPC simulations will be able to retrieve status without this package.

Statistical analysis and plotting of output depend on [`numpy`](https://pypi.python.org/pypi/numpy), [`matplotlib`](https://pypi.python.org/pypi/matplotlib), and [`pandas`](https://pypi.python.org/pypi/pandas).

32- and 64-bit Windows binaries may be downloaded [here](http://www.lfd.uci.edu/~gohlke/pythonlibs).

Interoperability with the JAVA layer of COMPS requires installation of the Java Runtime Environment and setup of the `COMPS` package, which in turn has dependencies on `cython` and `pyjnius`.  Those instructions are currently outside the scope of the installation instructions for this package.

#### Test

There are a number of unit tests in the `test` directory.  If one has installed the [`nose`](http://nose.readthedocs.org/en/latest/index.html) package, one can navigate to the `test` directory and call `nosetests` to run all tests.

#### Examples

There are a number of example simulation sweep and analysis processing configurations in the `examples` directory.

