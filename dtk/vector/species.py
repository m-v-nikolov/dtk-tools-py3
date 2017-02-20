import copy
import warnings

param_block = {

    "Larval_Habitat_Types": {
        "TEMPORARY_RAINFALL": 8e8,
        "CONSTANT": 8e7
    },

    "Aquatic_Arrhenius_1": 84200000000,
    "Aquatic_Arrhenius_2": 8328,
    "Aquatic_Mortality_Rate": 0.1,

    "Immature_Duration": 2,

    "Adult_Life_Expectancy": 10,
    "Days_Between_Feeds": 3,
    "Anthropophily": 0.95,  # species- and site-specific feeding parameters
    "Indoor_Feeding_Fraction": 0.5,
    "Egg_Batch_Size": 100,

    "Acquire_Modifier": 0.2,  # VECTOR_SIM uses a factor here for human-to-mosquito infectiousness, while MALARIA_SIM explicitly models gametocytes
    "Infected_Arrhenius_1": 117000000000,
    "Infected_Arrhenius_2": 8336,
    "Infected_Egg_Batch_Factor": 0.8,

    "Infectious_Human_Feed_Mortality_Factor": 1.5,
    "Transmission_Rate": 0.9  # Based on late-2013 calibration of PfPR vs EIR favoring 1.0 to 0.5
}

# An. arabiensis
arabiensis_param_block = copy.deepcopy(param_block)

# An. funestus
funestus_param_block = copy.deepcopy(param_block)
mod_funestus_params = {
    "Larval_Habitat_Types": {
        "WATER_VEGETATION": 2e7
    },
    "Indoor_Feeding_Fraction": 0.95,
}
funestus_param_block.update(mod_funestus_params)

# extra funestus for Munyumbwe
munyumbwe_funestus_param_block = copy.deepcopy(funestus_param_block)

# An. gambiae
gambiae_param_block = copy.deepcopy(param_block)
gambiae_param_block["Indoor_Feeding_Fraction"] = 0.95

# An. farauti
farauti_param_block = copy.deepcopy(param_block)
mod_farauti_params = {

    "Larval_Habitat_Types": {
        "BRACKISH_SWAMP": 10000000000
    },
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
# previous to 160722, maculatus block had
#    "Larval_Habitat_Types": {
#        "WATER_VEGETATION": 1e7
#    },
#    "Anthropophily": 0.3,
#    "Indoor_Feeding_Fraction": 0.4,
# on 160722, modified to Trung Trop Med Intl Health 2005 data from Ratanakiri
# maculatus seasonal with rainfall (Durnez Malar J 2013)
maculatus_param_block = copy.deepcopy(param_block)
mod_maculatus_params = {

    "Larval_Habitat_Types": {
        "TEMPORARY_RAINFALL": 1e7,
        "CONSTANT": 1e6
    },
    "Adult_Life_Expectancy": 7,
    "Days_Between_Feeds": 3,
    "Anthropophily": 0.5,
    "Indoor_Feeding_Fraction": 0.05,
    "Egg_Batch_Size": 70,
    "Acquire_Modifier": 0.2,
    "Transmission_Rate": 0.8
}
maculatus_param_block.update(mod_maculatus_params)

# An. minimus
# http://www.bioone.org/doi/abs/10.1603/033.046.0511
# http://www.map.ox.ac.uk/explore/mosquito-malaria-vectors/bionomics/anopheles-minimus/
# previous to 160722, minimus block had
#    "Larval_Habitat_Types": {
#        "WATER_VEGETATION": 1e7
#    },
#    "Anthropophily": 0.93,
#    "Indoor_Feeding_Fraction": 0.95,
# on 160722, modified to Trung Trop Med Intl Health 2005 data from Ratanakiri
# minimus more present during drier periods after rainy season
minimus_param_block = copy.deepcopy(param_block)
mod_minimus_params = {

    "Larval_Habitat_Types": {
        "WATER_VEGETATION": 1e7 # update habitat type?
    },
    "Adult_Life_Expectancy": 7,
    "Days_Between_Feeds": 3,
    "Anthropophily": 0.5,
    "Indoor_Feeding_Fraction": 0.5,
    "Egg_Batch_Size": 70,
    "Acquire_Modifier": 0.2,
    "Transmission_Rate": 0.8
}
minimus_param_block.update(mod_minimus_params)

# An. dirus
# Trung Trop Med Intl Health 2005
# Durnez Malar J 2013
# dirus more abundant during rainy season but also some constant portion in forest
dirus_param_block = copy.deepcopy(param_block)
mod_dirus_params = {

    "Larval_Habitat_Types": {
        "TEMPORARY_RAINFALL": 1e7,
        "CONSTANT": 1e6
    },
    "Adult_Life_Expectancy": 7,
    "Days_Between_Feeds": 3,
    "Anthropophily": 0.95,
    "Indoor_Feeding_Fraction": 0.3,
    "Egg_Batch_Size": 70,
    "Acquire_Modifier": 0.2,
    "Transmission_Rate": 0.8
}
dirus_param_block.update(mod_dirus_params)


# An. albimanus
# CDC Malar J 2016 review
albimanus_param_block = copy.deepcopy(param_block)
mod_albimanus_params = {

    "Larval_Habitat_Types": { # seasonal with rainfall
        "TEMPORARY_RAINFALL": 1e7,
        "CONSTANT": 1e6
    },
    "Adult_Life_Expectancy": 5, # daily survival rate somewhere between 0.7 and 0.9
    "Days_Between_Feeds": 3, # observed 2.6 to 5.2
    "Anthropophily": 0.5,
    "Indoor_Feeding_Fraction": 0.1,
    "Egg_Batch_Size": 70,
    "Acquire_Modifier": 0.2, # ?
    "Transmission_Rate": 0.8 # ?
}
albimanus_param_block.update(mod_albimanus_params)

# An. aegypti
# Dengue
aegypti_param_block = {
    "Acquire_Modifier": 1,
    "Adult_Life_Expectancy": 14,
    "Anthropophily": 0.95,
    "Aquatic_Arrhenius_1": 9752291.727,
    "Aquatic_Arrhenius_2": 5525.492,
    "Aquatic_Mortality_Rate": 0.12,
    "Cycle_Arrhenius_1": 4.120591E10,
    "Cycle_Arrhenius_2": 7.740230E3,
    "Cycle_Arrhenius_Reduction_Factor": 0.58,
    "Days_Between_Feeds": 3,
    "Egg_Batch_Size": 70,
    "Egg_Survival_Rate": 0.99,
    "Larval_Habitat_Types": {
        "TEMPORARY_RAINFALL": 1.125e10
    },
    "Immature_Duration": 2,
    "Indoor_Feeding_Fraction": 1,
    "Infected_Arrhenius_1": 4.784476E12,
    "Infected_Arrhenius_2": 9550,
    "Infected_Egg_Batch_Factor": 1,
    "Infectious_Human_Feed_Mortality_Factor": 1,
    "Nighttime_Feeding_Fraction": 0,
    "Transmission_Rate": 0.5
}


# Dictionary of params by species name
vector_params_by_species = {
    "arabiensis": arabiensis_param_block,
    "funestus": funestus_param_block,
    "munyumbwe_funestus": munyumbwe_funestus_param_block,
    "farauti": farauti_param_block,
    "gambiae": gambiae_param_block,
    "maculatus": maculatus_param_block,
    "minimus": minimus_param_block,
    "dirus": dirus_param_block,
    "albimanus": albimanus_param_block,
    "aegypti": aegypti_param_block
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
        pp[s] = copy.deepcopy(vector_params_by_species[s])
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


def update_species_param(cb, species, parameter, value, overwrite):
    """ Update a 'Vector_Species_Param' variable in a config file; return a length-one dict with a numeric value.

    :param cb: DTKConfigBuilder object with a 'config' attribute.
    :param species: (string) vector species whose parameter will be updated.
    :param parameter: (string) 'Vector_Species_Param' variable to be updated.
    :param value: (float, dict) New value for 'parameter'.
    Note that the function only returns the first key-value pair in 'value'.
    :param overwrite: (logical) Relevant only if 'value' is a dict.
    If True, will replace the entire original parameter with whatever is passed in 'value'. If False, will change only the elements specified in 'value'.
    :return: a dict whose key traces the config parameters from 'species' onward (including the key of 'value' if 'value' is a dict) and whose value is equal to the updated config value.
    """

    if isinstance(value, dict):

        if overwrite:
            # update values in 'parameter' without deleting what's already there.
            # i.e: update the "TEMPORARY RAINFALL" value in a "Larval_Habitat_Types" object
            # without eliminating the "CONSTANT" value
            for k, v in value.iteritems():
                cb.config['parameters']['Vector_Species_Params'][species][parameter][k] = v
        else:
            cb.config['parameters']['Vector_Species_Params'][species][parameter] = value

        if len(value) > 1:
            warnings.warn("value is a dict of length>1, returning only the first value.")

        return {'.'.join([species, value.keys()[0]]): value.values()[0]}
    else:
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
        habitats = get_species_param(cb, s, 'Larval_Habitat_Types')
        scaled_habitats = {h: scale * v for (h, v) in habitats.items()}
        set_species_param(cb, s, 'Larval_Habitat_Types', scaled_habitats)


def set_larval_habitat(cb, habitats):
    """
    Set vector species and habitat parameters of config argument and return
    Example:
    habitats = {"arabiensis": {"TEMPORARY_RAINFALL": 1.7e9, "CONSTANT": 1e7}}
    """

    for species, habitat in habitats.items():
        set_species_param(cb, species, 'Larval_Habitat_Types', habitat)

