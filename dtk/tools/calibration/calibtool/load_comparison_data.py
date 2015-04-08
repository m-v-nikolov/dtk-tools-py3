import numpy as np

datastruct = { 
    'Dapelogo' : {
        'density_by_age_and_season' : {
            'parasitemia_bins' : [0, 50, 500, 5000, 50000, 500000],
            'age_bins' : [5, 15, 100],
            'start_wet' : {
                'PfPR by Parasitemia and Age Bin' : np.array([[1, 0, 0, 2, 2, 3], [2, 1, 0, 2, 0, 4], [9, 5, 4, 4, 2, 3]]), # 18S data - 25S data
                #'PfPR by Parasitemia and Age Bin' : np.array([[0, 0, 1, 2, 2, 4], [0, 0, 3, 2, 0, 6], [6, 7, 5, 4, 2, 3]]), # straight 18S data
                'PfPR by Gametocytemia and Age Bin' : np.array([[0, 1, 4, 2, 2, 0], [0, 1, 4, 6, 0, 0], [12, 8, 3, 4, 0, 0]])
            },
            'peak_wet' : {
                'PfPR by Parasitemia and Age Bin' : np.array([[1, 2, 0, 1, 3, 1], [2, 5, 2, 3, 1, 1], [6, 8, 4, 4, 0, 2]]), # 18S data - 25S data
                #'PfPR by Parasitemia and Age Bin' : np.array([[0, 3, 0, 1, 3, 1], [0, 5, 4, 2, 2, 1], [2, 12, 4, 4, 0, 3]]), # straight 18S data
                'PfPR by Gametocytemia and Age Bin' : np.array([[1, 3, 2, 2, 0, 0], [0, 8, 0, 3, 0, 0], [11, 10, 2, 2, 0, 0]])
            },
            'end_wet' : {
                'PfPR by Parasitemia and Age Bin' : np.array([[1, 1, 0, 4, 3, 1], [4, 1, 2, 4, 2, 1], [6, 9, 6, 2, 2, 0]]), # 18S data - 25S data
                #'PfPR by Parasitemia and Age Bin' : np.array([[0, 2, 0, 4, 3, 1], [0, 4, 2, 4, 3, 1], [3, 12, 6, 2, 2, 0]]), # straight 18S data
                'PfPR by Gametocytemia and Age Bin' : np.array([[2, 3, 2, 2, 1, 0], [2, 5, 4, 2, 1, 0], [14, 7, 4, 0, 0, 0]])
            }
        },
        'infectiousness_by_age_and_season' : {
            'fraction_infected_bins' : [0, 5, 20, 50, 80, 100],
            'age_bins' : [5, 15, 100],
            'start_wet' : {
                'infectiousness' : np.array([[2, 2, 0, 4, 1, 0], [1, 3, 5, 1, 1, 0], [18, 9, 0, 0, 0, 0]])
            },
            'peak_wet' : {
                'infectiousness' : np.array([[3, 1, 2, 2, 0, 0], [9, 0, 2, 0, 3, 0], [20, 1, 2, 1, 1, 0]])
            },
            'end_wet' : {
                'infectiousness' : np.array([[5, 0, 1, 3, 0, 0], [10, 1, 2, 1, 0, 0], [23, 2, 0, 0, 0, 0]])
            }
        },
        'density_and_infectiousness_by_age_and_season' : {
            'parasitemia_bins' : [0, 0.5, 5, 50, 500, 5000, 50000, 500000],
            'age_bins' : [5, 15, 100],
            'start_wet' : { # innermost array: infectiousness at constant gametocytemia; next inner array: gametocytemias; outer array: age group
                'Gametocytemia and Infectiousness' : np.array([[ [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [1, 1, 0, 2, 0, 0], [0, 1, 0, 1, 0, 0], [0, 0, 0, 1, 1, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 2, 1, 0, 1, 0], [1, 1, 3, 1, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [7, 5, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0], [2, 0, 0, 0, 0, 0], [2, 1, 0, 0, 0, 0], [2, 1, 0, 0, 0, 0], [2, 2, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ]])
            },
            'peak_wet' : {
                'Gametocytemia and Infectiousness' : np.array([[ [0, 0, 1, 0, 0, 0], [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0], [1, 0, 1, 0, 0, 0], [0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [4, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0], [2, 0, 0, 0, 0, 0], [0, 0, 1, 0, 2, 1], [0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 1, 1], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [13, 1, 0, 0, 0, 0], [4, 0, 1, 0, 0, 0], [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0], [1, 0, 1, 0, 0, 0], [1, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ]])
            },
            'end_wet' : {
                'Gametocytemia and Infectiousness' : np.array([[ [2, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [1, 0, 0, 1, 0, 0], [1, 0, 0, 1, 0, 0], [0, 0, 0, 1, 0, 1], [0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [2, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [1, 0, 0, 1, 0, 0], [3, 0, 0, 0, 0, 0], [2, 0, 2, 0, 0, 0], [1, 1, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [13, 1, 0, 0, 0, 0], [2, 0, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0], [4, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ]])
            }
        }
    },
    'Laye' : {
        'density_by_age_and_season' : {
            'parasitemia_bins' : [0, 50, 500, 5000, 50000, 500000],
            'age_bins' : [5, 15, 100],
            'start_wet' : {
                'PfPR by Parasitemia and Age Bin' : np.array([[2, 0, 0, 0, 1, 1], [4, 1, 2, 3, 2, 6], [7, 9, 4, 2, 4, 1]]), # 18S data - 25S data
                #'PfPR by Parasitemia and Age Bin' : np.array([[0, 1, 1, 0, 1, 2], [1, 4, 2, 3, 2, 9], [4, 11, 5, 2, 4, 1]]), # straight 18S data
                'PfPR by Gametocytemia and Age Bin' : np.array([[0, 0, 0, 5, 0, 0], [3, 9, 8, 1, 0, 0], [16, 4, 6, 1, 0, 0]])
            },
            'peak_wet' : {
                'PfPR by Parasitemia and Age Bin' : np.array([[0, 1, 0, 1, 1, 0], [13, 1, 0, 3, 0, 1], [9, 12, 3, 0, 1, 0]]), # 18S data - 25S data
                #'PfPR by Parasitemia and Age Bin' : np.array([[0, 1, 0, 1, 1, 0], [1, 7, 6, 3, 0, 2], [0, 21, 3, 0, 1, 0]]), # straight 18S data
                'PfPR by Gametocytemia and Age Bin' : np.array([[1, 0, 1, 1, 0, 0], [2, 4, 8, 4, 1, 0], [7, 10, 5, 3, 0, 0]])
            },
            'end_wet' : {
                'PfPR by Parasitemia and Age Bin' : np.array([[1, 0, 0, 0, 1, 0], [8, 1, 1, 6, 3, 1], [10, 11, 4, 2, 0, 0]]), # 18S data - 25S data
                #'PfPR by Parasitemia and Age Bin' : np.array([[1, 0, 0, 0, 1, 0], [5, 4, 1, 6, 3, 1], [5, 16, 4, 2, 0, 0]]), # straight 18S data
                'PfPR by Gametocytemia and Age Bin' : np.array([[1, 0, 0, 1, 0, 0], [7, 9, 3, 1, 0, 0], [14, 10, 3, 0, 0, 0]])
            }
        },
        'infectiousness_by_age_and_season' : {
            'fraction_infected_bins' : [0, 5, 20, 50, 80, 100],
            'age_bins' : [5, 15, 100],
            'start_wet' : {
                'infectiousness' : np.array([[1, 0, 2, 0, 1, 0], [7, 5, 4, 4, 1, 0], [22, 2, 1, 1, 0, 0]])
            },
            'peak_wet' : {
                'infectiousness' : np.array([[2, 0, 1, 0, 0, 0], [12, 1, 1, 3, 2, 0], [20, 2, 2, 0, 1, 0]])
            },
            'end_wet' : {
                'infectiousness' : np.array([[1, 0, 0, 1, 0, 0], [17, 2, 1, 0, 0, 0], [26, 1, 0, 0, 0, 0]])
            }
        },
        'density_and_infectiousness_by_age_and_season' : {
            'parasitemia_bins' : [0, 0.5, 5, 50, 500, 5000, 50000, 500000],
            'fraction_infected_bins' : [0, 5, 20, 50, 80, 100],
            'age_bins' : [5, 15, 100],
            'start_wet' : { # innermost array: infectiousness at constant gametocytemia; next inner array: gametocytemias; outer array: age group
                'Gametocytemia and Infectiousness' : np.array([[ [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [1, 0, 2, 0, 1, 1], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ], 
                                                               [ [1, 2, 0, 0, 0, 0], [1, 0, 1, 1, 0, 0], [1, 2, 0, 0, 0, 0], [1, 1, 0, 0, 1, 0], [3, 0, 2, 3, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [15, 1, 0, 0, 0, 0], [1, 1, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [2, 0, 0, 0, 0, 0], [3, 0, 0, 1, 0, 1], [0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ]])
            },
            'peak_wet' : {
                'Gametocytemia and Infectiousness' : np.array([[ [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [2, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [4, 0, 0, 0, 0, 0], [4, 0, 1, 2, 1, 0], [1, 1, 0, 1, 1, 0], [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [7, 0, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0], [1, 0, 1, 0, 0, 0], [4, 0, 1, 0, 0, 0], [4, 1, 0, 0, 0, 0], [1, 1, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ]])
            },
            'end_wet' : {
                'Gametocytemia and Infectiousness' : np.array([[ [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [7, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [3, 1, 1, 0, 0, 0], [3, 0, 0, 0, 0, 0], [2, 1, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ],
                                                               [ [13, 0, 0, 0, 0, 0], [3, 0, 0, 0, 0, 0], [2, 0, 0, 0, 0, 0], [6, 0, 0, 0, 0, 0], [2, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0] ]])
            }
        }
    },
    'Dielmo' : {
        'annual_clinical_incidence_by_age' : {
            'n_obs' : [55, 60, 55, 50, 50, 38, 38, 38, 38, 38, 26, 26, 26, 26, 26, 110, 75, 75, 150, 70, 70, 90],
            'age_bins' : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100],
            'Annual Clinical Incidence by Age Bin' : [3.2, 5, 6.1, 4.75, 3.1, 2.75, 2.7, 1.9, 0.12, 0.8, 0.5, 0.25, 0.1, 0.2, 0.4, 0.3, 0.2, 0.2, 0.2, 0.15, 0.15, 0.15]
        }
    },
    'Ndiop' : {
        'annual_clinical_incidence_by_age' : {
            'n_obs' : [31, 34, 31, 28, 28, 21, 21, 21, 21, 21, 15, 15, 15, 15, 15, 62, 42, 42, 84, 39, 39, 50],
            'age_bins' : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100],
            'Annual Clinical Incidence by Age Bin' : [1.9, 2.2, 2.6, 2.8, 2.9, 3.0, 2.8, 2.7, 2.6, 2.6, 2.5, 2.2, 2.1, 1.8, 1.5, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.4]
        }
    },
    'Namawala' : {
        'prevalence_by_age' : {
            'n_obs' : [150, 150, 626, 1252, 626, 2142, 1074, 1074, 605, 605, 489],
            'age_bins' : [0.5, 1, 2, 4, 5, 10, 15, 20, 30, 40, 50],
            'PfPR by Age Bin' : [0.55, 0.85, 0.9, 0.88, 0.85, 0.82, 0.75, 0.65, 0.45, 0.42, 0.4]
        }
    },
    'Sugungum' : {
        'prevalence_by_age' : {
            'n_obs' : [79, 79, 114, 229, 114, 669, 314, 324, 733, 829, 582, 418],
            'age_bins' : [0.5, 1, 2, 4, 5, 10, 15, 20, 30, 40, 50, 60],
            'PfPR by Age Bin' : [0.3, 0.68, 0.75, 0.82, 0.88, 0.76, 0.6, 0.42, 0.27, 0.22, 0.25, 0.32]
        }
    },
    'Matsari' : {
        'prevalence_by_age' : {
            'n_obs' : [52, 52, 76, 151, 76, 441, 207, 214, 484, 547, 384, 276],
            'age_bins' : [0.5, 1, 2, 4, 5, 10, 15, 20, 30, 40, 50, 60],
            'PfPR by Age Bin' : [0.2, 0.68, 0.7, 0.85, 0.8, 0.8, 0.78, 0.55, 0.35, 0.3, 0.25, 0.3]
        }
    },
    'Rafin_Marke' : {
        'prevalence_by_age' : {
            'n_obs' : [45, 45,  66, 132,  66, 386, 182, 187, 424, 479, 336, 241],
            'age_bins' : [0.5, 1, 2, 4, 5, 10, 15, 20, 30, 40, 50, 60],
            'PfPR by Age Bin' : [0.44, 0.5, 0.55, 0.8, 0.85, 0.83, 0.68, 0.55, 0.35, 0.25, 0.2, 0.15]
        }
    },
    'Malariatherapy' : {
        'density_timecourse' : {
            'n_obs_densities' : 131,
            'parasitemia_bins' : [10, 100, 1000, 10000, 100000, 1e9],
            'peak_parasitemias' : [0, 0, 1, 14, 94, 22],
            'peak_gametocytemias' : [10, 22, 50, 45, 4, 0],
            'n_obs_durations' : 118,
            'infection_duration_bins' : [20, 50, 100, 150, 200, 300, 1000],
            'parasitemia_durations' : [4, 16, 33, 27, 14, 17, 7],
            'gametocytemia_durations' : [14, 36, 28, 15, 9, 14, 2]
        }
    }
}

def load_comparison_data(site, datatype) :

    return datastruct[site][datatype]
