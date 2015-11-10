from dtk.malaria.immunity import add_immune_overlays
from dtk.vector.input_EIR_by_site import configure_site_EIR
from dtk.vector.species import set_larval_habitat, set_species_param
from dtk.interventions.health_seeking import add_health_seeking
from dtk.utils.reports.MalariaReport import add_summary_report,add_survey_report
from dtk.interventions.malaria_challenge import add_challenge_trial
from dtk.vector.species import set_larval_habitat, set_species_param
from dtk.interventions.outbreak import recurring_outbreak
from dtk.interventions.itn import add_ITN
import pandas as pd

def config_setup_fn(duration=21915):
    return lambda cb: cb.update_params({'Simulation_Duration' : duration,
                                        'Infection_Updates_Per_Timestep' : 8})

# reporters
def summary_report_fn(start=1,interval=365,nreports=2000,age_bins=[1000],description='Annual_Report'):
    return lambda cb: add_summary_report(cb, start=start, interval=interval, nreports=nreports, description=description,age_bins=age_bins)

def survey_report_fn(days,interval=10000,nreports=1):
    return lambda cb: add_survey_report(cb,survey_days=days,reporting_interval=interval,nreports=nreports)

# vector
def larval_habitat_fn(species, habitats) :
    return lambda cb: set_larval_habitat(cb, {species : habitats})
def species_param_fn(species, param, value) :
    return lambda cb : set_species_param(cb, species, param, value)

# immune overlays
def add_immunity_fn(tags):
    return lambda cb: add_immune_overlays(cb,tags=tags)

# input EIR
def site_input_eir_fn(site,birth_cohort=True, set_site_geography=False):
    return lambda cb: configure_site_EIR(cb,site=site,birth_cohort=birth_cohort, set_site_geography=False)

# health-seeking
def add_treatment_fn(start=0,drug=['Artemether', 'Lumefantrine'],targets=[{'trigger':'NewClinicalCase','coverage':0.8,'seek':0.6,'rate':0.2}]):
    def fn(cb,start=start,drug=drug,targets=targets):
        add_health_seeking(cb,start_day=start,drug=drug,targets=targets)
        cb.update_params({'PKPD_Model': 'CONCENTRATION_VERSUS_TIME'})
    return fn


# ITNs from nodeid-coverage specified in csv
def add_itn_by_node_id_fn(reffname, start=0) :
    def fn(cb) :
        df = pd.read_csv(reffname)
        for i in range(len(df.index)) :
            coverage = { 'min' : 0, 'max' : 200, 'coverage' : float(df.ix[i, 'itn'])}
            add_ITN(cb, start, [coverage], nodeIDs=[int(df.ix[i, 'node'])])
    return fn
