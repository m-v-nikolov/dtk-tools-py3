============================
Creating a simple simulation
============================

In this recipe we will learn how to create and run a simple simulation.
Lets create an ``example`` folder and create a ``simple_simulation.py`` file.

The first thing to do is to create a :ref:`dtkconfigbuilder`. For this example, we will use the :meth:`.from_defaults` class method
of the :class:`.DTKConfigBuilder` to instantiate a config builder from a set of default. We will pass the ``VECTOR_SIM`` type to
the function to get the standard vector simulation::

    from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
    cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')

At this stage, the config builder contains an empty campaign and a default configuration as shown::

    print cb.campaign
    # Prints:
    # {'Campaign_Name': 'Empty Campaign', 'Events': [], 'Use_Defaults': 1}

    print cb.config
    # Prints:
    # {'parameters': {'Population_Scale_Type': 'FIXED_SCALING', 'Climate_Model': 'CLIMATE_BY_DATA', 'Node_Grid_Size': 0.042, 'Sample_Rate_5_9': 1, [...]

The simulation cannot be ran in this state because the defaults do not include any climate or demographics.
