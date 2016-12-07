import itertools
from datetime import date
import calendar
import logging
from collections import OrderedDict

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def summary_channel_to_pandas(data, channel):
    """
    A function to return a hierarchical binned pandas.Series for a specified MalariaSummaryReport.json channel
    :param simdata: parsed data from summary report
    :param channel: channel in summary report
    :return: pd.Series with MultiIndex binning taken from summary metadata
    """

    grouping = get_grouping_for_summary_channel(data, channel)
    bins = get_bins_for_summary_grouping(data, grouping)

    return json_to_pandas(data[grouping][channel], bins, channel)


def json_to_pandas(data, bins, channel=None):
    """
    A function to convert nested array channel data from a json file to
    a pandas.Series with the specified MultiIndex binning.
    """

    logger.debug("Converting JSON data from '%s' channel to pandas.Series with %s MultiIndex.", channel, bins.keys())
    bin_tuples = list(itertools.product(*bins.values()))
    multi_index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())

    channel_series = pd.Series(np.array(data).flatten(), index=multi_index, name=channel)

    return channel_series


def get_grouping_for_summary_channel(data, channel):
    """
    A function to find the grouping to which a channel belongs in MalariaSummaryReport.json
    :param data: parsed data from summary report
    :param channel: channel to find
    :return: grouping or exception if not found

    Example:

    >>> get_grouping_for_summary_channel(data, channel='Average Population by Age Bin')
    'DataByTimeAndAgeBins'
    """

    for group, group_data in data.items():
        if channel in group_data.keys():
            return group

    raise Exception('Unable to find channel %s in groupings %s' % (channel, data.keys()))


def get_bins_for_summary_grouping(data, grouping):
    """
    A function to get the dimensions and binning of data for a specified MalariaSummaryReport.json grouping
    :param data: parsed data from summary report
    :param grouping: group name
    :return: an OrderedDict of dimensions and bins

    Example:

    >>> get_bins_for_summary_grouping(data, grouping='DataByTimeAndAgeBins')
    OrderedDict([('Time', [31, 61, 92, ..., 1095]), ('Age Bins', [0, 10, 20, ..., 1000])])
    """

    metadata = data['Metadata']
    time = data['DataByTime']['Time Of Report']

    if grouping == 'DataByTime':
        return OrderedDict([
            ('Time', time)
        ])
    elif grouping == 'DataByTimeAndAgeBins':
        return OrderedDict([
            ('Time', time),
            ('Age Bins', metadata['Age Bins'])
        ])
    elif grouping == 'DataByTimeAndPfPRBinsAndAgeBins':
        return OrderedDict([
            ('Time', time),
            ('PfPR bins', metadata['Parasitemia Bins']),
            ('Age Bins', metadata['Age Bins'])
        ])

    raise Exception('Unable to find grouping %s in %s' % (grouping, data.keys()))


def season_channel_age_density_json_to_pandas(reference, bins):
    """
    A helper function to convert reference data from its form in e.g. site_Laye.py:

    "Seasons": {
        "start_wet": {
            "PfPR by Parasitemia and Age Bin": [
                [2, 0, 0, 0, 1, 1], [4, 1, 2, 3, 2, 6], [7, 9, 4, 2, 4, 1]],
            "PfPR by Gametocytemia and Age Bin": [
                [0, 0, 0, 5, 0, 0], [3, 9, 8, 1, 0, 0], [16, 4, 6, 1, 0, 0]]
        },
        ...
    }

    To a pd.Series with MultiIndex:

    PfPR Type                          Seasons    Age Bins  PfPR bins
    PfPR by Gametocytemia and Age Bin  start_wet  5         0             0
                                                            50            0
                                                            500           0
                                                            5000          5
                                                            50000         0
                                                            500000        0
    """

    season_dict = {}
    for season, season_data in reference.items():
        channel_dict = {}
        for channel, channel_data in season_data.items():
            channel_dict[channel] = json_to_pandas(channel_data, bins)
        season_dict[season] = pd.DataFrame(channel_dict)

    # Concatenate the multi-channel (i.e. parasitemia, gametocytemia) dataframes by season
    df = pd.concat(season_dict.values(), axis=1, keys=season_dict.keys(), names=['Seasons', 'PfPR Type'])

    # Stack the hierarchical columns into the MultiIndex
    channel_series = df.stack(['Seasons', 'PfPR Type'])\
                       .reorder_levels(['PfPR Type', 'Seasons', 'Age Bins', 'PfPR bins'])\
                       .sort_index()

    logger.debug('\n%s', channel_series)

    return channel_series


def convert_to_counts(rates, pops):
    """
    Convert population-normalized rates to counts
    :param rates: a pandas.Series of normalized rates
    :param pops: a pandas.Series of average population counts
    :return: a pandas.Series (same binning as rates)
    """

    rate_idx = rates.index.names
    pop_idx = pops.index.names

    # Join rates to population counts on the binning of the latter
    df = rates.reset_index().set_index(pop_idx)\
              .join(pops, how='left')\
              .reset_index().set_index(rate_idx)

    # Multiply rates by population and return counts
    counts = (df[rates.name] * df[pops.name]).rename(rates.name)
    return counts


def rebin_age_from_birth_cohort(counts, age_bins):
    """
    Reinterpret 'Time' as 'Age' for a birth cohort and re-bin counts in specified bins
    :param counts: a pandas.Series of counts with MultiIndex containing level 'Time' in days
    :param age_bins: a list of ages in years to cut into categorical bins
    :return: a pandas.Series of counts summed into the reinterpreted age bins
    """

    df = counts.reset_index()

    # Time in days but Age in years
    df['Age'] = df['Time'] / 365.0

    # Assign each Age to a range in specified age_bins (left inclusive)
    df['Age Bins'] = pd.cut(df.Age, age_bins, include_lowest=True)

    # Sum counts for time points sharing an age bin and return Series
    rebinned_series = df.groupby(counts.index.names).sum()[counts.name]
    return rebinned_series


def rebin_by_month(counts, months):
    """
    Re-bin counts replacing 'Time' with specified month bins
    :param counts: a pandas.Series of counts with MultiIndex containing level 'Time' in days
    :param months: a list of month names
    :return: a pandas.Series of counts summed into month bins
    """

    df = counts.reset_index()

    # Day of Year from Time (in days)
    df['Day of Year'] = 1 + df['Time'] % 365

    # Assign each Day of Year to a named Month
    df['Month'] = df['Day of Year'].apply(lambda x: calendar.month_name[date.fromordinal(x).month])

    # Sum counts for time points sharing a month and return Series
    idx_names = list(counts.index.names)  # copy FrozenList to mutable
    idx_names[idx_names.index('Time')] = 'Month'  # replace Time with Month in new MultiIndex
    rebinned_series = df.groupby(idx_names).sum()[counts.name]
    return rebinned_series


def reorder_sim_data(channel_series, ref_channel_series, months, channel, population):
    """
    A function to reorder sim data to match reference data
    """

    print(channel_series.head())
    print(ref_channel_series.head())
    print(population.head())

    # Prepare age bins from multi-index for cuts
    # TODO: push bins [0, 5), [5, 15) into reference itself?
    age_bins = ref_channel_series.index.levels[ref_channel_series.index.names.index('Age Bins')]
    age_bins = sorted(age_bins.tolist() + [0])

    # Data frames
    df_pop = population.reset_index()
    df_sim = channel_series.reset_index()
    df_ref = ref_channel_series.reset_index()

    # Seasons
    # TODO: handle this already in site_Laye reference, e.g. april = [92, 121]
    months_of_year = dict((v,k) for k,v in enumerate(calendar.month_name))
    seasonIndex = []
    for i in range(len(months)):
        seasonIndex.extend([t for t in range(months_of_year[months[i]] - 1, df_sim.Time[-1:] + 1, 12)])
    seasons = list(set(df_ref['Seasons']))
    season_month = dict(zip(months,seasons))
    print(season_month)

    # Reorder simulation data to match reference data

    # The population normalization part
    pop = pd.merge(df_sim, df_pop, left_on=['Time', 'Age Bins'], right_on=['Time', 'Age Bins'])  # Find population by age bin and pull out relevant rows
    df_sim[channel] = pop[channel].multiply(pop['Average Population by Age Bin']).values

    # Birth cohort age bins from time
    df_sim['Age Bins'] = pd.cut((df_sim['Time'] + 1) / 12, age_bins)  # Reorder Age Bins

    # Season from time
    df_sim = df_sim[df_sim.Time.isin(seasonIndex)]  # Only retain months corresponding to seasons in ref data
    df_sim['Time'] = [season_month[calendar.month_name[i]] for i in (df_sim['Time']%12+1)]  # Label Season

    # Name with channel to prepare for merging
    df_sim['PfPR Type'] = [s for s in channel.split() if "temia" in s]*len(df_sim)
    df_sim = df_sim.rename(index=str, columns={"Time": "Seasons"})

    # Reorder simulation data frame to match reference data frame
    # df_sim = df_sim[list(df_ref.columns.values)]

    return df_sim


def accumulate_agebins_cohort(simdata, average_pop, sim_agebins, raw_agebins):
    """
    A function to sum over each year's values in a summary report,
    combining incidence rate and average population
    to give total counts and population in the reference age binning.
    """

    glommed_data = [0] * len(raw_agebins)
    simageindex = [-1] * len(sim_agebins)
    yearageindex = [-1] * len(simdata)
    num_in_bin = [0] * len(raw_agebins)

    for i in range(len(simageindex)):
        for j, age in enumerate(raw_agebins):
            if sim_agebins[i] > age:
                simageindex[i] = j
                break

    for i in range(len(yearageindex)):
        for j, age in enumerate(raw_agebins):
            if i < age:
                yearageindex[i] = j
                break

    for i in range(len(yearageindex)):
        if yearageindex[i] < 0:
            continue
        for j in range(len(simageindex)):
            if simageindex[j] < 0:
                continue
            glommed_data[simageindex[j]] += simdata[i][j] * average_pop[i][j]
            num_in_bin[simageindex[j]] += average_pop[i][j]

    return num_in_bin, glommed_data


def get_spatial_report_data_at_date(sp_data, date):

    return pd.DataFrame({'node': sp_data['nodeids'],
                         'data': sp_data['data'][date]})


def get_risk_by_distance(df_sim, distances, ddf):

    nodelist = df_sim['node'].values.tolist()
    rel_risk = []

    for k, n_dist in enumerate(distances):
        pos_w_pos = 0.
        tot_w_pos = 0.

        for hh_num in df_sim.index:
            if df_sim.ix[hh_num, 'pos'] < 1:
                continue

            if n_dist == 0 and df_sim.ix[hh_num, 'pop'] > 1:
                hh_pos = df_sim.ix[hh_num, 'pos']
                hh_tot = df_sim.ix[hh_num, 'pop']
                num_pos = (hh_pos - 1)*hh_pos
                num_ppl = (hh_tot - 1)*hh_pos

            else:
                # node IDs of nodes within distance
                neighbors = ddf[(ddf['node1'] == nodelist[hh_num]) & (ddf['node2'] != nodelist[hh_num]) &
                                (ddf['dist'] <= n_dist) & (ddf['dist'] > distances[k-1])]['node2'].values

                ndf = df_sim[df_sim['node'].isin(neighbors)]
                num_pos = sum(ndf['pos'].values)
                num_ppl = sum(ndf['pop'].values)

            pos_w_pos += num_pos
            tot_w_pos += num_ppl

        if tot_w_pos > 0:
            rel_risk.append(pos_w_pos/tot_w_pos)
        else:
            rel_risk.append(0)

    return rel_risk