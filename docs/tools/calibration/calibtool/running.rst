Running CalibTool
-----------------

Run from the command line as follows::

    % python ./calibration_manager.py


The primary point of user manipulation is load_settings.py, which sets
up a dictionary including locations of local working directories, HPC
settings, local simulation settings, which sites to simulate, which
analyzers should be run for each site, any relative weights for each
site, iterative settings such as number of samples and max number of
iterations, and the file where the names and boundaries of sampled
parameters are listed.

Parameters to be sampled over should be specified as follows in json
format:

.. code-block:: python

    {
        'Parameter_Name_1' : {
            'max' : max_value,
        'min' : min_value,
        'type' : PARAM_TYPE
        },
        ...
    }

where ``PARAM_TYPE`` is a string specifying linear vs log sampling, and if
the parameter must be an integer. For example, a parameter to be
sampled over log space should have type 'log', a parameter sampled
over linear space but as an integer should have type 'linear_int',
etc.

load_settings.py also contains setup details for each
analyzer type. This includes the reporter from which data should be
gathered, relevant fields, and any other analyzer-specific settings
that will be needed for parsing and calculating likelihoods.

.. warning::
    Each calibration experiment MUST have a unique name.

When setting up a new calibration experiment, load_settings.py will
save settings and analyzers to json files.

To resume a partially-completed calibration, set ``settings['expname']``
in load_settings.py to the name of the calibration, then run
calibration_manager.py as normal. It is not necessary to cross-check
all remaining settings since load_settings.py will be loading the
settings.json and analyzers.json files from the appropriate experiment
directory.

