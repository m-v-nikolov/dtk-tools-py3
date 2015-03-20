from collections import deque
from dtk.interventions.input_EIR import add_InputEIR
from dtk.interventions.health_seeking import add_health_seeking
from dtk.interventions.malaria_drug_campaign_cff import drug_params

# Dictionary of supported study-site configuration functions keyed on site name
study_site_monthly_EIRs = { 
    "Namawala": [43.8, 68.5, 27.4, 46.6, 49.4, 24.7, 13.7, 11, 11, 2.74, 13.7, 16.5] ,                    # EIR = 329
    "Dielmo": [10.4, 13, 6, 2.6, 4, 6, 35, 21, 28, 15, 10.4, 8.4],                                        # EIR = 160
    "Sugungum": [2.3,  6.8, 12.6, 20.2, 27.7, 26.9, 21, 10.3,  2.6,  0.5,  0.5,  1.0],                    # EIR = 132
    "Matsari": [1.2, 3.5, 6.5, 10.4, 14.3, 13.9, 10.6, 5.3, 1.3, 0.26, 0.28, 0.52],                       # EIR =  68
    'Siaya': [55*m for m in [0.07, 0.08, 0.04, 0.02, 0.03, 0.04, 0.22, 0.13, 0.18, 0.09, 0.07, 0.05]],    # EIR =  56
    'Kilifi_South': [3.6, 1.4, 0.0, 2.8, 0.4, 10.3, 10.6, 3.1, 0.4, 0.0, 0.7, 0.8],                       # EIR =  34
    "Ndiop": [0.39, 0.19, 0.77, 0, 0, 0, 6.4, 2.2, 4.7, 3.9, 0.87, 0.58],                                 # EIR =  20
    "Rafin_Marke": [0.6, 1.1, 1.7, 2.6, 3.4, 3.4, 2.9, 1.9, 0.6, 0.12, 0.15, 0.31],                       # EIR =  18
    'Kilifi_North': [0.6, 0.25, 0.0, 0.45, 0.05, 1.7, 1.75, 0.5, 0.05, 0.0, 0.1, 0.15],                   # EIR =   5.6
    'Sukuta': [3*m for m in [0.07, 0.08, 0.04, 0.02, 0.03, 0.04, 0.22, 0.13, 0.18, 0.09, 0.07, 0.05]],    # EIR =   3.1
    'Bakau':  [0.12*m for m in [0.02, 0.01, 0.04, 0.00, 0.00, 0.00, 0.32, 0.11, 0.24, 0.20, 0.04, 0.03]]  # EIR =   0.12
}

fT_by_site={}

def mAb_vs_EIR(EIR):
    # Rough cut at function from eyeballing a few BinnedReport outputs parsed into antibody fractions
    mAb = 0.9 * (1e-4*EIR*EIR + 0.7*EIR) / ( 0.7*EIR + 2 )
    return min(mAb, 1.0)

# Configuration of study-site input EIR
def configure_site_EIR(cb, site, habitat, circular_shift=0, fT=0):

    if site not in study_site_monthly_EIRs.keys():
        raise Exception("Don't know how to configure site: %s " % site)

    if site in fT_by_site.keys():
        fT=fT_by_site[site]
    else:
        fT=float(fT)
    #print('Using treatment fraction of %0.2f for site %s.'%(fT,site))

    # Calibration is done with CONSTANT_INITIAL_IMMUNITY on birth cohort
    # but with a downscaling to account for maternal immunity levels
    # Here, we'll keep the CONSTANT model and downscale as a function of annual EIR
    annual_EIR = sum(study_site_monthly_EIRs[site])
    mAb = cb.get_param('Maternal_Antibody_Protection') * mAb_vs_EIR(annual_EIR)

    # No births/deaths.  Just following a birth cohort.
    cb.update_params({ 'Config_Name': site, 
                       'Enable_Vital_Dynamics': 0,
                       'Demographics_Filename': 'birth_cohort_demographics.compiled.json',
                       'Vector_Species_Names': [],
                       'Climate_Model': 'CLIMATE_CONSTANT',
                       'Maternal_Antibodies_Type': 'CONSTANT_INITIAL_IMMUNITY',
                       'Maternal_Antibody_Protection': mAb
                       })

    # Shift order of months according to circular_shift argument
    EIR_deque = deque([habitat * m for m in study_site_monthly_EIRs[site]])
    EIR_deque.rotate(circular_shift)
    monthlyEIRs=list(EIR_deque)
    add_InputEIR(cb, monthlyEIRs=monthlyEIRs)

    # Add treatment of some fraction of clinical episodes
    if fT > 0:
        drugs=['Artemether','Lumefantrine']
        for drug in drugs:
            cb.config["parameters"]["Malaria_Drug_Params"][drug] = drug_params[drug]
        add_health_seeking(cb, start_day = 0,
                           targets = [ { 'trigger': 'NewClinicalCase', 
                                         'coverage': 1, 
                                         'seek': fT,
                                         'rate': 0 } ],
                           drug    = drugs,
                           dosing  = 'FullTreatmentCourse')

    return {'monthlyEIRs':monthlyEIRs,'fT':fT}