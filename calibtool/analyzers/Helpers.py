import pandas as pd

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

def get_spatial_report_data_at_date(sp_data, date) :

    return pd.DataFrame( { 'node' : sp_data['nodeids'],
                           'data' : sp_data['data'][date] } )

def get_risk_by_distance(df, distances, ddf) :

    nodelist = df['node'].values.tolist()
    rel_risk = []
    for k, n_dist in enumerate(distances) :
        pos_w_pos = 0.
        tot_w_pos = 0.
        for hh_num in df.index :
            if df.loc[hh_num, 'pos'] < 1 :
                continue
            
            if n_dist == 0 and df.loc[hh_num, 'pop'] > 1 :
                hh_pos = df.loc[hh_num, 'pos']
                hh_tot = df.loc[hh_num, 'pop']
                num_pos = (hh_pos - 1)*hh_pos
                num_ppl = (hh_tot - 1)*hh_pos

            else :
                # node IDs of nodes within distance
                neighbors = ddf[(ddf['node1'] == nodelist[hh_num]) & (ddf['node2'] != nodelist[hh_num]) &
                                (ddf['dist'] <= n_dist) & (ddf['dist'] > distances[k-1])]['node2'].values

                ndf = df[df['node'].isin(neighbors)]
                num_pos = sum(ndf['pos'].values)
                num_ppl = sum(ndf['pop'].values)

            pos_w_pos += num_pos
            tot_w_pos += num_ppl
        if tot_w_pos > 0 :
            rel_risk.append(pos_w_pos/tot_w_pos)
        else :
            rel_risk.append(0)
    return rel_risk