import copy
import getpass
import datetime
from collections import namedtuple

from dtk.tools.demographics.node import lat_lon_from_nodeid

# --------------------------------------------------------------
# Larval habitat parameters
# --------------------------------------------------------------

params = {
    "Egg_Hatch_Delay_Distribution": "NO_DELAY", 
    "Egg_Saturation_At_Oviposition": "SATURATION_AT_OVIPOSITION", 
    "Mean_Egg_Hatch_Delay": 0,
    "Rainfall_In_mm_To_Fill_Swamp": 1000.0, 
    "Semipermanent_Habitat_Decay_Rate": 0.01, 
    "Temporary_Habitat_Decay_Factor": 0.05, 
    "Larval_Density_Dependence": "UNIFORM_WHEN_OVERPOPULATION", 
    "Vector_Larval_Rainfall_Mortality": "NONE"
}

# --------------------------------------------------------------
# Notre Dame modifications for instar-specific behavior
# --------------------------------------------------------------

notre_dame_params = copy.deepcopy(params)
notre_dame_params.update({
    "Egg_Hatch_Delay_Distribution": "EXPONENTIAL_DURATION", 
    "Egg_Saturation_At_Oviposition": "NO_SATURATION", 
    "Mean_Egg_Hatch_Delay": 2,
    "Larval_Density_Dependence": "GRADUAL_INSTAR_SPECIFIC"})

# --------------------------------------------------------------
# Adjustments to node-specific larval habitat via demographics overlay
# --------------------------------------------------------------

NodesMultipliers=namedtuple('NodesMultipliers',['nodes','multipliers'])

def set_habitat_multipliers(cb, demog_name,
                            NodesMultipliers_list = [ NodesMultipliers(
                                                        nodes=[326436567],
                                                        multipliers={'ALL_HABITATS':1.0} ) ], 
                            res_arcsec = None):

    def resolution_name(res_arcsec=res_arcsec):
        known_resolutions = { 150: '2.5arcmin', 30: '30arcsec' }
        if res_arcsec:
            return known_resolutions[res_arcsec]
        else:
            print('Trying to guess resolution based on malaria being in the tropics.')
            for res,name in known_resolutions.items():
                lat,lon=lat_lon_from_nodeid(NodesMultipliers_list[0].nodes[0],res/3600.)
                if abs(lat)<45: 
                    return name
        raise Exception('No support for resolution other than 30 and 150 arcsec.')

    metadata={'Author': getpass.getuser(),
              'IdReference': 'Gridded world grump'+resolution_name(),
              'NodeCount': sum([len(nm.nodes) for nm in NodesMultipliers_list]),
              'DateCreated': datetime.datetime.now().strftime('%a %b %d %X %Y')}

    nodes=[]
    for nm in NodesMultipliers_list:
        for nodeid in nm.nodes:
            nodes.append({'NodeID': nodeid,
                          'NodeAttributes': { 'LarvalHabitatMultiplier':nm.multipliers } })

    cb.add_demog_overlay(demog_name, {'Nodes': nodes, 'Metadata': metadata})