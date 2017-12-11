=============================
Running your first simulation
=============================

dtk-tools is packaged with a lot of examples demonstrating the features of the tools.
You can find the examples in the ``dtk-tools/examples`` folder.

.. warning::
    We are recommending to not modify the examples directly in the dtk-tools folder but to copy the folder in your usual working directory and work from there.
    That way you can always go back to the built-in examples if needed.

Running example_sim
===================

From a command line where the tools are available, navigate to your newly copied examples folder::

    cd examples

We will run the most basic simulation available in the ``example_sim.py`` script. To do so we will use the dtk command :dtk-cmd:`run` as follow::

    dtk run example_sim.py

This command will create a simulation and send it to COMPS by default so you may be prompted to enter your COMPS credentials.
We can break the output returned by the command in different parts. The first part presents information about the experiment created:

.. code-block:: json

    {
       "command_line": "Assets\\Eradication.exe --config config.json --input-path ./Assets",
       "date_created": "2017-11-09 13:21:11.780551",
       "dtk_tools_revision": "1.0b3",
       "endpoint": "https://comps2.idmod.org",
       "exp_id": "2c664be8-93c5-e711-80c6-f0921c167864",
       "exp_name": "ExampleSim",
       "id": "ExampleSim_2c664be8-93c5-e711-80c6-f0921c167864",
       "location": "HPC",
       "selected_block": "HPC",
       "setup_overlay_file": "c:\\Eradication\\examples\\simtools.ini",
       "sim_root": "$COMPS_PATH(USER)\\output",
       "sim_type": "VECTOR_SIM",
       "working_directory": "c:\\Eradication\\examples"
    }

It shows you that the experiment was run on COMPS (``"location": "HPC"``), but also other useful information like the id
of the newly created experiment (``"exp_id": "2c664be8-93c5-e711-80c6-f0921c167864"``).

Following the experiment information, you will find the information about the simulations created in this experiment.
The ``example_sim.py`` example creates a single simulation but the tools are geared towards large experiments.

.. code-block:: console

    Creating the simulations (each . represent up to 20)
    | Creator processes: 1 (max: 16)
    | Simulations per batch: 20
    | Simulations Count: 1
    | Max simulations per threads: 20

This tells us that the system created 1 simulation (``Simulation Count: 1``) using 1 process (``Creator processes: 1``).

The last part shows the tags associated to the simulations contained in the experiment that we just ran. Because
experiments can contain a lot of simulations, only the first few are shown and looks like:

.. code-block:: json

    [
       {
          "2d664be8-93c5-e711-80c6-f0921c167864": {
             "environment": "Bayesian",
             "exe_collection_id": "ba726085-1fc3-e711-80c6-f0921c167864",
             "input_collection_id": "7fb0e472-8371-e711-80c1-f0921c167860"
          }
       }
    ]

This shows that we created the simulation with the id ``2d664be8-93c5-e711-80c6-f0921c167864`` and this simulation has
three tags:

- ``environment`` with the value ``Bayesian``
- ``exe_collection_id``
- ``input_collection_id``

More tags can be set on simulations as appropriate but this example is only keeping it to the tags automatically set
by the system.

Monitoring status
=================

At this point the experiment is running. You can check its status by with the :dtk-cmd:`status` command::

    dtk status

This command assumes you are interested by the status of the latest ran experiment on your system and returns the following::

    ExampleSim ('2c664be8-93c5-e711-80c6-f0921c167864') states:
    {
        "2d664be8-93c5-e711-80c6-f0921c167864": "Running"
    }
    {'Running': 1}


As you can see, our ``ExampleSim`` experiment, contains one ``Running`` simulation.
Let's check for the status a few more time until we see::

    ExampleSim ('2c664be8-93c5-e711-80c6-f0921c167864') states:
    {
        "2d664be8-93c5-e711-80c6-f0921c167864": "Succeeded"
    }
    {'Succeeded': 1}

At this point our experiment has successfully completed.

Showing graphs
==============

Now that our experiment completed successfully, it would be interesting to see some output graphs.
The :dtk-cmd:`analyze` command is here for this reason. The command can take different parameters including the
experiment id and which analyzer we want to use. For this example, we will use a built-in analyzer displaying time series from the ``InsetChart.json`` output file::

    dtk analyze -a time_series

Once again here, we did not specify any experiment id as we want to chart the most recent one.
This command should open a window showing the graphs.