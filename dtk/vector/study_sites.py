import logging

from ..generic.geography import set_geography
from ..generic.climate import set_climate_constant
from species import set_larval_habitat, set_species_param, scale_all_habitats

class StudySite(object):
    site = ''
    static = False

    @classmethod
    def setup(cls, geography):
        geo_parts = geography.split('.')
        if len(geo_parts) == 2 and geo_parts[1] == 'static':
            cls.site = geo_parts[0]
            cls.static = True
        else:
            cls.site = geography
            cls.static = False

    @classmethod
    def set_geography(cls, cb, site, pop_scale=1):
        set_geography(cb, site, cls.static, pop_scale)

def configure_site(cb, site, pop_scale=1):
    StudySite.setup(site)
    cb.set_param("Config_Name", StudySite.site)
    cfg_fn = globals().get('configure_' + StudySite.site.lower(), None)
    if cfg_fn:
        logging.debug('StudySite.site = %s', StudySite.site)
        StudySite.set_geography(cb, geography_from_site(StudySite.site), pop_scale)
        cfg_fn(cb)
        if pop_scale != 1:
            scale_all_habitats(cb, pop_scale)
    else:
        raise Exception('%s study site not yet implemented.' % StudySite.site)
    return {'_site_': site, 'population_scale': pop_scale}

def geography_from_site(site):
    site_splits = site.split('.') # e.g. to accommodate site='Chipepo.static'
    site_to_geography = {
        'Sugungum': 'Garki_Single',
        'Matsari': 'Garki_Single',
        'Rafin_Marke': 'Garki_Single',
                         
        'Chipepo': 'Sinazongwe',
        'SinazongweConstant': 'Sinazongwe'
        }

    geo = site_to_geography.get(site_splits[0], '')
    return '.'.join([geo] + site_splits[1:]) if geo else site

def set_habitat_scale(cb, scale):
    cb.set_param('x_Temporary_Larval_Habitat', scale)    

#-------------------------------------------------------------------------------

#Namawala, Tanzania: EIR = 400
def configure_namawala(cb):
    set_larval_habitat( cb, {"arabiensis" : [7.5e9, 1e7]
                             #"funestus"   : [4e8],
                             #"gambiae"    : [8.3e8, 1e7]
                             })

#Sugungum, Garki, Jigawa, Nigeria: EIR = 132 (56 from funestus)
def configure_sugungum(cb):
    set_larval_habitat( cb, {"arabiensis" : [2.3e9, 1.25e7],
                             "funestus"   : [6e8],
                             "gambiae"    : [2.3e9, 1.25e7]})

#Matsari, Garki, Jigawa, Nigeria: EIR = 68 (2 from funestus)
def configure_matsari(cb):
    set_larval_habitat( cb, {"arabiensis" : [2.2e9, 1.25e7],
                             "funestus"   : [2.5e7],
                             "gambiae"    : [2.2e9, 1.25e7]})

#Rafin Marke, Garki, Jigawa, Nigeria: EIR = 18
def configure_rafin_marke(cb):
    set_larval_habitat( cb, {"arabiensis" : [5e8, 8e6],
                             "gambiae"    : [5e8, 8e6]})

#Dielmo, Senegal: EIR = 200
def configure_dielmo(cb):
    set_larval_habitat(cb, {"arabiensis" : [4e9, 1e7],
                            "funestus"   : [5e8],
                            "gambiae"    : [4e9, 1e7]})

#Ndiop, Senegal: EIR = 20
def configure_ndiop(cb):
    set_larval_habitat(cb, {"arabiensis" : [4e8, 5e6],
                            "gambiae"    : [4e8, 5e6]})

#Thies, Senegal
def configure_thies(cb):
    set_larval_habitat(cb, {"arabiensis" : [4e7, 1.5e6],
                            "gambiae"    : [4e7, 1.5e6]})

# Burkina sites from A L Ouedraogo
def configure_dapelogo(cb) :
    set_larval_habitat(cb, {"funestus" : [5e8],
                            "gambiae"  : [3e10, 1e8]})
def configure_laye(cb) :
    set_larval_habitat(cb, {"funestus" : [5e7],
                            "gambiae"  : [3e9, 1e7]})

# Sinazongwe, Southern, Zambia: EIR ~= 20
def configure_sinazongwe(cb):
    set_larval_habitat(cb, {"arabiensis": {'TEMPORARY_RAINFALL': 2e9, 'CONSTANT': 2e8}})
    set_species_param(cb, "arabiensis", "Indoor_Feeding_Fraction", 0.5)

def configure_chipepo(cb):
    set_larval_habitat(cb, {"arabiensis": {'TEMPORARY_RAINFALL': 1e9, 'CONSTANT': 1e9}})
    set_species_param(cb, "arabiensis", "Indoor_Feeding_Fraction", 0.5)

def configure_sinazongweconstant(cb):
    set_larval_habitat(cb, {"arabiensis": {'CONSTANT': 1.5e9}})
    set_species_param(cb, "arabiensis", "Indoor_Feeding_Fraction", 0.5)
    set_climate_constant(cb, Base_Air_Temperature=22, Base_Rainfall=10)
    cb.enable('Climate_Stochasticity')

# Gwembe, Southern, Zambia: EIR ~= 0.1-20
def configure_gwembe2node(cb):
    set_larval_habitat(cb, {"arabiensis":[2e9, 8e7]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.8)

# Gwembe + Sinazongwe, Southern, Zambia: EIR ~= 0.1-20
def configure_gwembesinazongwehealthfacility(cb):
    set_larval_habitat(cb, {"arabiensis":[2e9, 8e7]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.8)

def configure_gwembesinazongwepopcluster(cb):
    #set_larval_habitat(cb, {"arabiensis":[2e9, 8e7]})
    #set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.8)
    set_larval_habitat(cb, {"arabiensis":[2e9, 2e8]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.5)

def configure_sinamalima_1_node(cb):
    set_geography(cb, "Sinamalima_1_node")
    set_larval_habitat(cb, {"arabiensis":[2e9, 2e8]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.5)
    
def configure_gwembe_1_node(cb):
    set_geography(cb, "Gwembe_1_node")
    set_larval_habitat(cb, {"arabiensis":[2e9, 2e8]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.5)
    
def configure_lukonde_1_node(cb):
    set_geography(cb, "Lukonde_1_node")
    set_larval_habitat(cb, {"arabiensis":[2e9, 2e8]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.5)
    
def configure_munumbwe_1_node(cb):
    set_geography(cb, "Munumbwe_1_node")
    set_larval_habitat(cb, {"arabiensis":[2e9, 2e8]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.5)

# Mocuba, Zambezia, Mozambique: EIR = 70
def configure_mocuba(cb):
    set_larval_habitat(cb, {"arabiensis"  : [1e8, 5e6],
                            "funestus"    : [8e8]})

# West Kenya: EIR ~ 100
def configure_west_kenya(cb):
    set_larval_habitat(cb, {"arabiensis" : [2.2e9, 1e7],
                            "funestus"   : [7e8],
                            "gambiae"    : [5.5e9, 1e7]})

# Solomon_Islands
def configure_solomon_islands(cb):
    set_larval_habitat(cb, {"farauti" : [6e9]})

def configure_solomon_islands_2node(cb):
    set_larval_habitat(cb, {"farauti" : [6e9]})
    

# Nabang on Chinese-Burmese border
def configure_nabang(cb):
    set_larval_habitat(cb, {"maculatus" : [1e8],
                            "minimus": [1e8]})
    
    
def configure_gwembe_sinazongwe_115_nodes(cb):
    set_geography(cb, "Gwembe_Sinazongwe_115_nodes")
    #set_larval_habitat(cb, {"arabiensis":[2e9, 8e7]})
    #set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.8)
    #set_larval_habitat(cb, {"arabiensis":[2e9, 2e8]})
    set_larval_habitat(cb, {"arabiensis":[1e8,  2e6],
                            "funestus":[ 1e8, 2e7 ]})    
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.5)
    

# Thailand: same habitat for two species, 
# but maculatus more zoophilic --> fewer human bites
def configure_tha_song_yang(cb):
    set_larval_habitat(cb, {"minimus" : [1e8 ],
                            "maculatus": [1e8]})