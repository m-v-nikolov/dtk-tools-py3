dtk commands
============

.. contents:: Available commands
    :local:

``analyze``
------------

.. dtk-cmd:: analyze -id {exp_id|suite_id|name},... -a {config_name.py|built-in}

Analyzes the *most recent* experiment matched by specified **id** or **name** (or just the most recent) with the python script passed or the built-in analyzer.
Refer to the :dtk-cmd:`analyze-list` to see all available built-in analyzers.


.. dtk-cmd-option:: -bn, --batchName

When the analyze command is called on more than one experiment, a batch is automatically created. By default it will be called
`batch_id` with `id` being an automatically generated identification. This option allows to specify a batch name.
If the chosen batch already exists, the command will ask if you want to merge, override or cancel.


.. dtk-cmd-option:: -id

IDs of the items to analyze (can be suites, batches, experiments). This option supports a list of IDs separated by commas and the IDs can be:

* Experiment id
* Simulation id
* Experiment name
* Batch id
* Batch name
* Suite id

.. dtk-cmd-option:: -a, --config_name

Python script or builtin analyzer name for custom analysis of simulations (see :dtk-cmd:`analyze-list`).

.. dtk-cmd-option:: --force, -f

Force analyzer to run even if jobs are not all finished.

``analyze-list``
----------------

.. dtk-cmd:: analyze-list

List the available builtin analyzers.

``clean``
---------

.. dtk-cmd:: clean {none|id|name}

Deletes **ALL** experiments matched by the id or name (or literally all experiments if nothing is passed).
**Use with caution**.

``clean-batch``
---------------

.. dtk-cmd:: clean_batch

Deletes all empty batches.

``clear_batch``
---------------

.. dtk-cmd:: clear_batch -id <batch_id>

Clear the provided batch of all experiments or remove empty batches if no id provided.

.. dtk-cmd-option:: -id

ID of the batch to clear.


``create_batch``
----------------

.. dtk-cmd:: create_batch -id <item_id,...> -bn <name>

Create a batch of experiments given the IDs of the items passed with the given name (or automatically generate a name if None is passed). The IDs supported are:

* Experiment id
* Experiment name
* Simulation id
* Batch id
* Batch name
* Suite id

.. note::

    The batch creation will merge any overlapping items and ensure there will be no duplicates in the final batch.

.. dtk-cmd-option:: -id

IDs of the items to group in the batch.

.. dtk-cmd-option:: --batchName, -bn

Name of the batch.


``delete``
----------

.. dtk-cmd:: delete {none|id|name}

Deletes the selected experiment (or most recent). This command will delete the experiment files (inputs and outputs) from COMPS or the local directory.

``delete_batch``
----------------

.. dtk-cmd:: delete_batch -id {none|id|name}

Delete all Batches or the Batch identified by given Batch ID/name.


``exterminate``
---------------

.. dtk-cmd:: exterminate {none|id|name}

Kills ALL experiments matched by the id or name (or literally all experiments if nothing is passed).

``get_package``
---------------

.. dtk-cmd:: get_package <package_name> -v <version>

Allows to download and install a disease package. Optionally a version can be specified. if not the last released version will be chosen.
The list of available packages can be displayed with the :dtk-cmd:`list_packages` command

.. dtk-cmd-option:: -v <version>

Specify a version to choose for the given package. A special version named ``HEAD`` allows to download the latest git commit for the disease repository.

.. note::
    ``-v HEAD`` is different than not giving a version number because without version specified, the latest git release is chosen and with ``-v HEAD`` the most recent commit is chosen.


``kill``
--------

.. dtk-cmd:: kill {none|id|name}

Kills all simulations in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

.. dtk-cmd-option:: -id

Comma separated list of simulation IDs to kill in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

``link``
--------
.. dtk-cmd:: link {none|id|name}

Opens the default browser with the COMPS page corresponding to the most recent experiment or the experiment matched by name or ID.

``list``
--------
.. dtk-cmd:: list {none|name}

list 20 *most recent* experiment containing specified **name** in the experiment name (or just the 20 most recent). For example::

    dtk list TestExperiment

.. dtk-cmd-option:: --<location>

list 20 *most recent* experiment by matched specified **location** in the experiment location. For example, to list experiments with HPC as a location::

    dtk list --HPC

.. dtk-cmd-option:: --number, -n

Use any number following by the command option to **limit** the number of *most recent* experiments to display. For example::

    dtk list -n 100

Use * to retrieve all experiments from local database. For example::

    dtk list -n *

``dtk list`` will only list experiments based on local database data that may not reflect the current status of the running experiments.

``list_batch``
--------------

.. dtk-cmd:: list_batch -id <batch_id> -n <limit>

List the 20 (or ``limit``) most recently created batches in the DB or the batch identified by ``batch_id``.


.. dtk-cmd-option:: -id

ID of the batch to list. If not provided, the command will list the ``limit`` batches present in the system.

.. dtk-cmd-option:: -n

Limit the number of batches to list.

``list_packages``
-----------------

.. dtk-cmd:: list_packages

List the packages available to the :dtk-cmd:`get_package` command.

``list_package_versions``
-------------------------

.. dtk-cmd:: list_package_versions <package_name>

List the versions available for the given package.


.. dtk-cmd-option:: -id

ID of the batch to list. If not provided, the command will list the ``limit`` batches present in the system.

.. dtk-cmd-option:: -n

Limit the number of batches to list.

``log``
-------

.. dtk-cmd:: log -l <level> -m <module> -n <number> -e <filename> -c

The log command allows to query and display the content of the logging database.
By default, ``dtk log`` will show all levels for all modules and limit to 100 rows.

.. dtk-cmd-option:: -l

Allows you to filter by level. All log entries for the given level and above will be displayed.
The levels are (from less important to more important):

- DEBUG
- INFO
- WARNING
- ERROR

.. dtk-cmd-option:: -m

Allows you to specify a particular module to filter by. For example, to see only ``Overseer`` debug, one can issue::

    dtk log -m Overseer

All the available modules are displayed at the begining of the log command output:

.. code-block:: console

    c:\MyWork\examples>dtk log -n 10
    Presenting the last 10 entries for the modules ['Overseer', 'SimConfigBuilder', 'ExperimentManagerFactory', 'General', 'ExperimentDataStore', 'BaseExperimentManager', 'AssetCollection', 'SimulationAssets', 'Simulation', 'Monitor', 'Comp
    sExperimentManager', 'COMPSRunner', 'Experiments', 'AuthManager', 'COMPSUtilities', 'LocalExperimentManager', 'LocalRunner', 'Helpers', 'IncidenceCalibSite', 'CalibSite', 'IterationState', 'CalibManager', 'SetupParser', 'commands', 'Out
    putParser', 'malaria_summary', 'BaseCalibrationAnalyzer', 'OptimTool', 'ChannelByAgeCohortAnalyzer', 'logging', 'AnalyzeHelper'] and level DEBUG
    ...


.. dtk-cmd-option:: -n

Allows to limit to only the n most recent entries (100 by default)

.. dtk-cmd-option:: -e <filename>

If specified, will export the results to a CSV file specified with this flag. For example ::

    dtk log -n 1000 -e log.csv

.. dtk-cmd-option:: -c

If this flag is present, exports the totality of the log DB to a CSV file.


``run``
-------

.. dtk-cmd:: run {config_name}

Run the passed configuration python script for custom running of simulation. For example::

    dtk run example_sweep.py

.. dtk-cmd-option:: --<block_name>

Overrides which configuration block the simulation will be ran. Even if the python configuration passed defines the location ``LOCAL``, the simulations will be ran on the selected block::

    dtk run example_simulation.py --MY_CONFIG_BLOCK

See :ref:`simtoolsoverlay` for more information.

.. dtk-cmd-option:: --priority

Overrides the :setting:`priority` setting of the :ref:`simtoolsini`.
Priority can take the following values:

    - ``Lowest``
    - ``BelowNormal``
    - ``Normal``
    - ``AboveNormal``
    - ``Highest``


For example, if we have a simulation supposed to run locally, we can force it to be HPC with lowest priority by using::

    dtk run example_local_simulation.py --HPC --priority Lowest

.. dtk-cmd-option:: --node_group <node_group>

Allows to overrides the :setting:`node_group` setting of the :ref:`simtoolsini`.

.. dtk-cmd-option:: --blocking, -b

If this flag is present, the tools will run the experiment and automatically display the status until done.

.. dtk-cmd-option:: --quiet, -q

If this flag is used, the tools will not generate console outputs while running.


``status``
----------

.. dtk-cmd:: status {none|id|name}

Returns the status of the *most recent* experiment matched by the specified **id** or **name**.


The ``experiment_id`` is displayed after issuing a ``dtk run`` command:

.. code-block:: doscon
    :linenos:
    :emphasize-lines: 9,10

    c:\MyWork\examples>dtk run example_sim.py

    Saving meta-data for experiment:
    {
       "command_line": "Assets\\Eradication.exe --config config.json --input-path ./Assets",
       "date_created": "2017-11-09 13:35:02.198259",
       "dtk_tools_revision": "1.0b3",
       "endpoint": "https://comps2.idmod.org",
       "exp_id": "d03141d7-95c5-e711-80c6-f0921c167864",
       "exp_name": "ExampleSim",
       "id": "ExampleSim_d03141d7-95c5-e711-80c6-f0921c167864",
       "location": "HPC",
       "selected_block": "HPC",
       "setup_overlay_file": "c:\\Eradication\\examples\\simtools.ini",
       "sim_root": "$COMPS_PATH(USER)\\output",
       "sim_type": "VECTOR_SIM",
       "working_directory": "c:\\Eradication\\examples"
    }


In this example, the id is: ``d03141d7-95c5-e711-80c6-f0921c167864`` and we can poll the status of this experiment with::

    dtk status d03141d7-95c5-e711-80c6-f0921c167864

In the same example, the name is: ``ExampleSim`` and can be polled with::

    dtk status ExampleSim

Which will return:

.. code-block:: doscon

    c:\MyWork\examples>dtk status ExampleSim
    ExampleSim ('d03141d7-95c5-e711-80c6-f0921c167864') states:
    {
        "d13141d7-95c5-e711-80c6-f0921c167864": "Succeeded"
    }
    {'Succeeded': 1}


Letting us know that the 1 simulation of our experiment completed successfully. You can learn more about the simulation states in the documentation related to the :ref:`experimentmanager`.


.. dtk-cmd-option:: --active, -a

Returns the status of all active experiments (mutually exclusive to any other parameters).

.. dtk-cmd-option:: --repeat, -r

Repeat status check until job is done processing. Without this option, the status command will only return the current state and return. With this option, the status of the experiment will be displayed at regular intervals until its completion.
For example:

.. code-block:: doscon

    c:\MyWork\examples>dtk status -r
    ExampleSim ('d03141d7-95c5-e711-80c6-f0921c167864') states:
    {
        "d13141d7-95c5-e711-80c6-f0921c167864": "CommissionRequested"
    }
    {'CommissionRequested': 1}

    ExampleSim ('d03141d7-95c5-e711-80c6-f0921c167864') states:
    {
        "d13141d7-95c5-e711-80c6-f0921c167864": "Running"
    }
    {'Running': 1}

    ExampleSim ('d03141d7-95c5-e711-80c6-f0921c167864') states:
    {
        "d13141d7-95c5-e711-80c6-f0921c167864": "Succeeded"
    }
    {'Succeeded': 1}



``stdout``
----------

.. dtk-cmd:: stdout {none|id|name}

Prints ``StdOut.txt`` for the *first* simulation in the *most recent* experiment matched by specified id or name (or just the most recent).

.. dtk-cmd-option:: -e

Prints ``StdErr.txt`` for the *first* simulation in the *most recent* experiment matched by specified id or name (or just the most recent).

.. dtk-cmd-option:: --failed, --succeeded

Prints ``StdOut.txt`` for the *first* failed or succeeded (depending on flag) simulation in the *most recent* experiment matched by specified id or name (or just the most recent).


``sync``
----------

.. dtk-cmd:: sync -d <days> -id <id> -n <name> -u <user>

The sync command allows you to synchronize the local DB with the COMPS DB.
issuing a simple ``dtk sync`` will sync the last 30 days of experiments for your current user.

.. dtk-cmd-option:: -d <days>

Synchronize ``days`` back from today (for the current user or the user specified with ``-u``).

.. dtk-cmd-option:: -id <exp_id>

Synchronize a specific experiment identified by its id (for the current user or the user specified with ``-u``).

.. dtk-cmd-option:: -n <experiment_name>

Synchronize all experiments matched by ``experiment_name`` (for the current user or the user specified with ``-u``).

.. dtk-cmd-option:: -u <COMPS_user>

Allows to synchronize experiments from a different user.

``test``
-----------

.. dtk-cmd:: test

Run all the unit tests included in the ``test`` folder. This requires ``nosetests`` to work.


``version``
-----------

.. dtk-cmd:: version

Displays the current dtk=tools version
