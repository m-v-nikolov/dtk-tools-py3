.. _simtoolsini:

===================
simtools.ini file
===================

The ``simtools.ini`` file allows you to specify the default configuration options.

.. seealso::
    To know more on the overlay mechanism, consult the :doc:`overlay`.


.. contents::
    :local:

DEFAULT section
===============

Anything in this section will apply to all the subsequent blocks if they do not override the value.
For example, let's assume the following file:

.. snippet:: cfg
    :filename: simtools/simtools.ini

    [DEFAULT]
    max_threads = 16

    [HPC]
    other_param = 2

    [LOCAL]
    max_threads = 8


if the ``HPC`` block is used for a simulation, the ``max_threads`` value will be coming from the ``[DEFAULT]`` block.
However, if the ``LOCAL`` block is used, the ``max_threads`` will be coming from the ``[LOCAL]`` block.

Usually this section contains the following parameters: :setting:`exe_path`, :setting:`dll_path` and :setting:`max_threads`.

Common parameters
==================

Those parameters apply to both HPC and LOCAL configurations.

.. setting:: type

``type``
--------------------------

Default: LOCAL

Every blocks defined in ini files need to have a type. The type can be either ``HPC`` or ``LOCAL`` and defines which set of defaults will be used
and which parameters are expected.

.. setting:: python_path

``python_path``
--------------------------

Default: Empty

Specify the path for the python scripts. This will correspond to the ``--python-script-path`` flag of ``Eradication.exe`` and can be left blank.

.. warning::
    If the path does not contain Python script, it can prevent the model to run and should be left blank.


.. setting:: exe_path

``exe_path``
--------------------------

Default: ``C:\Eradication\DtkTrunk\Eradication\x64\Release\Eradication.exe``

Path of the current executable you wish to use for your simulations. This executable will be staged in the :setting:`bin_staging_root`.

.. warning::
    If the :setting:`use_comps_asset_svc` is used, this path will be ignored as the executable will not be staged.

.. setting:: dll_path

``dll_path``
--------------------------

Default: ``C:\Eradication\DtkTrunk\x64\Release``

Path where the DLL used for the simulations are stored. The required DLLs will be copied from this directory and staged in the :setting:`lib_staging_root`.

.. note::
    This folder should not contained directly the dll as simtools will add ``reporter_plugins``, ``interventions`` or ``disease_plugins`` to this path depending on the type of DLLs it looks for.

.. warning::
    If the :setting:`use_comps_asset_svc` is used, this path will be ignored as the dll will not be staged.

.. setting:: max_threads

``max_threads``
--------------------------

Default: ``6``

Defines how many threads can be fired off when analyzing an experiment.

.. setting:: sim_root

``sim_root``
--------------------------

| HPC Default:  ``\\idmppfil01\IDM\home\%(user)s\output\simulations\``
| LOCAL Default:  ``C:\Eradication\simulations``

Folder where all the simulations inputs/outputs will be stored.

.. warning::

    The provided path needs to be accessible by your endpoint in the case of HPC simulation.



.. setting:: input_root

``input_root``
--------------------------

| HPC Default: ``\\idmppfil01\IDM\home\%(user)s\input\``
| LOCAL Default: ``C:\Eradication\EMOD-InputData``

Folder where all the input files (climate and demographics) are stored.

.. warning::

    The provided path needs to be accessible by your endpoint in the case of HPC simulation.



.. setting:: bin_staging_root

``bin_staging_root``
--------------------------

| HPC Default: ``\\idmppfil01\IDM\home\%(user)s\bin\``
| LOCAL Default: ``C:\Eradication\bin``

Folder where the executable will be cached.

.. warning::

    The provided path needs to be accessible by your endpoint in the case of an HPC simulation.
    Also if the :setting:`use_comps_asset_svc` is on, this path needs to be the full path to an accessible exe.


.. setting:: lib_staging_root

``lib_staging_root``
--------------------------

| HPC Default: ``\\idmppfil01\IDM\home\%(user)s\emodules\``
| LOCAL Default: ``C:\Eradication\bin``

Folder where the custom reporters and other dlls will be cached.

.. warning::

    The provided path needs to be accessible by your endpoint in the case of an HPC simulation.
    Also if the :setting:`use_comps_asset_svc` is on, this path needs to hold the path where the DLL are stored.




LOCAL defaults
===============
This section defines parameters related to running the simulations in a LOCAL environment.
Those defaults will apply to every blocks with the ``type=LOCAL``.

.. setting:: max_local_sims

``max_local_sims``
--------------------------

Default: 8

Number of simulations ran in parallel.



HPC defaults
=============

This section defines parameters related to running the simulations in an HPC environment.
Those defaults will apply to every blocks with the ``type=HPC``.

.. setting:: server_endpoint

``server_endpoint``
--------------------------

Default: ``https://comps.idmod.org``

URL of the endpoint. Note that you will need a valid login/password on this endpoint.


.. setting:: node_group

``node_group``
--------------------------

Default: ``emod_abcd``

Defines the node group that will be used for the simulation.


.. setting:: priority

``priority``
--------------------------

Default: ``Lowest``

Priority of the simulation can be:

    - ``Lowest``
    - ``BelowNormal``
    - ``Normal``
    - ``AboveNormal``
    - ``Highest``


.. setting:: num_retries

``num_retries``
--------------------------

Default: 0

How many times a failed simulation needs to be retried.


.. setting:: sims_per_thread

``sims_per_thread``
--------------------------

Default: 20

Number of simulations per analysis threads.


.. setting:: use_comps_asset_svc

``use_comps_asset_svc``
--------------------------

Default: 0

If set to ``1``, uses the COMPS assets service.

.. warning::
    When setting this to ``1``, don't forget to set:

    * :setting:`lib_staging_root` with the folder containing already staged DLLs.
    * :setting:`bin_staging_root` with the full path to the exe used for the simulations.


.. setting:: compress_assets

``compress_assets``
--------------------------

Default: 0

If the COMPS assets service is used, choose to compress the assets or not.


.. setting:: environment

``environment``
--------------------------

Default: Bayesian

Specify which environment to run on.


Complete example
==================

.. snippet:: cfg
    :filename: simtools/simtools.ini

    [DEFAULT]
    max_threads = 16
    exe_path = C:\Eradication\DtkTrunk\Eradication\x64\Release\Eradication.exe
    dll_path = C:\Eradication\DtkTrunk\x64\Release


    [HPC]
    type = HPC
    server_endpoint = https://comps.idmod.org
    environment = Bayesian
    node_group = emod_abcd
    priority = Normal

    sim_root = \\idmppfil01\IDM\home\%(user)s\output\simulations\
    input_root = \\idmppfil01\IDM\home\%(user)s\input\
    bin_staging_root = \\idmppfil01\IDM\home\%(user)s\bin\
    lib_staging_root = \\idmppfil01\IDM\home\%(user)s\emodules\

    num_retries = 0
    sims_per_thread = 20
    use_comps_asset_svc = 0
    compress_assets = 0

    [LOCAL]
    type = LOCAL
    max_local_sims = 3
    sim_root = C:\Eradication\simulations
    input_root = C:\Eradication\EMOD-InputData
    bin_staging_root = C:\Eradication\bin
    lib_staging_root = C:\Eradication\bin
    python_path=C:\Eradication\python
