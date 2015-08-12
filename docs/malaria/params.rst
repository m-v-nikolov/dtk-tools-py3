Params
------

The params.py file initializes the malaria related parameters of the configuration by creating a ``disease_params`` dictionary
and updating it with the defaults found in infection, immunity and symptoms files. It also adds the drug parameters
by including the ``drug_params``. To finish, it includes by default the parameters fir Arabiensis, Funestus and Gambiae
by calling the :any:`set_params_by_species` function.

.. automodule:: dtk.malaria.params
    :members:
    :undoc-members:

:orphan:
