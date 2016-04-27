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

.. dtk-cmd:: analyze <config_name>


``kill``
-------------

.. dtk-cmd:: kill <jobs_ids>


``resubmit``
-------------

.. dtk-cmd:: resubmit <jobs_ids>



``run``
---------

.. dtk-cmd:: run <config_name>

Run the passed configuration python script for custom running of simulation. For example::

    dtk run example_sweep.py

.. dtk-cmd-option:: --hpc

Overrides where the simulation will be ran. Even if the python configuration passed defines the location ``LOCAL``, the simulations will be ran on HPC::

    dtk run example_simulation.py --hpc

.. dtk-cmd-option:: --priority <priority>

Overrides the :setting:`priority` setting of the :ref:`dtksetup`.
Priority can take the following values:

    - ``Lowest``
    - ``BelowNormal``
    - ``Normal``
    - ``AboveNormal``
    - ``Highest``


For example, if we have a simulation supposed to run locally, we can force it to be HPC with lowest priority by using::

    dtk run example_local_simulation.py --hpc --priority Lowest

.. dtk-cmd-option:: --node_group <node_group>

Allows to overrides the :setting:`node_group` setting of the :ref:`dtksetup`.


``status``
-----------

.. dtk-cmd:: status

Allows to check the status of a given experiment.

.. dtk-cmd-option:: --expId <experiment_id>, -e <experiment_id>

Specified for which experiment we want to check the status.
If this argument is not specified, the command will check the most recent experiment created.

The ``experiment_id`` is displayed after issuing a ``dtk run`` command:

.. code-block:: doscon
    :linenos:
    :emphasize-lines: 8,12

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

    dtk status --expId 2016_04_27_10_42_42_675000

Which will return:

.. code-block:: doscon

    c:\dtk-tools\examples>dtk status --expId 2016_04_27_10_42_42_675000
    Reloading ExperimentManager from: simulations\ExampleSim_2016_04_27_10_42_42_675000.json
    Job states:
    {
        "12232": "Success"
    }
    {'Success': 1}

Letting us know that the 1 simulation of our experiment completed successfully. You can learn more about the simulation states in the documentation related to the :ref:`experimentmanager`.

.. dtk-cmd-option:: --repeat

Repeat status check until job is done processing. Without this option, the status command will only return the current state and return. With this option, the status of the experiment will be displayed at regular intervals until its completion.
For example:

.. code-block:: doscon

    c:\dtk-tools\examples>dtk status --expId 2016_04_27_12_15_09_172000 --repeat
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

