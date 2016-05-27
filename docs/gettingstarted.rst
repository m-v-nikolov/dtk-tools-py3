Getting started
=====================

The dtk package is intended to strengthen and simplify the interaction between researchers and the DTK model.

Modules contained in this package are intended to:

    * Empower the user to configure diverse simulations and arbitrarily complex campaigns built up from a standardized library of configuration fragments and utility functions;
    * Facilitate transparent switching between local and remote HPC commissioning, job-status queries, and output analysis;
    * Enable the configuration of arbitrary collections of simulations (e.g. parameteric sweeps) through an extensible library of builder classes;
    * Collect a library of post-processing analysis functionality, e.g. filtering, mapping, averaging, plotting.

Installation
-------------

The package being in development, run the following command from the dtk-tools root: ::

    pip install -e .

Setup
----------
To configure your user-specific paths and settings for local and HPC job submission, edit the properties in ``simtools/simtools.ini``.
To learn more about the available options, please refer to :doc:`simtools/simtoolsini`.

One can verify the proper system setup by navigating to the ``test`` directory and running the unit tests contained therein, e.g. by executing ``nosetests`` if one has the `nose <http://nose.readthedocs.org/en/latest/index.html>`_ package installed.
