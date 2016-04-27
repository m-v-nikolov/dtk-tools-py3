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

    python setup.py develop

Because a cross-platform solution for automatic installation of the numpy dependency is challenging, we have included the win_amd64 version 1.9.2+mkl of the numpy wheel locally. On other platforms, it is required to have installed that package first by issuing the following command from the ``install`` directory: ::

    pip install numpy-1.9.2+mkl-cp27-none-win_amd64.whl

Setup
----------
To configure your user-specific paths and settings for local and HPC job submission, edit the properties in ``dtk/dtk_setup.cfg``.
To learn more about the available options, please refer to :doc:`dtk/dtksetup`.

One can verify the proper system setup by navigating to the ``test`` directory and running the unit tests contained therein, e.g. by executing ``nosetests`` if one has the `nose <http://nose.readthedocs.org/en/latest/index.html>`_ package installed.
