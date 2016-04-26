===================
dtk_setup.cfg file
===================

The ``dtk_setup.cfg`` file allows you to overrides the default configuration options available.

GLOBAL section
===============

.. setting:: max_threads

``max_trheads``
--------------------------

Default: ``6``

Defines how many threads can be fired off when analyzing an experiment.




HPC section
=============

This section defines parameters related to running the simulations in an HPC environment.

    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | Parameter              | Description                                                                                              | Default                                                 |
    +========================+==========================================================================================================+=========================================================+
    | server_endpoint        | URL of the endpoint.                                                                                     | ``https://comps.idmod.org``                             |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | node_group             | Defines the node group that will be used for the simulations.                                            | ``emod_abcd``                                           |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | priority               |     Priority of the simulation can be:                                                                   |  ``Lowest``                                             |
    |                        |                                                                                                          |                                                         |
    |                        |      * ``Lowest``                                                                                        |                                                         |
    |                        |      * ``BelowNormal``                                                                                   |                                                         |
    |                        |      * ``Normal``                                                                                        |                                                         |
    |                        |      * ``AboveNormal``                                                                                   |                                                         |
    |                        |      * ``Highest``                                                                                       |                                                         |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | sim_root               | Folder where all the simulations inputs/outputs will be stored. Needs to be accessible by COMPS.         |  ``\\idmppfil01\IDM\home\%(user)s\output\simulations\`` |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | input_root             | Folder where all the input files (climate and demographics) are stored. Needs to be accessible by COMPS. |  ``\\idmppfil01\IDM\home\%(user)s\input\``              |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | bin_root               | Folder where the executable will be cached. Needs to be accessible by COMPS.                             | ``\\idmppfil01\IDM\home\%(user)s\bin\``                 |
    |                        | Test                                                                                                     |                                                         |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | dll_root               | Folder where the custom reporters and other dlls will be cached. Needs to be accessible by COMPS.        |  ``\\idmppfil01\IDM\home\%(user)s\emodules\``           |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | num_retries            | How many times a failed simulation needs to be retried.                                                  |  ``Lowest``                                             |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | sims_per_thread        | Number of simulations per analysis threads.                                                              |  ``Lowest``                                             |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | use_comps_asset_svc    | If set to ``1``, uses the COMPS assets service.                                                          |  ``Lowest``                                             |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
    | compress_assets        | If the COMPS assets service is used, choose to compress the assets or not.                               |  ``Lowest``                                             |
    +------------------------+----------------------------------------------------------------------------------------------------------+---------------------------------------------------------+


Complete example
-----------------

.. code-block:: cfg

    [GLOBAL]
    max_threads    = 16

    [HPC]
    server_endpoint = https://comps.idmod.org
    node_group      = emod_abcd
    priority = Lowest

    sim_root            = \\idmppfil01\IDM\home\%(user)s\output\simulations\
    input_root          = \\idmppfil01\IDM\home\%(user)s\input\
    bin_root            = \\idmppfil01\IDM\home\%(user)s\bin\
    dll_root            = \\idmppfil01\IDM\home\%(user)s\emodules\

    num_retries         = 0
    sims_per_thread     = 20
    use_comps_asset_svc = 0
    compress_assets     = 0

    [LOCAL]
    max_local_sims = 1
    sim_root       = C:\Eradication\simulations
    input_root     = C:\Eradication\EMOD-InputData
    bin_root       = C:\Eradication\DTK_Trunk\x64\Release
    dll_root       = C:\Eradication\DTK_Trunk\x64\Release

    [POSIX]
    sim_root       = /Users/%(user)s/simtools/simulations
    input_root     = /Users/%(user)s/simtools/input
    bin_root       = /Users/%(user)s/simtools/bin
    dll_root       = /Users/%(user)s/simtools/emodules

    [BINARIES]
    exe_path   = C:\Eradication\DtkTrunk\Eradication\x64\Release\Eradication.exe
    dll_path   = C:\Eradication\DtkTrunk\x64\Release
