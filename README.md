#### Installation

In order to set up the python scripts in these directories, 
the following environmental variables should be set:

  PATH: append current directory to have dtk.py execute without specifying full path
  PYTHONPATH: append current directory to allow import of 'dtk' python package contents in scripts outside of this directory
  PATHEXT: append '.PY' to allow dtk.py to be run with a command like 'dtk status'

In the absence of administrator priviliges to set up the above paths,
one can still type the full commands, e.g. 'python ../python/dtk.py status'

#### Setup

To configure your user-specific paths and settings for local and HPC job submission, copy the template from:
  dtk/utils/dtk_setup.example.cfg
to a file called:
  dtk_setup.cfg
and edit its content accordingly:

#### Dependencies

The 'dtk status' command has the following external dependency
for process ID lookup of local simulations (https://code.google.com/p/psutil/).
HPC simulations will be able to retrieve status without this package.
(At time of writing, the binary installer executable is available on the left 
and is easier than installing from the link to the source code at the top)

Statistical analysis and plotting of output has external dependencies (numpy, matplotlib, pandas)
32- and 64-bit Windows binaries may be downloaded from: http://www.lfd.uci.edu/~gohlke/pythonlibs/
