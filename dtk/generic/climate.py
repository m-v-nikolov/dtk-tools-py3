params = {

    "Climate_Model": "CLIMATE_BY_DATA",
    "Climate_Update_Resolution": "CLIMATE_UPDATE_DAY",
    "Enable_Climate_Stochasticity": 0,

    "Air_Temperature_Filename": "",
    "Air_Temperature_Offset": 0,
    "Air_Temperature_Variance": 2,
    "Base_Air_Temperature": 22.0,

    "Relative_Humidity_Filename": "",
    "Relative_Humidity_Scale_Factor": 1,
    "Relative_Humidity_Variance": 0.05,
    "Base_Relative_Humidity": 0.75,

    "Land_Temperature_Filename": "",
    "Land_Temperature_Offset": 0,
    "Land_Temperature_Variance": 2,
    "Base_Land_Temperature": 26.0,

    "Rainfall_Filename": "",
    "Rainfall_Scale_Factor": 1,
    "Enable_Rainfall_Stochasticity": 1,
    "Base_Rainfall": 10.0

}


def set_climate_constant(cb, **kwargs):
    """
    Set the climate to constant weather by changing the ``Climate_Model`` parameter to ``CLIMATE_CONSTANT``.
    Also set the extra parameters passed.

    :param cb: The :py:class:`DTKConfigBuilder` object containing the current configuration
    :param kwargs: Extra parameters to change in the config file
    :return: Nothing
    """
    cb.set_param('Climate_Model', 'CLIMATE_CONSTANT')
    cb.update_params(kwargs, validate=True)