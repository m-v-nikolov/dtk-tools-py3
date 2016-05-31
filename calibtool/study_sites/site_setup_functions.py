from dtk.malaria.immunity import add_immune_overlays
from dtk.vector.input_EIR_by_site import configure_site_EIR
from dtk.interventions.input_EIR import add_InputEIR
from dtk.interventions.health_seeking import add_health_seeking
from dtk.utils.reports.MalariaReport import add_summary_report,add_survey_report,add_filtered_report
from dtk.vector.species import set_larval_habitat, set_species_param
from dtk.interventions.outbreak import recurring_outbreak
from dtk.interventions.itn import add_ITN
from dtk.interventions.migrate_to import add_migration_event
from dtk.interventions.malaria_drug_campaigns import add_drug_campaign
import pandas as pd
import json
import numpy as np

def config_setup_fn(duration=21915):
    return lambda cb: cb.update_params({'Simulation_Duration' : duration,
                                        'Infection_Updates_Per_Timestep' : 8})

# reporters
def summary_report_fn(start=1,interval=365,nreports=2000,age_bins=[1000],description='Annual_Report', nodes={"class": "NodeSetAll"}):
    return lambda cb: add_summary_report(cb, start=start, interval=interval, nreports=nreports, description=description,age_bins=age_bins, nodes=nodes)

def survey_report_fn(days,interval=10000,nreports=1):
    return lambda cb: add_survey_report(cb,survey_days=days,reporting_interval=interval,nreports=nreports)

def filtered_report_fn(start, end, nodes, description=''):
    return lambda cb: add_filtered_report(cb, start=start, end=end, nodes=nodes, description=description)

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
def input_eir_fn(monthlyEIRs, start_day=0, nodes={"class": "NodeSetAll"}):
    return lambda cb: add_InputEIR(cb,monthlyEIRs, start_day=start_day, nodes=nodes)

# importation pressure
def add_outbreak_fn(start_day=0, outbreak_fraction=0.01, repetitions=-1, tsteps_btwn=365, nodes={"class": "NodeSetAll"}) :
    return lambda cb: recurring_outbreak(cb, outbreak_fraction=outbreak_fraction, repetitions=repetitions, tsteps_btwn=tsteps_btwn, start_day=start_day, nodes=nodes)

# health-seeking
def add_treatment_fn(start=0,drug=['Artemether', 'Lumefantrine'],targets=[{'trigger':'NewClinicalCase','coverage':0.8,'seek':0.6,'rate':0.2}]):
    def fn(cb,start=start,drug=drug,targets=targets):
        add_health_seeking(cb,start_day=start,drug=drug,targets=targets)
        cb.update_params({'PKPD_Model': 'CONCENTRATION_VERSUS_TIME'})
    return fn

# health-seeking from nodeid-coverage specified in csv
def add_HS_by_node_id_fn(reffname, start=0) :        
    def fn(cb) :
        with open(reffname) as fin :
            cov = json.loads(fin.read())
        for hscov in cov['hscov'] :
            targets = [ { 'trigger': 'NewClinicalCase', 'coverage': 1, 'agemin':15, 'agemax':200, 'seek': hscov['coverage'], 'rate': 0.3 },
                        { 'trigger': 'NewClinicalCase', 'coverage': 1, 'agemin':0, 'agemax':15, 'seek':  min([1, hscov['coverage']*1.5]), 'rate': 0.3 },
                        { 'trigger': 'NewSevereCase',   'coverage': 1, 'seek': 0.8, 'rate': 0.5 } ]
            add_health_seeking(cb, start_day = start, targets=targets, nodes={'Node_List' : hscov['nodes'], "class": "NodeSetNodeList"})
    return fn

# ITNs
def add_itn_fn(start=0, coverage=1, nodeIDs=[]) :
    def fn(cb) :
        coverage_by_age = { 'min' : 0, 'max' : 200, 'coverage' : coverage}
        add_ITN(cb, start=start, coverage_by_ages=[coverage_by_age], nodeIDs=nodeIDs)
    return fn

# ITNs from nodeid-coverage specified in csv
def add_itn_by_node_id_fn(reffname, itn_dates, itn_fracs, channel='itn2012cov') :
    def fn(cb) :
        itn_distr = zip(itn_dates, itn_fracs)
        with open(reffname) as fin :
            cov = json.loads(fin.read())
        for itncov in cov[channel] :
            if itncov['coverage'] > 0 :
                for i, (itn_date, itn_frac) in enumerate(itn_distr) :
                    c = itncov['coverage']*itn_frac
                    if i < len(itn_fracs)-1 :
                        c /= np.prod([1 - x*itncov['coverage'] for x in itn_fracs[i+1:]])
                    coverage = { 'min' : 0, 'max' : 200, 'coverage' : c}
                    add_ITN(cb, itn_date, [coverage], nodeIDs=itncov['nodes'])
    return fn



# migration
def add_migration_fn(nodeto, start_day=0, coverage=1, repetitions=1, tsteps_btwn=365, duration_of_stay=100, is_family_trip=0, target='Everyone', nodesfrom={"class": "NodeSetAll"}) :
    return lambda cb : add_migration_event(cb, nodeto, start_day=start_day, coverage=coverage, repetitions=repetitions, 
                                           tsteps_btwn=tsteps_btwn, duration_of_stay=duration_of_stay, 
                                           is_family_trip=is_family_trip, target=target, nodesfrom=nodesfrom)

# drug campaign
def add_drug_campaign_fn(drug_code, start_days, coverage=1.0, repetitions=3, interval=60, diagnostic_threshold=40, 
                         snowballs=0, delay=0, nodes={"class": "NodeSetAll"}, target_group='Everyone') :
    return lambda cb : add_drug_campaign(cb, drug_code, start_days=start_days, coverage=coverage, 
                                         repetitions=repetitions, interval=interval, diagnostic_threshold=diagnostic_threshold, 
                                         snowballs=snowballs, delay=delay, nodes=nodes, target_group=target_group)