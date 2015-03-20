import sys
from ..generic.geography import set_geography
from vector_species_cff import set_larval_habitat

#Navrongo, Ghana: EIR = 450+
def configure_navrongo(config):
    raise Exception("Navrongo geography not yet implemented")
    return config

#Namawala, Tanzania: EIR = 400
def configure_namawala(config):
    config = set_geography(config, "Namawala")
    config = set_larval_habitat( config, 
                                {"arabiensis" : [7.5e9, 1e7],
                                 "funestus"   : [4e8],
                                 "gambiae"    : [8.3e8, 1e7]})
    return config

#Idete, Tanzania: EIR = 400
def configure_idete(config):
    raise Exception("Idete geography not yet implemented")
    return config

#Sugungum, Garki, Jigawa, Nigeria: EIR = 132 (56 from funestus)
def configure_sugungum(config):
    config = set_geography(config, "Garki_Single")
    config = set_larval_habitat( config, 
                                {"arabiensis" : [2.3e9, 1.25e7],
                                 "funestus"   : [6e8],
                                 "gambiae"    : [2.3e9, 1.25e7]})
    return config

#Matsari, Garki, Jigawa, Nigeria: EIR = 68 (2 from funestus)
def configure_matsari(config):
    config = set_geography(config, "Garki_Single")
    config = set_larval_habitat( config, 
                                {"arabiensis" : [2.2e9, 1.25e7],
                                 "funestus"   : [2.5e7],
                                 "gambiae"    : [2.2e9, 1.25e7]})
    return config

#Rafin Marke, Garki, Jigawa, Nigeria: EIR = 18
def configure_rafin_marke(config):
    config = set_geography(config, "Garki_Single")
    config = set_larval_habitat( config, 
                                {"arabiensis" : [5e8, 8e6],
                                 "gambiae"    : [5e8, 8e6]})
    return config

#Dielmo, Senegal: EIR = 200
def configure_dielmo(config):
    config = set_geography(config, "Dielmo")
    config = set_larval_habitat( config, 
                                {"arabiensis" : [4e9, 1e7],
                                 "funestus"   : [5e8],
                                 "gambiae"    : [4e9, 1e7]})
    return config

#Ndiop, Senegal: EIR = 20
def configure_ndiop(config):
    config = set_geography(config, "Ndiop")
    config = set_larval_habitat( config, 
                                {"arabiensis" : [4e8, 5e6],
                                 "gambiae"    : [4e8, 5e6]})
    return config

#Thies, Senegal
def configure_thies(config):
    config = set_geography(config, "Thies")
    config = set_larval_habitat( config, 
                                {"arabiensis" : [4e7, 1.5e6],
                                 "gambiae"    : [4e7, 1.5e6]})
    return config

# Sinazongwe, Southern, Zambia: EIR = 20
def configure_sinazongwe(config):
    config = set_geography(config, "Sinazongwe")
    config = set_larval_habitat(config, {"arabiensis":[2e9, 8e7]})
    config["parameters"]["Vector_Species_Params"]["arabiensis"]["Indoor_Feeding_Fraction"] = 0.8
    return config

def configure_sinazongwe_dry(config):
    config = set_geography(config, "Sinazongwe")
    config = set_larval_habitat(config, {"arabiensis":[2e9, 2e8]})
    config["parameters"]["Vector_Species_Params"]["arabiensis"]["Indoor_Feeding_Fraction"] = 0.5
    return config

def configure_sinazongwe_constant(config):
    config = set_geography(config, "Sinazongwe")
    config = set_larval_habitat(config, {"arabiensis":[8e8, 1e7]})
    config["parameters"]["Vector_Species_Params"]["arabiensis"]["Indoor_Feeding_Fraction"] = 0.5
    config["Climate_Model"] = "CLIMATE_CONSTANT"
    return config

# Gwembe, Southern, Zambia: EIR = 1-20
def configure_gwembe2node(config):
    config = set_geography(config, "Gwembe2Node")
    config = set_larval_habitat(config, {"arabiensis":[2e9, 8e7]})
    config["parameters"]["Vector_Species_Params"]["arabiensis"]["Indoor_Feeding_Fraction"] = 0.8
    return config

# Gwembe + Sinazongwe, Southern, Zambia: EIR = 1-20
def configure_gwembe_sinazongwe_health_facility(config):
    config = set_geography(config, "GwembeSinazongweHealthFacility")
    config = set_larval_habitat(config, {"arabiensis":[2e9, 8e7]})
    config["parameters"]["Vector_Species_Params"]["arabiensis"]["Indoor_Feeding_Fraction"] = 0.8
    return config

def configure_gwembe_sinazongwe_pop_cluster(config):
    config = set_geography(config, "GwembeSinazongwePopCluster")
    #config = set_larval_habitat(config, {"arabiensis":[2e9, 8e7]})
    #config["parameters"]["Vector_Species_Params"]["arabiensis"]["Indoor_Feeding_Fraction"] = 0.8
    config = set_larval_habitat(config, {"arabiensis":[2e9, 2e8]})
    config["parameters"]["Vector_Species_Params"]["arabiensis"]["Indoor_Feeding_Fraction"] = 0.5
    return config

# Mocuba, Zambezia, Mozambique: EIR = 70
def configure_mocuba(config):
    config = set_geography(config, "Mocuba")
    config = set_larval_habitat(config, 
                                {"arabiensis"  : [1e8, 5e6],
                                 "funestus"    : [8e8]})
    return config

# West Kenya: EIR ~ 100
def configure_west_kenya(config):
    config = set_geography(config, "West_Kenya")
    config = set_larval_habitat( config, 
                                {"arabiensis" : [2.2e9, 1e7],
                                 "funestus"   : [7e8],
                                 "gambiae"    : [5.5e9, 1e7]})
    return config

# Solomon_Islands
def configure_solomons(config):
    config = set_geography(config, "Solomon_Islands")
    config = set_larval_habitat( config, 
                                {"farauti" : [6e9]})
    return config

def configure_solomons_2node(config):
    config = set_geography(config, "Solomon_Islands_2Node")
    config = set_larval_habitat( config, 
                                {"farauti" : [6e9]})
    return config

def configure_nabang(config):
    config = set_geography(config, "Nabang")
    config = set_larval_habitat( config, 
                                {"maculatus" : [1e8],
                                 "minimus": [1e8]})
    return config

# Thailand: same habitat for two species, 
# but maculatus more zoophilic --> fewer human bites
def configure_Tha_Song_Yang(config):
    config = set_geography(config, "Tha_Song_Yang")
    config = set_larval_habitat( config, 
                                {"minimus" : [1e8 ],
                                 "maculatus": [1e8]})

# Burkina sites from ALOuedraogo
def configure_burkina(config):
    config = set_geography(config, "Dapelogo")
    config = set_larval_habitat( config, 
                                {"funestus" : [5e8],
                                 "gambiae"    : [3e10, 1e8]})
    return config

def configure_dapelogo(config) :
    config = set_geography(config, "Dapelogo")
    config = configure_burkina(config)

def configure_laye(config) :
    config = set_geography(config, "Laye")
    config = configure_burkina(config)


# Dictionary of supported study-site configuration functions keyed on site name
study_sites_fns = { "Sinazongwe": configure_sinazongwe_dry, #configure_sinazongwe,
                    "SinazongweWithDrySeason": configure_sinazongwe_dry,
                    "SinazongweConstant": configure_sinazongwe_constant,
                    "Gwembe2Node": configure_gwembe2node,
                    "GwembeSinazongweHealthFacility": configure_gwembe_sinazongwe_health_facility,
                    "GwembeSinazongwePopCluster": configure_gwembe_sinazongwe_pop_cluster,
                    "Namawala": configure_namawala,
                    "Rafin_Marke": configure_rafin_marke,
                    "Matsari": configure_matsari,
                    "Sugungum": configure_sugungum,
                    "Mocuba": configure_mocuba,
                    "Thies": configure_thies,
                    "Dielmo": configure_dielmo,
                    "Ndiop": configure_ndiop,
                    "West_Kenya": configure_west_kenya,
                    "Nabang": configure_nabang,
                    "Tha_Song_Yang": configure_Tha_Song_Yang,
                    "Solomon_Islands": configure_solomons,
                    "Solomon_Islands_2Node": configure_solomons_2node,
                    "Dapelogo": configure_dapelogo,
                    "Laye": configure_laye }

# Configuration of study-site geographies
def configure_site(config, site):

    if site not in study_sites_fns.keys():
        raise Exception("Don't know how to configure site: %s " % site)

    config["parameters"]["Config_Name"] = site
    study_sites_fns[site](config)

    return config
