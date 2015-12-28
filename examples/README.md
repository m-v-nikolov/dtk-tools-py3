The scripts in this directory are simple examples that show how to configure, run, and analyze the output of simulations.

### Commandline Basics

The single entry point into management of jobs is through the various `dtk` command-line options.

The usage is shown by the following `--help` flag:

```
dtk -h
```

The most flexible way of configuring jobs is by passing in a configuration function with custom instructions.

See the `example_sim.py` and `example_sweep.py` examples that can be run either locally

```
dtk run example_sim.py
```

or remotely by adding the `--hpc` flag to the command:

```
dtk run example_sweep.py --hpc
```

Other commands to manage query and manage already submitted jobs are `status`, `kill`, and `resubmit`.

Analogous to the flexible submission syntax, one can specify custom analysis instructions in a script, e.g. `example_plots.py`.

```
dtk analyze example_plots.py
```

### IPython Notebooks

Several end-to-end interactive tutorials based on IPython notebooks may be found in the `notebooks` subdirectory.

### More Examples

More advanced configuration examples, e.g. introducing custom sweeps and DLL-based reporting, may be found in the `features` subdirectory.
