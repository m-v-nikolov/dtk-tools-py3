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
    Test 123das asd
    
    Longer explanation

    PARAMETERS
    =============
    :param cb: fdsfs

    OTHER PARAMETERS
    ==================
    :param kwargs: fsd fsd
    :return: fsdf sdf
    """
    cb.set_param('Climate_Model', 'CLIMATE_CONSTANT')
    cb.update_params(kwargs, validate=True)