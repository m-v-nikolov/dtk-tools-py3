#       this is copied wholesale from dtk.calibration.analyzers.analyze_clinical_incidence_by_age_cohort
def accumulate_agebins_cohort(simdata, average_pop, sim_agebins, raw_agebins) :
    '''
    A function to sum over each year's values in a summary report,
    combining incidence rate and average population
    to give total counts and population in the reference age binning.
    '''

    glommed_data = [0]*len(raw_agebins)
    simageindex = [-1]*len(sim_agebins)
    yearageindex = [-1]*len(simdata)
    num_in_bin = [0]*len(raw_agebins)

    for i in range(len(simageindex)) :
        for j, age in enumerate(raw_agebins) :
            if sim_agebins[i] < age :
                simageindex[i] = j
                break
    for i in range(len(yearageindex)) :
        for j, age in enumerate(raw_agebins) :
            if i < age :
                yearageindex[i] = j
                break

    for i in range(len(yearageindex)) :
        if yearageindex[i] < 0 :
            continue
        for j in range(len(simageindex)) :
            if simageindex[j] < 0 :
                continue
            glommed_data[simageindex[j]] += simdata[i][j]*average_pop[i][j]
            num_in_bin[simageindex[j]] += average_pop[i][j]

    return num_in_bin, glommed_data