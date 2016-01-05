from collections import deque
from dtk.generic.geography import set_geography
from dtk.interventions.input_EIR import add_InputEIR

# Study-site EIR by month of year
study_site_monthly_EIRs = { 
    'Dapelogo':     [1, 1, 1, 1, 1, 3, 27, 70, 130, 57, 29, 1],                                                 # EIR = 322
    "Namawala":     [43.8, 68.5, 27.4, 46.6, 49.4, 24.7, 13.7, 11, 11, 2.74, 13.7, 16.5] ,                      # EIR = 329
    "Dielmo":       [10.4, 13, 6, 2.6, 4, 6, 35, 21, 28, 15, 10.4, 8.4],                                        # EIR = 160
    "Sugungum":     [2.27,  6.83, 12.60, 20.23, 27.66, 26.89, 20.60, 10.31,  2.56,  0.50,  0.54,  1.01],        # EIR = 132
    "Matsari":      [1.17, 3.52, 6.49, 10.42, 14.25, 13.85, 10.61, 5.31, 1.32, 0.26, 0.28, 0.52],               # EIR =  68
    'Siaya':        [55*m for m in [0.07, 0.08, 0.04, 0.02, 0.03, 0.04, 0.22, 0.13, 0.18, 0.09, 0.07, 0.05]],   # EIR =  56
    'Laye':         [1, 1, 1, 1, 1, 7, 8, 9, 5, 4, 6, 1],                                                       # EIR =  45
    'Kilifi_South': [3.6, 1.4, 0.0, 2.8, 0.4, 10.3, 10.6, 3.1, 0.4, 0.0, 0.7, 0.8],                             # EIR =  34
    "Ndiop":        [0.39, 0.19, 0.77, 0, 0, 0, 6.4, 2.2, 4.7, 3.9, 0.87, 0.58],                                # EIR =  20
    "Rafin_Marke":  [0.59, 1.11, 1.71, 2.55, 3.41, 3.37, 2.87, 1.95, 0.56, 0.12, 0.15, 0.31],                   # EIR =  18
    'Kilifi_North': [0.6, 0.25, 0.0, 0.45, 0.05, 1.7, 1.75, 0.5, 0.05, 0.0, 0.1, 0.15],                         # EIR =   5.6
    'Sukuta':       [3*m for m in [0.07, 0.08, 0.04, 0.02, 0.03, 0.04, 0.22, 0.13, 0.18, 0.09, 0.07, 0.05]],    # EIR =   3.1
    'Bakau':        [0.12*m for m in [0.02, 0.01, 0.04, 0.00, 0.00, 0.00, 0.32, 0.11, 0.24, 0.20, 0.04, 0.03]]  # EIR =   0.12
}

def mAb_vs_EIR(EIR):
    # Rough cut at function from eyeballing a few BinnedReport outputs parsed into antibody fractions
    mAb = 0.9 * (1e-4*EIR*EIR + 0.7*EIR) / ( 0.7*EIR + 2 )
    return min(mAb, 1.0)

# Configuration of study-site input EIR
def configure_site_EIR(cb, site, habitat=1, circular_shift=0, birth_cohort=True, set_site_geography=True):

    if site not in study_site_monthly_EIRs.keys():
        raise Exception("Don't know how to configure site: %s " % site)

    EIRs = [habitat * m for m in study_site_monthly_EIRs[site]]

    # Calibration is done with CONSTANT_INITIAL_IMMUNITY on birth cohort
    # but with a downscaling to account for maternal immunity levels
    # Here, we'll keep the CONSTANT model and downscale as a function of annual EIR
    annual_EIR = sum(EIRs)
    mAb = cb.get_param('Maternal_Antibody_Protection') * mAb_vs_EIR(annual_EIR)

    if birth_cohort:
        set_geography(cb, "Birth_Cohort")
    elif set_site_geography :
        set_geography(cb,site)
    cb.update_params({ 'Config_Name': site, 
                       'Vector_Species_Names': [], # no mosquitoes
                       'Maternal_Antibodies_Type': 'CONSTANT_INITIAL_IMMUNITY',
                       'Maternal_Antibody_Protection': mAb
                       })

    # Shift order of months according to circular_shift argument
    EIR_deque = deque(EIRs)
    EIR_deque.rotate(circular_shift)
    monthlyEIRs=list(EIR_deque)
    add_InputEIR(cb, monthlyEIRs=monthlyEIRs)

    return {'monthlyEIRs':monthlyEIRs}