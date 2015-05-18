from ..generic.geography import set_geography
from species import set_larval_habitat, set_species_param

class StudySite(object):

    site=''
    static=False

    @classmethod
    def setup(cls,geography):
        geo_parts=geography.split('.')
        if len(geo_parts)==2 and geo_parts[1]=='static':
            cls.site=geo_parts[0]
            cls.static=True
        else:
            cls.site=geography

    @classmethod
    def set_geography(cls,cb,site):
        set_geography(cb,site,cls.static)

# Configuration of study-site geographies
def configure_site(cb, site):
    StudySite.setup(site)
    cb.set_param("Config_Name", StudySite.site)
    cfg_fn=globals().get('configure_' + StudySite.site.lower(), None)
    if cfg_fn:
        cfg_fn(cb)
    else:
        raise Exception('%s study site not yet implemented.' % StudySite.site)

#Namawala, Tanzania: EIR = 400
def configure_namawala(cb):
    StudySite.set_geography(cb, "Namawala")
    set_larval_habitat( cb, {"arabiensis" : [7.5e9, 1e7],
                             "funestus"   : [4e8],
                             "gambiae"    : [8.3e8, 1e7]})

#Sugungum, Garki, Jigawa, Nigeria: EIR = 132 (56 from funestus)
def configure_sugungum(cb):
    StudySite.set_geography(cb, "Garki_Single")
    set_larval_habitat( cb, {"arabiensis" : [2.3e9, 1.25e7],
                             "funestus"   : [6e8],
                             "gambiae"    : [2.3e9, 1.25e7]})

#Matsari, Garki, Jigawa, Nigeria: EIR = 68 (2 from funestus)
def configure_matsari(cb):
    StudySite.set_geography(cb, "Garki_Single")
    set_larval_habitat( cb, {"arabiensis" : [2.2e9, 1.25e7],
                             "funestus"   : [2.5e7],
                             "gambiae"    : [2.2e9, 1.25e7]})

#Rafin Marke, Garki, Jigawa, Nigeria: EIR = 18
def configure_rafin_marke(cb):
    StudySite.set_geography(cb, "Garki_Single")
    set_larval_habitat( cb, {"arabiensis" : [5e8, 8e6],
                             "gambiae"    : [5e8, 8e6]})

#Dielmo, Senegal: EIR = 200
def configure_dielmo(cb):
    StudySite.set_geography(cb, "Dielmo")
    set_larval_habitat(cb, {"arabiensis" : [4e9, 1e7],
                            "funestus"   : [5e8],
                            "gambiae"    : [4e9, 1e7]})

#Ndiop, Senegal: EIR = 20
def configure_ndiop(cb):
    StudySite.set_geography(cb, "Ndiop")
    set_larval_habitat(cb, {"arabiensis" : [4e8, 5e6],
                            "gambiae"    : [4e8, 5e6]})

#Thies, Senegal
def configure_thies(cb):
    StudySite.set_geography(cb, "Thies")
    set_larval_habitat(cb, {"arabiensis" : [4e7, 1.5e6],
                            "gambiae"    : [4e7, 1.5e6]})

# Burkina sites from A L Ouedraogo
def configure_dapelogo(cb) :
    StudySite.set_geography(cb, "Dapelogo")
    set_larval_habitat(cb, {"funestus" : [5e8],
                            "gambiae"  : [3e10, 1e8]})
def configure_laye(cb) :
    StudySite.set_geography(cb, "Laye")
    set_larval_habitat(cb, {"funestus" : [5e7],
                            "gambiae"  : [3e9, 1e7]})

# Sinazongwe, Southern, Zambia: EIR ~= 20
def configure_sinazongwe(cb):
    StudySite.set_geography(cb, "Sinazongwe")
    set_larval_habitat(cb, {"arabiensis":[2e9, 2e8]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.5)

# Gwembe, Southern, Zambia: EIR ~= 0.1-20
def configure_gwembe2node(cb):
    StudySite.set_geography(cb, "Gwembe2Node")
    set_larval_habitat(cb, {"arabiensis":[2e9, 8e7]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.8)

# Gwembe + Sinazongwe, Southern, Zambia: EIR ~= 0.1-20
def configure_gwembesinazongwehealthfacility(cb):
    StudySite.set_geography(cb, "GwembeSinazongweHealthFacility")
    set_larval_habitat(cb, {"arabiensis":[2e9, 8e7]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.8)

def configure_gwembesinazongwepopcluster(cb):
    StudySite.set_geography(cb, "GwembeSinazongwePopCluster")
    #set_larval_habitat(cb, {"arabiensis":[2e9, 8e7]})
    #set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.8)
    set_larval_habitat(cb, {"arabiensis":[2e9, 2e8]})
    set_species_param(cb,"arabiensis","Indoor_Feeding_Fraction",0.5)

# Mocuba, Zambezia, Mozambique: EIR = 70
def configure_mocuba(cb):
    StudySite.set_geography(cb, "Mocuba")
    set_larval_habitat(cb, {"arabiensis"  : [1e8, 5e6],
                            "funestus"    : [8e8]})

# West Kenya: EIR ~ 100
def configure_west_kenya(cb):
    StudySite.set_geography(cb, "West_Kenya")
    set_larval_habitat(cb, {"arabiensis" : [2.2e9, 1e7],
                            "funestus"   : [7e8],
                            "gambiae"    : [5.5e9, 1e7]})

# Solomon_Islands
def configure_solomon_islands(cb):
    StudySite.set_geography(cb, "Solomon_Islands")
    set_larval_habitat(cb, {"farauti" : [6e9]})

def configure_solomon_islands_2node(cb):
    StudySite.set_geography(cb, "Solomon_Islands_2Node")
    set_larval_habitat(cb, {"farauti" : [6e9]})
    

# Nabang on Chinese-Burmese border
def configure_nabang(cb):
    StudySite.set_geography(cb, "Nabang")
    set_larval_habitat(cb, {"maculatus" : [1e8],
                            "minimus": [1e8]})

# Thailand: same habitat for two species, 
# but maculatus more zoophilic --> fewer human bites
def configure_tha_song_yang(cb):
    StudySite.set_geography(cb, "Tha_Song_Yang")
    set_larval_habitat(cb, {"minimus" : [1e8 ],
                            "maculatus": [1e8]})