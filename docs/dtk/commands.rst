===================
dtk commands
===================

Available commands
------------------
+------------------------+------------------------+
| :dtk-cmd:`analyze`     |  :dtk-cmd:`kill`       |
+------------------------+------------------------+
| :dtk-cmd:`resubmit`    |  :dtk-cmd:`run`        |
+------------------------+------------------------+
| :dtk-cmd:`status`      |                        |
+------------------------+------------------------+

``analyze``
-------------

.. dtk-cmd:: dtk analyze {none|id|name} <config_name.py>

Analyzes the *most recent* experiment matched by specified **id** or **name** (or just the most recent) with the python script passed.

.. dtk-cmd-option:: --comps, -c

Use COMPS asset service to read output files (default is direct file access).

.. dtk-cmd-option:: --force, -f

Force analyzer to run even if jobs are not all finished.

``kill``
-------------

.. dtk-cmd:: kill {none|id|name}

Kills all simulations in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

.. dtk-cmd-option:: --simIds, -s

Comma separated list of job IDs or process of simulations to kill in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

.. dtk-cmd-option:: --all, -a

Kills all simulations in all experiments matched by specified id or name (or just the most recent).


``resubmit``
-------------

.. dtk-cmd:: resubmit {none|id|name}

Resubmits all failed or canceled simulations in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

.. dtk-cmd-option:: --simIds, -s

Comma separated list of job IDs or process of simulations to resubmit in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

.. dtk-cmd-option:: --all, -a

Resubmit all failed or canceled simulations in selected experiments.

``run``
---------

.. dtk-cmd:: run {config_name}

Run the passed configuration python script for custom running of simulation. For example::

    dtk run example_sweep.py

.. dtk-cmd-option:: --hpc

Overrides where the simulation will be ran. Even if the python configuration passed defines the location ``LOCAL``, the simulations will be ran on HPC::

    dtk run example_simulation.py --hpc

.. dtk-cmd-option:: --priority

Overrides the :setting:`priority` setting of the :ref:`simtoolsini`.
Priority can take the following values:

    - ``Lowest``
    - ``BelowNormal``
    - ``Normal``
    - ``AboveNormal``
    - ``Highest``


For example, if we have a simulation supposed to run locally, we can force it to be HPC with lowest priority by using::

    dtk run example_local_simulation.py --hpc --priority Lowest

.. dtk-cmd-option:: --node_group <node_group>

Allows to overrides the :setting:`node_group` setting of the :ref:`simtoolsini`.


``status``
-----------

.. dtk-cmd:: status {none|id|name}

Returns the status of the *most recent* experiment matched by the specified **id** or **name**.


The ``experiment_id`` is displayed after issuing a ``dtk run`` command:

.. code-block:: doscon
    :linenos:
    :emphasize-lines: 8,12,13

    c:\dtk-tools\examples>dtk run example_sim.py

    Initializing LOCAL ExperimentManager from parsed setup
    Getting md5 for C:\Eradication\DtkTrunk\Eradication\x64\Release\Eradication.exe
    MD5 of Eradication.exe: a82da8d874e4fe6a5bd7acdf6cbe6911
    Copying Eradication.exe to C:\Eradication\bin...
    Copying complete.
    Creating exp_id = 2016_04_27_10_42_42_675000
    Saving meta-data for experiment:
    {
        "exe_name": "C:\\Eradication\\bin\\a82da8d874e4fe6a5bd7acdf6cbe6911\\Eradication.exe",
        "exp_id": "2016_04_27_10_42_42_675000",
        "exp_name": "ExampleSim",
        "location": "LOCAL",
        "sim_root": "C:\\Eradication\\simulations",
        "sim_type": "VECTOR_SIM",
        "sims": {
            "2016_04_27_10_42_42_688000": {
                "jobId": 12232
            }
        }
    }

In this example, the id is: ``2016_04_27_10_42_42_675000`` and we can poll the status of this experiment with::

    dtk status 2016_04_27_10_42_42_675000

In the same example, the name is: ``ExampleSim`` and can be polled with::

    dtk status ExampleSim

Which will return:

.. code-block:: doscon

    c:\dtk-tools\examples>dtk status 2016_04_27_10_42_42_675000
    Reloading ExperimentManager from: simulations\ExampleSim_2016_04_27_10_42_42_675000.json
    Job states:
    {
        "12232": "Success"
    }
    {'Success': 1}

Letting us know that the 1 simulation of our experiment completed successfully. You can learn more about the simulation states in the documentation related to the :ref:`experimentmanager`.


.. dtk-cmd-option:: --active, -a

Returns the status of all active experiments (mutually exclusive to any other parameters).

.. dtk-cmd-option:: --repeat, -r

Repeat status check until job is done processing. Without this option, the status command will only return the current state and return. With this option, the status of the experiment will be displayed at regular intervals until its completion.
For example:

.. code-block:: doscon

    c:\dtk-tools\examples>dtk status 2016_04_27_12_15_09_172000 --repeat
    Reloading ExperimentManager from: simulations\ExampleSim_2016_04_27_12_15_09_172000.json
    Job states:
    {
        "5900": "Running (40% complete)"
    }
    {'Running': 1}
    Job states:
    {
        "5900": "Running (81% complete)"
    }
    {'Running': 1}
    Job states:
    {
        "5900": "Running (97% complete)"
    }
    {'Running': 1}
    Job states:
    {
        "5900": "Finished"
    }
    {'Finished': 1}

