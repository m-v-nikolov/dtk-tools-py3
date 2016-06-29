.. _simtoolsoverlay:

===========================
INI File overlay mechanism
===========================

To illustrate how the overlay mechanism works, we will use the example of running a single simulation.

.. contents::
    :local:

Running with all defaults
-------------------------

The following folder structure is assumed::

    Example
    |_ example_sim.py

Also we assume that the ``example_sim.py`` file is simple and do not overrides anythong regarding to the ``SetupParser()`` like:

.. snippet:: python
    :filename: example_sim.py

    from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder

    cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')

    run_sim_args =  {'config_builder': cb,
                     'exp_name': 'ExampleSim'}

To run the simulation one would issue a ``dtk run example_sim.py``.

dtk-tools will then assumes we want to run a ``LOCAL`` simulation and look for the ``LOCAL`` block and configuration in the default ini file (``simtools/simtools.ini``).


Switching blocks in default ini file
-------------------------------------

Now lets consider the same file and directory structure as the previous example.
Because our default ini file has the ``LOCAL`` and ``HPC`` blocks present, one could issue the following commands::

    dtk run example_sim.py --HPC
    dtk run example_sim.py --LOCAL

The first command would go look for the parameters in the ``HPC`` block present in ``simtools/simtools.ini``).
Similarly, the second command would look for the parameters in the ``LOCAL`` block of the ``simtools.ini`` file
(which is the same as doing ``dtk run example_sim.py`` because ``--LOCAL`` is always assumed.

If the user would issue a ``dtk run example_sim.py --MYBLOCK`` the command would fail because ``simtools/simtools.cfg``
only includes ``HPC`` and ``LOCAL``.

.. note::
    The ``--CONFIG_NAME`` flag is not yet implemented and for now only allows ``--hpc`` to switch to HPC environment.
    See `GitHub issue <https://github.com/InstituteforDiseaseModeling/dtk-tools/issues/192>`_ for more information.


LOCAL Ini file without arguments
--------------------------------

Now if one wants to define custom blocks or overrides the current blocks, the tools will automatically look for
``simtools.ini`` file in the working directory.

Let's assume the following folder structure::

    Example
    |_ example_sim.py
    |_ simtools.ini

With simtools.ini looking like:

.. snippet:: ini
    :filename: simtools.ini

    [DEFAULT]
    max_threads = 10

    [LOCAL]
    max_local_sims = 5

    [MY_BLOCK]
    type=HPC
    use_comps_assets_svc = 1
    max_threads = 8


For simplicity, lets assume our global default looks like:

.. snippet:: ini
    :filename: simtools/simtools.ini

    [DEFAULT]
    dll_root = C:\dll
    max_threads = 3

    [LOCAL]
    type=LOCAL
    max_local_sims = 1
    sim_root = C:\Temp

    [HPC]
    type=HPC
    use_comps_assets_svc = 0
    max_threads = 3


If one would issue the following command:

.. code-block:: bat

    dtk run example_sim.py

1. No config block specified so ``LOCAL`` is assumed
2. Load the ``DEFAULT`` block from the global defaults(``simtools/simtools.ini``)
3. Load the ``LOCAL`` block from the global defaults
4. A ``simtools.ini`` file is present in the local directory
5. The local ini file has a ``DEFAULT`` block overlays its parameters
6. The local ini file has a ``LOCAL`` block, overlays it

Therefore the resulting set of parameters will look like:

.. code-block:: python
    :emphasize-lines: 2,3,9,10,11,15,26

    step-2 = {
        'dll_root':'C:\dll', # Coming from global(DEFAULT)
        'max_threads':3      # Coming from global(DEFAULT)
    }

    step-3 = {
        'dll_root':'C:\dll',
        'max_threads':3,
        'type':'LOCAL',      # Coming from global(LOCAL)
        'max_local_sims':1,  # Coming from global(LOCAL)
        'sim_root':'C:\Temp',# Coming from global(LOCAL)
    }

    step-5 = {
        'max_threads':10,    # Overridden by local(DEFAULT)
        'dll_root':'C:\dll',
        'type':'LOCAL',
        'max_local_sims':1,
        'sim_root':'C:\Temp',
    }

    final = {
        'max_threads':10,
        'dll_root':'C:\dll',
        'type':'LOCAL',
        'max_local_sims':5, # Overridden by local(LOCAL)
        'sim_root':'C:\Temp',
    }



LOCAL Ini file with block selection
-----------------------------------

Let's assume the same files structure/content as the previous example.

.. code-block:: bat

    dtk run example_sim.py --MY_BLOCK

1. MY_BLOCK is specified
2. A ``simtools.ini`` file is present in the local directory and has the ``MY_BLOCK`` definition
3. Look the ``MY_BLOCK.type`` (here ``HPC``)
4. Load the ``DEFAULT`` block from the global defaults(``simtools/simtools.ini``)
5. Load the ``HPC`` block from the global defaults
6. The local ini file has a ``DEFAULT`` block overlays its parameters
7. Overlays the ``MY_BLOCK`` parameters


.. code-block:: python
    :emphasize-lines: 2,7,8,15,16,22,31,32

    step-3 = {
        'type':'HPC'         # Coming from local(MY_BLOCK)
    }

    step-4 = {
        'type':'HPC',
        'dll_root':'C:\dll', # Coming from global(DEFAULT)
        'max_threads':3      # Coming from global(DEFAULT)
    }

    step-5 = {
        'type':'HPC',
        'dll_root':'C:\dll',
        'max_threads':3,
        'use_comps_assets_svc' = 0, # Coming from global(HPC)
        'max_threads' = 3           # Coming from global(HPC)
    }

    step-6 = {
        'type':'HPC',
        'dll_root':'C:\dll',
        'max_threads':10,          # Overridden by local(DEFAULT)
        'use_comps_assets_svc' = 0,
        'max_threads' = 3
    }

    final = {
        'type':'HPC',
        'dll_root':'C:\dll',
        'max_threads':10,
        'use_comps_assets_svc' = 1, # Overridden by local(MY_BLOCK)
        'max_threads' = 8           # Overridden by local(MY_BLOCK)
    }


Specified ini file
-------------------

If the user specifies a ini file with the following command::

    dtk run example_sim.py --ini my_custom_ini.ini

Then the local ini file will be ignored and only the specified custom ini file will be used for the overlay.
Because no block is specified, the command assumes the ``LOCAL`` block is used.

* If no ``LOCAL`` block is present in the custom ini file, the general default ``LOCAL`` block will be used.
* If a ``LOCAL`` block is present in the custom ini file, its parameters will be overlaid to the global ``LOCAL`` block.

Specified ini file and block
-----------------------------

If the user specified a ini file and a block name with the following command::

    dtk run example_sim.py --ini my_custom_ini.ini --MY_BLOCK

The ``MY_BLOCK`` block needs to be defined in the ``my_custom_ini.ini``. Its parameter will be overlayed to the parameters
coming from either the global ``LOCAL`` or the global ``HPC`` depending on the ``MY_BLOCK.type``.

File and block selection in the code
-------------------------------------

The ini file and block can be specified directly within the code when instantiating a ``SetupParser()``.
For example for the following calibration:

.. code-block:: python
    :emphasize-lines: 2

    calib_manager = CalibManager(name='ExampleCalibration',
                                 setup=SetupParser(selected_block='TEST_BLOCK',setup_file='custom_ini.ini'),
                                 config_builder=cb,
                                 sample_point_fn=sample_point_fn,
                                 sites=sites,
                                 next_point=IMIS(prior, **next_point_kwargs),
                                 sim_runs_per_param_set=2,
                                 max_iterations=2,
                                 num_to_plot=5,
                                 plotters=plotters)


The ``SetupParser`` constructor can take two parameters:

* `selected_block`: Name of the block we want to select
* `setup_file`: Path to the custom ini file

.. note::
    Note that the constructor can take either or both parameters.


For simulation where the ``SetupParser`` is not directly used like:

.. code-block:: python

    from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder

    cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')

    run_sim_args =  {'config_builder': cb,
                     'exp_name': 'ExampleSim'}

The ``SetupParser`` has the particularity to rely on its class variables ``selected_block`` and ``setup_file``. Once those are set
any subsequent instantiation of the object will use them.
So you can just change their values directly on the class at any point on the code before running:

.. code-block:: python
    :emphasize-lines: 2,4,5

    from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
    from simtools.SetupParser import SetupParser

    SetupParser.selected_block = 'TEST'
    SetupParser.setup_file = 'test.ini'

    cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
    configure_site(cb, 'Namawala')

    run_sim_args =  {'config_builder': cb,
                     'exp_name': 'ExampleSim'}


The previous calibration example can also be set the same way instead of using the constructor:

.. code-block:: python
    :emphasize-lines: 1,3,4,7

    from simtools.SetupParser import SetupParser

    SetupParser.selected_block = 'TEST_BLOCK'
    SetupParser.setup_file = 'custom_ini.ini'

    calib_manager = CalibManager(name='ExampleCalibration',
                                 setup=SetupParser(),
                                 config_builder=cb,
                                 sample_point_fn=sample_point_fn,
                                 sites=sites,
                                 next_point=IMIS(prior, **next_point_kwargs),
                                 sim_runs_per_param_set=2,
                                 max_iterations=2,
                                 num_to_plot=5,
                                 plotters=plotters)

As you notice even with an empty constructor, ``SetupParser`` will still use ``TEST_BLOCK`` and ``custom_ini.ini``.