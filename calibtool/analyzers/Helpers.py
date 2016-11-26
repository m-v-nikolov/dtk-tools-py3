import pandas as pd
import numpy as np
import itertools
import calendar

def json_to_pandas(simdata,bins,channel):
    '''
    A function to convert simulation data from a json file to
    a Pandas dataframe
    '''
    bin_tuples = list(itertools.product(*bins.values()))
    multi_index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())

    channel_series = pd.Series(np.array(simdata).flatten(), index=multi_index, name=channel)

    return channel_series


def ref_json_to_pandas(refdata, required_reference_types, bins, channel):
    '''
    A function to convert reference data from the site_*.py
    to a Pandas dataframe
    '''
    if 'by_age_and_season' in required_reference_types:
        Para = [[] for i in range(2)]
        for season in refdata['Seasons']:
            for Paratype in refdata['Seasons'][season].keys():
                if 'Gametocytemia' in Paratype:
                    Para[1].append(refdata['Seasons'][season][Paratype])
                elif 'Parasitemia' in Paratype:
                    Para[0].append(refdata['Seasons'][season][Paratype])
        bin_tuples = list(itertools.product(*bins.values()))
        multi_index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())
        ref_channel_series = pd.Series(np.array(Para).flatten(), index=multi_index,name=channel)

    return ref_channel_series

def reorder_sim_data(channel_series,ref_channel_series,months,channel,population):
    '''
    A function to reorder sim data to match reference data
    '''
    # Data frames
    df_pop = population.reset_index()
    df_sim = channel_series.reset_index()
    df_ref = ref_channel_series.reset_index()

    # Age bins
    age_bins = list(set(df_ref['Age Bins']))
    age_bins.append(0)
    age_bins.sort()

    # Seasons
    months_of_year = dict((v,k) for k,v in enumerate(calendar.month_name))
    seasonIndex = []
    for i in range(len(months)):
        seasonIndex.extend([t for t in range(months_of_year[months[i]] - 1, df_sim.Time[-1:] + 1, 12)])
    seasons = list(set(df_ref['Seasons']))
    season_month = dict(zip(months,seasons))

    # Reorder simulation data to match reference data
    df_sim = df_sim[df_sim.Time.isin(seasonIndex)]      # Only retain months corresponding to seasons in ref data
    pop = pd.merge(df_sim, df_pop, left_on=['Time', 'Age Bins'], right_on=['Time', 'Age Bins']) # Find population by age bin and pull out relevant rows
    df_sim['PfPR by Parasitemia and Age Bin'] = pop['PfPR by Parasitemia and Age Bin'].multiply(pop['Population by Age Bin']).values
    df_sim['Age Bins'] = pd.cut((df_sim['Time'] + 1) / 12, age_bins)  # Reorder Age Bins
    df_sim['Time'] = [season_month[calendar.month_name[i]] for i in (df_sim['Time']%12+1)]  # Label Season
    df_sim['PfPR Type'] = [s for s in channel.split() if "temia" in s]*len(df_sim)
    df_sim = df_sim.rename(index=str, columns={"Time": "Seasons"})
    df_sim = df_sim[list(df_ref.columns.values)] # Reorder simulation data frame to match reference data frame

    return df_sim





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
            if sim_agebins[i] > age :
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
#
# def accumulate_ageseasonbins_cohort(simdata, average_pop, raw_agebins, seasons) :
#     '''
#     A function to sum over each year's values in a summary report,
#     combining incidence rate and average population
#     to give total counts and population in the reference age binning.
#     '''
#     simdata = np.asarray(simdata)
#     average_pop = np.asarray(average_pop)
#
#     num_years = int(simdata.shape[0]/12)
#     binsCytes = simdata.shape[1]
#
#     glommed_data = np.zeros((len(seasons),len(raw_agebins),binsCytes))
#     num_in_bin = np.zeros((len(seasons),len(raw_agebins)))
#     seasonindex = np.full([len(seasons),num_years],np.nan)        # Stores indices from the 'data' list that correspond to each of the seasons
#     simageindex = np.full([len(seasons),num_years],np.nan)  # Stores age bin index for each month in the 'data' file
#
#
#     for i in range(len(seasons)):
#         seasonindex[i,:] = np.arange(seasons[i]-1,12 * num_years,12)
#         simageindex[i, :] = np.arange(seasons[i] - 1, 12 * num_years, 12)
#         for j in range(num_years):
#             for k, age in enumerate(raw_agebins):
#                 if simageindex[i,j]/12<age:
#                     simageindex[i, j] = k
#                     break
#
#
#     for i in range(len(seasons)):
#         for k in range(binsCytes):
#             for j in range(num_years):
#                 glommed_data[i,simageindex[i,j],k] += simdata[seasonindex[i,j],k,0]#*average_pop[seasonindex[i,j]]
#                 num_in_bin[i,simageindex[i,j]] += average_pop[seasonindex[i,j]]
#
#     return num_in_bin, glommed_data
#
def get_spatial_report_data_at_date(sp_data, date) :

    return pd.DataFrame( { 'node' : sp_data['nodeids'],
                           'data' : sp_data['data'][date] } )

def get_risk_by_distance(df_sim, distances, ddf) :

    nodelist = df_sim['node'].values.tolist()
    rel_risk = []
    for k, n_dist in enumerate(distances) :
        pos_w_pos = 0.
        tot_w_pos = 0.
        for hh_num in df_sim.index :
            if df_sim.ix[hh_num, 'pos'] < 1 :
                continue

            if n_dist == 0 and df_sim.ix[hh_num, 'pop'] > 1 :
                hh_pos = df_sim.ix[hh_num, 'pos']
                hh_tot = df_sim.ix[hh_num, 'pop']
                num_pos = (hh_pos - 1)*hh_pos
                num_ppl = (hh_tot - 1)*hh_pos

            else :
                # node IDs of nodes within distance
                neighbors = ddf[(ddf['node1'] == nodelist[hh_num]) & (ddf['node2'] != nodelist[hh_num]) &
                                (ddf['dist'] <= n_dist) & (ddf['dist'] > distances[k-1])]['node2'].values

                ndf = df_sim[df_sim['node'].isin(neighbors)]
                num_pos = sum(ndf['pos'].values)
                num_ppl = sum(ndf['pop'].values)

            pos_w_pos += num_pos
            tot_w_pos += num_ppl
        if tot_w_pos > 0 :
            rel_risk.append(pos_w_pos/tot_w_pos)
        else :
            rel_risk.append(0)
    return rel_risk