import itertools
from datetime import date, datetime
import calendar
import itertools
import logging
import random
from collections import OrderedDict
from datetime import date

import numpy as np
import numpy.ma as ma
import pandas as pd


import dtk.utils.parsers.malaria_summary as malaria_summary

logger = logging.getLogger(__name__)


def grouped_df(df, pfprdict, index, column_keep, column_del):
    """
    Recut dataframe to recategorize data into desired age and parasitemia bins

    df - Dataframe to be rebinned

    pfprdict - Dictionary mapping postive counts per slide view (http://garkiproject.nd.edu/demographic-parasitological-surveys.html)
                to density of parasites/gametocytes per uL

    index - Multi index into which 'df' is rebinned

    column_keep - Column (e.g. parasitemia) to keep

    column_del - Column (e.g. gametocytemia) to delete
    """
    dftemp = df.copy()
    del dftemp[column_del]

    dftemp['PfPR Bin'] = df[column_keep]
    dftemp = aggregate_on_index(dftemp, index)

    dfGrouped = dftemp.groupby(['Season', 'Age Bin', 'PfPR Bin'])

    dftemp = dfGrouped[column_keep].count()
    dftemp = dftemp.unstack().fillna(0).stack()
    dftemp = dftemp.rename(column_keep).reset_index()
    dftemp['PfPR Bin'] = [pfprdict[p] for p in dftemp['PfPR Bin']]

    dftemp = dftemp.set_index(['Season', 'Age Bin', 'PfPR Bin'])

    logger.debug('\n%s', dftemp)

    return dftemp


def season_channel_age_density_csv_to_pandas(csvfilename, metadata):
    """
    A helper function to convert Garki reference data locally stored in a csv file generate by code:

    https://github.com/pselvaraj87/Malaria-GarkiDB

    The data in the csv file is stored as:

      1          Patient_id  Village      Seasons        Age     Age Bins      Parasitemia  Gametocytemia
      2 0           4464     Batakashi      DC2  0.00547945205479  1.0          0.0               0.0
      3 1           2230     Ajura          DC2  0.0493150684932   1.0          0.005             0.0
      4 2           6995     Rafin Marke    DC2  0.0821917808219   1.0          0.0               0.0
      5 3           5407     Ungwar Balco   DC2  0.120547945205    1.0          0.0               0.0
      6 4           4988     Ungwar Balco   DC2  0.104109589041    1.0          0.005             0.0
      7 5           9282     Kargo Kudu     DC2  0.145205479452    1.0          0.0075            0.0
      8 6           2211     Ajura          DC2  0.134246575342    1.0          0.0               0.0
      ...
      ...

    to a Pandas dataframe with Multi Index:

    Channel                            Season     Age Bin   PfPR Bin
    PfPR by Gametocytemia and Age Bin  start_wet  5         0             0
                                                            50            0
                                                            500           0
                                                            5000          5
      ...

    """
    df = pd.read_csv(csvfilename)
    df = df.loc[df['Village'] == metadata['village']]

    pfprBinsDensity = metadata['parasitemia_bins']
    uL_per_field = 0.5 / 200.0  # from Garki PDF - page 111 - 0.5 uL per 200 views
    pfprBins = 1 - np.exp(-np.asarray(pfprBinsDensity) * uL_per_field)
    seasons = metadata['seasons']
    pfprdict = dict(zip(pfprBins, pfprBinsDensity))

    bins = OrderedDict([
        ('Season', metadata['seasons']),
        ('Age Bin', metadata['age_bins']),
        ('PfPR Bin', pfprBins)
    ])
    bin_tuples = list(itertools.product(*bins.values()))
    index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())

    df = df.loc[df['Seasons'].isin(seasons)]
    df = df.rename(columns={'Seasons': 'Season', 'Age': 'Age Bin'})

    df2 = grouped_df(df, pfprdict, index, 'Parasitemia', 'Gametocytemia')
    df3 = grouped_df(df, pfprdict, index, 'Gametocytemia', 'Parasitemia')
    dfJoined = df2.join(df3).fillna(0)
    dfJoined = pd.concat([dfJoined['Gametocytemia'], dfJoined['Parasitemia']])
    dfJoined.name = 'Counts'
    dftemp = dfJoined.reset_index()
    dftemp['Channel'] = 'PfPR by Gametocytemia and Age Bin'
    dftemp.loc[len(dftemp)/2:, 'Channel'] = 'PfPR by Parasitemia and Age Bin'
    dftemp = dftemp.rename(columns={'Seasons': 'Season', 'PfPR Bins': 'PfPR Bin', 'Age Bins': 'Age Bin'})
    dftemp = dftemp.set_index(['Channel', 'Season', 'Age Bin', 'PfPR Bin'])

    logger.debug('\n%s', dftemp)

    return dftemp


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

    To a pd.DataFrame with MultiIndex:
                                                                     Counts
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
            channel_dict[channel] = malaria_summary.json_to_pandas(channel_data, bins)
        season_dict[season] = pd.DataFrame(channel_dict)

    # Concatenate the multi-channel (i.e. parasitemia, gametocytemia) dataframes by season
    df = pd.concat(season_dict.values(), axis=1, keys=season_dict.keys(), names=['Season', 'Channel'])

    # Stack the hierarchical columns into the MultiIndex
    channel_series = df.stack(['Season', 'Channel'])\
                       .reorder_levels(['Channel', 'Season', 'Age Bin', 'PfPR Bin'])\
                       .sort_index()

    reference_df = pd.DataFrame(channel_series.rename('Counts'))  # 1-column DataFrame for standardized combine/compare
    logger.debug('\n%s', reference_df)

    return reference_df


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
    reference_df = pd.DataFrame(reference)
    reference_df.set_index(index_key, inplace=True)

    logger.debug('\n%s', reference_df)
    return reference_df


def convert_annualized(s, reporting_interval=None, start_day=None):
    """
    Use Time index level to revert annualized rate channels,
    e.g. Annual Incidence --> Incidence per Reporting Interval
         Average Population --> Person Years
    :param s: pandas.Series with 'Time' level in multi-index
    :param reporting_interval: (optional) metadata from original output file on interval related to 'Time' index
    :param start_day: (optional) metadata from original output file on beginning of first aggregation interval
    :return: pandas.Series normalized to Reporting Interval as a fraction of the year
    """

    s_ix = s.index
    time_ix = s_ix.names.index('Time')
    time_levels = s_ix.levels[time_ix].values

    start_time = (start_day - 1) if start_day else 0  # metadata reported at end of first time step

    time_intervals = np.diff(np.insert(time_levels, 0, values=start_time))  # prepending simulation Start_Time

    if reporting_interval and len(time_intervals) > 1 and np.abs(time_intervals[0] - reporting_interval) > 1:
        raise Exception('Time differences between reports differ by more than integer rounding.')
    if len(time_intervals) > 2 and np.abs(time_intervals[0] - time_intervals[1]) > 1:
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
        logger.debug("%s (%s) : %s" % (ix.name, ix.dtype, ix.values))

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
    if keep != slice(None):
        df = df.groupby([ix.name for ix in levels]).sum()[keep].dropna()
    logger.debug('Data aggregated/joined on MultiIndex levels:\n%s', df.head(15))
    return df


def aggregate_on_month(sim, ref):
    months = list(ref['Month'].unique())
    sim = sim[sim['Month'].isin(months)]

    return sim


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


def ento_data(csvfilename, metadata):

    df = pd.read_csv(csvfilename)

    df = df[['date', 'gambiae_count', 'funestus_count', 'adult_house']]
    df['gambiae'] = df['gambiae_count'] / df['adult_house']
    df['funestus'] = df['funestus_count'] / df['adult_house']
    df = df.dropna()

    df['date'] = pd.to_datetime(df['date'])
    dateparser = lambda x: int(x.strftime('%m'))
    df['Month'] = df['date'].apply(lambda x: int(dateparser(x)))
    df2 = df.groupby('Month')['gambiae'].apply(np.mean).reset_index()
    df2['funestus'] = list(df.groupby('Month')['funestus'].apply(np.mean))

    # Keep only species requested
    for spec in metadata['species']:
        df1 = df2[['Month', spec]]
        df1 = df1.rename(columns={spec: 'Counts'})
        df1['Channel'] = [spec] * len(df1)
        if 'dftemp' in locals():
            dftemp = pd.concat([dftemp, df1])
        else:
            dftemp = df1.copy()

    dftemp = dftemp.sort_values(['Channel', 'Month'])
    dftemp = dftemp.set_index(['Channel', 'Month'])

    return dftemp


def garki_ento_data(csvfilename, metadata):

    df = pd.read_csv(csvfilename)

    df = df.loc[df['Village'] == metadata['village']]
    df['Channel'] = df['Channel'].apply(lambda x: x.split('.')[1].lower())
    df = df.loc[df['Channel'].isin(metadata['species'])]

    del df['Village']
    if 'Unnamed: 0' in df.columns:
        del df['Unnamed: 0']

    dftemp = df.sort_values(['Channel', 'Month'])
    dftemp = dftemp.set_index(['Channel', 'Month'])

    return dftemp


def hhs_to_nodes(csvfilename, hhs_file, metadata):
    from geopy.distance import vincenty
    hh_hf_records = pd.read_csv(csvfilename)
    hh_hf_records = hh_hf_records[hh_hf_records['hf_name'] == metadata['hf']]
    hh_hf_records = hh_hf_records.rename(index=str, columns={"House_ID": "ID", 'lat_r2': 'lat', 'lng_r2': 'lon'})
    hhs_df = pd.read_csv(hhs_file)
    # hhs_df = hhs_df[['ID', 'household_number_mda1', 'household_number_mda2', 'household_number_mda3']]
    hhs_df = hhs_df[['ID', 'household_number_mda1']]
    # pd.unique(hhs_df[['household_number_mda1', 'household_number_mda2', 'household_number_mda3']].values.ravel('K'))
    hhs_df = hhs_df.rename(index=str, columns={"household_number_mda2": "house_ID"})

    all_hh_records = hh_hf_records.merge(hhs_df, on=['ID'])
    all_hh_records = all_hh_records.dropna()

    y_min = all_hh_records['lat'].min()
    y_max = all_hh_records['lat'].max()
    x_min = all_hh_records['lon'].min()
    x_max = all_hh_records['lon'].max()

    # square grid cell/pixel side (in m)
    cell_size = 1000

    # demographic grid cell should contain more households than a threshold
    cell_household_threshold = 1

    # how far people would definitely go by foot in units of neighborhood hops (1 hop is the adjacent 8 cells on the grid; 2 hops is the adjacent 24 cells, etc.
    # this prepares an approximation of a local topology
    migration_radius = 2

    hh_records = all_hh_records[
        (all_hh_records.lon > x_min) & (all_hh_records.lon < x_max) & (all_hh_records.lat > y_min) & (
        all_hh_records.lat < y_max)]

    # get point locations of households
    points = hh_records.as_matrix(["lon", "lat"])

    # get number of grid cells along the x (grid width) and y axis (grid height) based on the bounding box dimensions and pixel/cell size
    num_cells_x = int(1000 * vincenty((y_min, x_min), (y_min, x_max)).km / cell_size) + 1
    num_cells_y = int(1000 * vincenty((y_min, x_min), (y_max, x_min)).km / cell_size) + 1

    # bin households in the grid
    H, xedges, yedges = np.histogram2d(points[:, 0], points[:, 1], bins=[num_cells_x, num_cells_y])

    # get centroids of grid cells
    x_mid = (xedges[1:] + xedges[:-1]) / 2
    y_mid = (yedges[1:] + yedges[:-1]) / 2

    # build a mesh of centroids
    X_mid, Y_mid = np.meshgrid(x_mid[:], y_mid[:])

    # filter pixels/cells by number of households greater than a threshold in each cell
    cells_masking = ma.masked_less(H, cell_household_threshold)
    cells_mask = cells_masking.mask

    # mask returns False for valid entries;  True would be easier to work with
    inverted_filtered_households_mask = np.in1d(cells_mask.ravel(), [False]).reshape(cells_mask.shape)
    filtered_household_cells_idx = np.where(inverted_filtered_households_mask)

    # map between node coordinates and node label; to avoid look-up logic
    coor_idxs_2_node_label = {}

    for i, idx_x in enumerate(filtered_household_cells_idx[0]):
        idx_y = filtered_household_cells_idx[1][i]

        node_label = str(i)  # unique node label

        coor_idxs_2_node_label[str(idx_x) + "_" + str(idx_y)] = node_label

    node_label = [0]*len(hh_records)
    for i in range(len(points)):
        X = X_mid * np.transpose(inverted_filtered_households_mask)
        Y = Y_mid * np.transpose(inverted_filtered_households_mask)
        X[X == 0] = 'nan'
        Y[Y == 0] = 'nan'
        x = X_mid - points[i][0]
        y = Y_mid - points[i][1]
        dist = x**2 + y**2
        neigh_cand = np.argwhere(dist == np.min(dist))
        node_label[i] = coor_idxs_2_node_label[str(neigh_cand[0][0]) + "_" + str(neigh_cand[0][1])]

    hh_records['NodeID'] =node_label

    return hh_records


def ento_spatial_data(datafilename, hhs_hffilename, hhs_file, metadata):

    # df2 = hhs_to_nodes(hhs_hffilename, hhs_file, metadata)

    df = pd.read_csv(datafilename)

    df = df[['date', 'gambiae_count', 'funestus_count', 'adult_house']]
    df['gambiae'] = df['gambiae_count'] / df['adult_house']
    df['funestus'] = df['funestus_count'] / df['adult_house']
    df = df.dropna()
    df['NodeID'] = [random.randint(0, 32) for i in range(len(df))]

    df['date'] = pd.to_datetime(df['date'])
    dateparser = lambda x: int(x.strftime('%m'))
    df['Month'] = df['date'].apply(lambda x: int(dateparser(x)))
    df2 = df.groupby(['Month', 'NodeID'])['gambiae'].apply(np.mean).reset_index()
    df2['funestus'] = list(df.groupby(['Month', 'NodeID'])['funestus'].apply(np.mean))

    # Keep only species requested
    for spec in metadata['species']:
        df1 = df2[['Month', 'NodeID',  spec]]
        df1 = df1.rename(columns={spec: 'Counts'})
        df1['Channel'] = [spec] * len(df1)
        if 'dftemp' in locals():
            dftemp = pd.concat([dftemp, df1])
        else:
            dftemp = df1.copy()

    dftemp = dftemp.sort_values(['Channel', 'Month', 'NodeID'])
    dftemp = dftemp.set_index(['Channel', 'Month', 'NodeID'])

    return dftemp
