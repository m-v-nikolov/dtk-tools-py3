import copy


param_block = {
    
    "Larval_Habitat_Types":{
                            "TEMPORARY_RAINFALL": 8e8,
                            "CONSTANT": 8e7
                            },
    
    "Habitat_Type": [ "TEMPORARY_RAINFALL", "CONSTANT" ], ##
    "Required_Habitat_Factor": [ 8e8, 8e7 ], ##

    "Aquatic_Arrhenius_1": 84200000000, 
    "Aquatic_Arrhenius_2": 8328, 
    "Aquatic_Mortality_Rate": 0.1, 

    "Immature_Duration": 2, 

    "Adult_Life_Expectancy": 10,
    "Days_Between_Feeds": 3, 
    "Anthropophily": 0.95,           ## species- and site-specific feeding parameters
    "Indoor_Feeding_Fraction": 0.5,  ##
    "Egg_Batch_Size": 100, 

    "Acquire_Modifier": 0.2, ## VECTOR_SIM uses a factor here for human-to-mosquito infectiousness, while MALARIA_SIM explicitly models gametocytes
    "Infected_Arrhenius_1": 117000000000, 
    "Infected_Arrhenius_2": 8336, 
    "Infected_Egg_Batch_Factor": 0.8,

    "Infectious_Human_Feed_Mortality_Factor": 1.5, 
    "Transmission_Rate": 0.9 ## Based on late-2013 calibration of PfPR vs EIR favoring 1.0 to 0.5
}

# An. arabiensis
arabiensis_param_block = copy.deepcopy(param_block)

# An. funestus

'''
# original setting
funestus_param_block = copy.deepcopy(param_block)
mod_funestus_params = {
    "Indoor_Feeding_Fraction": 0.95,
    "Habitat_Type": [ "WATER_VEGETATION" ],
    "Required_Habitat_Factor": [ 2e7 ]
}
funestus_param_block.update(mod_funestus_params)
'''

# 2.5 release setting
funestus_param_block = copy.deepcopy(param_block)
mod_funestus_params = {
    "Larval_Habitat_Types":{
        "WATER_VEGETATION": 2e7
        },
    "Indoor_Feeding_Fraction": 0.95,
}
funestus_param_block.update(mod_funestus_params)

'''
# need this modification to run sims w/ piecewise_monthly hab; that will need to change as related code is consolidated in the DTK
funestus_param_block = copy.deepcopy(param_block)
mod_funestus_params = {
    "Indoor_Feeding_Fraction": 0.95,
    "Habitat_Type": [ "PIECEWISE_MONTHLY",  "WATER_VEGETATION"],
    "Required_Habitat_Factor": [ 1e8, 2e7 ]
}
funestus_param_block.update(mod_funestus_params)
'''

# An. gambiae
gambiae_param_block = copy.deepcopy(param_block)
gambiae_param_block["Indoor_Feeding_Fraction"] = 0.95

# An. farauti
farauti_param_block = copy.deepcopy(param_block)
mod_farauti_params = {
    "Habitat_Type": [ "BRACKISH_SWAMP" ], 
    "Required_Habitat_Factor": [ 10000000000 ], 
    "Adult_Life_Expectancy": 5.9, 
    "Days_Between_Feeds": 2, 
    "Anthropophily": 0.97, 
    "Indoor_Feeding_Fraction": 0.05, 
    "Egg_Batch_Size": 70, 
    "Acquire_Modifier": 0.05, 
    "Transmission_Rate": 0.8
}
farauti_param_block.update(mod_farauti_params)

# Thailand_Anopheles_Survey_1968.pdf
# An. maculatus
# http://www.bioone.org/doi/full/10.3376/038.034.0108
# http://www.map.ox.ac.uk/explore/mosquito-malaria-vectors/bionomics/anopheles-maculatus/
maculatus_param_block = copy.deepcopy(param_block)
mod_maculatus_params = {
    "Habitat_Type": [ "WATER_VEGETATION" ], 
    "Required_Habitat_Factor": [ 1e7 ], 
    "Adult_Life_Expectancy": 7, 
    "Days_Between_Feeds": 3, 
    "Anthropophily": 0.3, 
    "Indoor_Feeding_Fraction": 0.4, 
    "Egg_Batch_Size": 70, 
    "Acquire_Modifier": 0.2, 
    "Transmission_Rate": 0.8
}
maculatus_param_block.update(mod_maculatus_params)

# An. minimus
# http://www.bioone.org/doi/abs/10.1603/033.046.0511
# http://www.map.ox.ac.uk/explore/mosquito-malaria-vectors/bionomics/anopheles-minimus/
minimus_param_block = copy.deepcopy(param_block)
mod_minimus_params = {
    "Habitat_Type": [ "WATER_VEGETATION" ], 
    "Required_Habitat_Factor": [ 1e7 ], 
    "Adult_Life_Expectancy": 7, 
    "Days_Between_Feeds": 3, 
    "Anthropophily": 0.93, 
    "Indoor_Feeding_Fraction": 0.95, 
    "Egg_Batch_Size": 70, 
    "Acquire_Modifier": 0.2, 
    "Transmission_Rate": 0.8
}
minimus_param_block.update(mod_minimus_params)

# Dictionary of params by species name
vector_params_by_species = {
    "arabiensis": arabiensis_param_block,
    "funestus": funestus_param_block,
    "farauti": farauti_param_block,
    "gambiae": gambiae_param_block,
    "maculatus": maculatus_param_block,
    "minimus": minimus_param_block
}

def set_params_by_species(params, ss, sim_type="VECTOR_SIM"):
    """

    :param params:
    :param ss:
    :param sim_type:
    :return:
    """
    pp = {}
    for s in ss:
        pp[s] = vector_params_by_species[s]
        if sim_type == "MALARIA_SIM":
            pp[s]["Acquire_Modifier"] = 0.8  ## gametocyte success modeled explicitly

    vector_species_params = {
        "Vector_Species_Names": ss,
        "Vector_Species_Params": pp
    }
    params.update(vector_species_params)

def set_species_param(cb, species, parameter, value):
    cb.config['parameters']['Vector_Species_Params'][species][parameter] = value
    return {'.'.join([species, parameter]): value}

def get_species_param(cb, species, parameter):
    try:
        return cb.config['parameters']['Vector_Species_Params'][species][parameter]
    except:
        print('Unable to get parameter %s for species %s' % (parameter, species))
        return None

def scale_all_habitats(cb, scale):
    species = cb.get_param('Vector_Species_Names')
    for s in species:
        v = [scale*h for h in get_species_param(cb, s, 'Required_Habitat_Factor')]
        set_species_param(cb, s, 'Required_Habitat_Factor', v)

def set_larval_habitat(cb, habitats):
    """
    Set vector species and habitat parameters of config argument and return
    Example:
    habitats = { "arabiensis" : [1.7e9, 1e7], "funestus" : [2e7] }
    habitats = { "arabiensis" : {"TEMPORARY_RAINFALL":1.7e9,"CONSTANT":1e7} }
    """
    
    cb.set_param('Vector_Species_Names', habitats.keys())
    '''
    for (species, habitat) in habitats.items():
        s = cb.config["parameters"]["Vector_Species_Params"][species]
        if isinstance(habitat, dict):
            s["Habitat_Type"] = habitat.keys()
            s["Required_Habitat_Factor"] = habitat.values()
        elif isinstance(habitat, list):
            s["Required_Habitat_Factor"] = habitat
            if len(habitat) != len(s["Habitat_Type"] ):
                raise Exception("Required_Habitat_Factor argument does not match size of Habitat_Type list")
        else:
            raise Exception("Don't recognize formatting of %s, which must be a dict or list",habitat)
    '''
    return