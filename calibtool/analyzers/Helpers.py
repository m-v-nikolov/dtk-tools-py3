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
    OrderedDict([('Time', [31, 61, 92, ..., 1095]), ('Age Bin', [0, 10, 20, ..., 1000])])
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
            ('Age Bin', metadata['Age Bins'])
        ])
    elif grouping == 'DataByTimeAndPfPRBinsAndAgeBins':
        return OrderedDict([
            ('Time', time),
            ('PfPR Bin', metadata['Parasitemia Bins']),
            ('Age Bin', metadata['Age Bins'])
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

    Channel                            Season     Age Bin   PfPR Bin
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
    df = pd.concat(season_dict.values(), axis=1, keys=season_dict.keys(), names=['Season', 'Channel'])

    # Stack the hierarchical columns into the MultiIndex
    channel_series = df.stack(['Season', 'Channel'])\
                       .reorder_levels(['Channel', 'Season', 'Age Bin', 'PfPR Bin'])\
                       .sort_index()

    logger.debug('\n%s', channel_series)

    return channel_series


def channel_age_json_to_pandas(reference, index_key='Age Bin'):
    """
    A helper function to convert reference data from its form in e.g. site_Dielmo.py:

        reference_data = {
            "Average Population by Age Bin": [ 55, 60, 55, 50, 50, ... ],
            "Age Bin": [ 1, 2, 3, 4, 5, ... ],
            "Annual Clinical Incidence by Age Bin": [ 3.2, 5, 6.1, 4.75, 3.1, ... ]
        }

    To a pd.DataFrame:

             Annual Clinical Incidence by Age Bin  Average Population by Age Bin
    Age Bin
    1                                        3.20                             55
    2                                        5.00                             60
    3                                        6.10                             55
    4                                        4.75                             50
    5                                        3.10                             50

    """
    index = reference.pop(index_key)
    reference_df = pd.DataFrame(reference, index=index)
    reference_df.index.name = index_key

    logger.debug('\n%s', reference_df)
    return reference_df


def convert_annualized(s):
    """
    Use Time index level to revert annualized rate channels,
    e.g. Annual Incidence --> Incidence per Reporting Interval
         Average Population --> Person Years
    :param s: pandas.Series with 'Time' level in multi-index
    :return: pandas.Series normalized to Reporting Interval as a fraction of the year
    """

    s_ix = s.index
    time_ix = s_ix.names.index('Time')
    time_levels = s_ix.levels[time_ix].values

    # TODO: instead of assuming Start_Time=0, fetch from report MetaData
    time_intervals = np.diff(np.insert(time_levels, 0, values=0))  # prepending Start_Time=0
    if len(time_intervals) > 1 and np.abs(time_intervals[0] - time_intervals[1]) > 1:
        raise Exception('Time differences between reports differ by more than integer rounding.')

    intervals_by_time = dict(zip(time_levels, time_intervals))
    df = s.reset_index()
    df[s.name] *= df.Time.apply(lambda x: intervals_by_time[x] / 365.0)
    return df.set_index(s_ix.names)


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


def age_from_birth_cohort(df):
    """
    Reinterpret 'Time' as 'Age Bin' for a birth cohort
    :param df: a pandas.DataFrame of counts and 'Time' in days
    :return: a pandas.DataFrame including an additional (or overwritten) 'Age Bin' column
    """

    df['Age Bin'] = df['Time'] / 365.0   # Time in days but Age in years
    return df


def season_from_time(df, seasons=None):
    """
    Reinterpret 'Time' as 'Month' or 'Season' for seasonal data
    :param df: a pandas.DataFrame of counts and 'Time' in days
    :param seasons: optional dictionary of month names to season names
    :return: a pandas.DataFrame including an additional 'Season' or 'Month' column
    """

    # Day of Year from Time (in days)
    day_of_year = 1 + df['Time'] % 365

    # Assign each Day of Year to a named Month
    month = day_of_year.apply(lambda x: calendar.month_name[date.fromordinal(x).month])

    # Return season if optional lookup is available, otherwise return month
    if seasons:
        df['Season'] = month.apply(lambda x: seasons.get(x))
        df.dropna(subset=['Season'], inplace=True)
    else:
        df['Month'] = month

    return df


def pairwise(iterable):
    """ s -> (s0,s1), (s1,s2), (s2, s3), ... """
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)


def aggregate_on_index(df, index, keep=slice(None)):
    """
    Aggregate and re-index data on specified (multi-)index (levels and) intervals
    :param df: a pandas.DataFrame with columns matching the specified (Multi)Index (level) names
    :param index: pandas.(Multi)Index of categorical values or right-bin-edges, e.g. ['early', 'late'] or [5, 15, 100]
    :param keep: optional list of columns to keep, default=all
    :return: pandas.Series or DataFrame of specified channels aggregated and indexed on the specified binning
    """

    if isinstance(index, pd.MultiIndex):
       levels = index.levels
    else:
       levels = [index]  # Only one "level" for Index. Put into list for generic pattern as for MultiIndex

    for ix in levels:
        logger.debug(ix.name, ix.dtype, ix.values)

        if ix.name not in df.columns:
            raise Exception('Cannot perform aggregation as MultiIndex level (%s) not found in DataFrame:\n%s' % (ix.name, df.head()))

        # If dtype is object, these are categorical (e.g. season='start_wet', channel='gametocytemia')
        if ix.dtype == 'object':
            # TODO: DatetimeIndex, TimedeltaIndex are implemented as int64.  Do we want to catch them separately?
            # Keep values present in reference index-level values; drop any that are not
            df = df[df[ix.name].isin(ix.values)]

        # Otherwise, the index-level values are upper-edges of aggregation bins for the corresponding channel
        elif ix.dtype in ['int64', 'float64']:
            bin_edges = np.concatenate(([-np.inf], ix.values))
            labels = ix.values  # just using upper-edges as in reference
            # TODO: more informative labels? would need to be modified also in reference to maintain useful link...
            # labels = []
            # for low, high in pairwise(bin_edges):
            #     if low == -np.inf:
            #         labels.append("<= {0}".format(high))
            #     elif high == np.inf:
            #         labels.append("> {0}".format(low))
            #     else:
            #         labels.append("{0} - {1}".format(low, high))

            df[ix.name] = pd.cut(df[ix.name], bin_edges, labels=labels)

        else:
            logger.warning('Unexpected dtype=%s for MultiIndex level (%s). No aggregation performed.', ix.dtype, ix.name)

    # Aggregate on reference MultiIndex, keeping specified channels and dropping missing data
    df = df.groupby([ix.name for ix in levels]).sum()[keep].dropna()
    logger.debug('Data aggregated on MultiIndex levels:\n%s', df.head(15))
    return df


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