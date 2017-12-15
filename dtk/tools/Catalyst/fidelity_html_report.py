import numpy as np
import os
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import shutil


# TODO: redesign generation of HTML UI (e.g. some package for ), cleaner separation of HTML UI and logic/data analysis
class FidelityHTMLReport:
    """Takes simulation data and generates summary HTML pages and one detail HTML page per channel."""
    _html_start = """
    <html>
    <head>
    <script type="text/javascript" src="fidelity_html_report.js"></script>
    <link rel="stylesheet" href="fidelity_html_report.css">
    </head>
    <body>
    <button class="button" style="position: fixed; right: 0.6%; top: 10px;z-index:10000; font-size: 16px;width: 30px" onmouseup="javascript:toggleReportHeader(this)">-</button>
    <div id="report_header" style="position: fixed; left: 7px; top: 5px;z-index: 100;width:99%" class="box">
    """

    _html_sections_select = """
        <select id="sections" onchange="javascript:scrollToSection(this[this.selectedIndex].text)" style="font-size: 18px;">
        </select><br>
        <script lang="javascript">populateSections()</script>
    """

    _html_top_pane_start = """
        <table border=0 width="100%">
            <tr>
                <td valign="top" width="20%">__args1__</td>
                <td width="10%">&nbsp;&nbsp;&nbsp;</td>
                <td valign="bottom" width="40%">__perf__</td>
    """

    _html_measures_table_comment = '<i>Measures compare mean time series of the given sweep value with the baseline mean time series or confidence intervals (+/- 1 and 2 SE).</i><br>'
    _html_green_shaded_confidence_interval_comment = '<br><i>Note for above plots: green shaded areas around base line represent confidence intervals (+/- 1 and 2 SE).</i><br>'

    _html_end = """
        <div style = "height:500px;">&nbsp;</div>
        <script lang="text/javascript">initPage()</script>
        </body></html>"""

    _measure_names = {
        'IN1SE': 'time series % within 1 SE interval',
        'IN2SE': 'time series % within 2 SE interval',
        'IO2SE': 'time series % overlaps 2 SE interval',
        'MAD': 'mean abs. deviation',
        'MAPE': 'mean abs. deviation %',
        'CORR': 'correlation',
        'KS': 'KS test [CDF distance, p-value]'
    }

    required_keys = ['nruns', 'duration', 'init', 'sweep_param', 'sweep_values', 'sweep_base_value',
                     'inset_channel_names']
    optional_keys = ['rolling_win_size', 'step_from', 'step_to', 'node_count']

    def __init__(self, df_raw, report_dir_path, def_name, init, debug=False, **kwargs):
        # init frequently used members so they show up in intellisense, actual values are dynamically set from **kwargs below
        self.sweep_param = None
        self.sweep_base_value = None
        self.sweep_values = None
        self.rolling_win_size = None

        import inspect
        args, _, _, values = inspect.getargvalues(inspect.currentframe())
        for key in args:
            if key != 'self' and not hasattr(self, key):
                setattr(self, key, values[key])

        for k, v in kwargs.items():
            if k in self.all_keys():
                setattr(self, k, v)

        self.colors_all = ['darkgreen', 'darkblue', 'blue', 'cyan', 'coral', 'darkorange', 'yellow', 'grey', 'purple',
                           'maroon']
        step_count = len(df_raw['step'].unique())
        if self.rolling_win_size is None:
            self.rolling_win_size = 30 if step_count > 300 else max(int(step_count / 10), 1)

        self.steps = sorted(df_raw['step'].unique())
        self.runs_count = len(df_raw['Run_Number'].unique())
        self.name = os.path.basename(report_dir_path)

        # empty result dir, deleting only types of files related to the report
        for p in os.listdir(report_dir_path):
            if p.endswith('.png') or p != 'data_raw.csv' and p.endswith('.csv') or p.endswith('.html') or p.endswith(
                    '.js') or p.endswith('.css'):
                ppath = os.path.join(report_dir_path, p)
                os.remove(ppath)

        source_path = os.path.dirname(__file__)
        shutil.copy2(os.path.join(source_path, 'fidelity_html_report.js'),
                     self.get_result_path('fidelity_html_report.js'))
        shutil.copy2(os.path.join(source_path, 'fidelity_html_report.css'),
                     self.get_result_path('fidelity_html_report.css'))

        # dict for caching measures and plots
        self.init_measure_cache()

    @staticmethod
    def all_keys():
        """List of required and optional arguments for instantiating FidelityHTMLReport."""
        return FidelityHTMLReport.required_keys + FidelityHTMLReport.optional_keys

    ### main HTML page methods

    def create_summary_page(self):
        """Generates summary HTML page."""
        report_path = self.get_result_path('summary_report.html')

        html = self._html_start
        html += '<h2>Fidelity Report: {}</h2>'.format(self.name)

        pd.set_option('display.max_colwidth', -1)

        df = pd.DataFrame([list(t) for t in zip(['number of runs', 'sim duration', 'node count'],
                                                [self.nruns, self.duration, self.node_count])], columns=['key', ' '])
        df = df.set_index('key')
        df.index.names = [None]
        html_args1 = df.to_html(**self.df_html_summary_args())

        df = self.init_perf_df()
        html_perf = df.to_html(**self.df_html_summary_args())

        html_summ = self._html_top_pane_start
        html_summ += """
                <td width="30%">
                    <div>Channels</div>
                    {}
                    <button onclick="javascript:window.scrollTo(0,0);document.getElementById('sections').selectedIndex=0" class="button">Back To Channels Summary</button>
                    <button id="img_rolling_switch" onclick="javasciprt:toggleRollingImages()" class="button">Show Raw Data Plots</button>
                </td>
            </tr>
        </table>""".format(self._html_sections_select)
        html += html_summ.replace("__args1__", html_args1).replace("__perf__", html_perf)
        html += '</div>'

        html += '<div id = "report_header_ph" style = "height:135px;">&nbsp;</div>'
        html += '<h2>Channels Summary</h2>'
        df_channels = pd.DataFrame()
        for channel in self.inset_channel_names:
            sweep_values_map, corr, _, _ = self.get_channel_summary_measures(channel)

            df = self.init_measures_summary_df(corr, sweep_values_map, ['se', 'dist'])  # 'perf', 'corr', 'prob'
            del df['category']
            df = pd.DataFrame(df.stack())
            df = df.reset_index()
            df.columns = ['measure_name', self.sweep_param, 'measure_value']
            df['channel'] = channel
            df = df[df['measure_name'].isin([self._measure_names['IN2SE'], self._measure_names['MAPE']])]
            df_channels = pd.concat([df_channels, df])

        measures_count = len(df_channels['measure_name'].unique())
        df_channels['measure_value'] = df_channels['measure_value'].apply(
            lambda x: np.round(x, 2) if type(x) == type(1.0) else x)

        df_channels = df_channels.pivot_table(index='channel', columns=['measure_name', self.sweep_param],
                                              values=['measure_value'], aggfunc='first')
        df_channels.index.names = [None]
        df_channels = df_channels.sort_index(axis=1, ascending=[None, True, self.is_sweep_ascending()])

        html_cols = '<col span="1" class="col0" />'
        html_cols += ''.join(['<col span="{}" class="col{}"/>'.format(len(self.sweep_values), str((i % 2) + 1)) for i in
                              range(measures_count)])
        html_cols += '<thead>'
        html_channels = df_channels.to_html(**self.df_html_summary_args()).replace('measure_value', '').replace(
            'measure_name', '').replace('Base_Individual_Sample_Rate', '')
        html += html_channels.replace('<thead>', html_cols)

        for channel in self.inset_channel_names:
            sweep_values_map, corr, plot_html, plot_html2 = self.get_channel_summary_measures(channel)
            df = self.init_measures_summary_df(corr, sweep_values_map, ['se', 'dist', 'corr', 'prob'])  # 'perf',
            del df['category']

            html += '<br><h2 id="{0}">{0}</h2>'.format(channel)
            html += df.to_html(**self.df_html_summary_args(4))
            html += self._html_measures_table_comment
            html += '<a href="{}_report.html">'.format(channel)
            html += plot_html
            html += plot_html2
            html += '</a>'

        html += self._html_green_shaded_confidence_interval_comment
        html += self._html_end

        self.save_report(html, report_path)

    def create_channel_detail_page(self, channel):
        """Generates channel detail HTML page."""
        report_path = self.get_result_path('{}_report.html'.format(channel))
        if os.path.isfile(report_path):
            os.remove(report_path)

        data_channel = 'inset_{}'.format(channel)

        html = self._html_start
        html += '<h2>Fidelity Report: {}, {}</h2>'.format(self.name, channel)

        pd.set_option('display.max_colwidth', -1)

        df = pd.DataFrame([list(t) for t in zip(['number of runs', 'sim duration', 'node count'],
                                                [self.nruns, self.duration, self.node_count])], columns=['key', ' '])
        df = df.set_index('key')
        df.index.names = [None]
        html_args1 = df.to_html(**self.df_html_summary_args())

        df = self.init_perf_df()
        html_perf = df.to_html(**self.df_html_summary_args())
        html_summ = self._html_top_pane_start
        html_summ += """
                <td width="30%">
                    <div>Sections</div>
                    {}
                    <button onclick="javascript:document.location='summary_report.html#{}'" class="button">Back To Summary</button>
                    <button id="img_rolling_switch" onclick="javasciprt:toggleRollingImages()" class="button">Show Raw Data Plots</button>
                </td>
            </tr>
        </table>""".format(self._html_sections_select, channel)
        html += html_summ.replace("__args1__", html_args1).replace("__perf__", html_perf)
        html += '</div>'
        html += '<div id = "report_header_ph" style = "height:135px;">&nbsp;</div>'

        sweep_values_map, corr, plot_html, plot_html2 = self.get_channel_summary_measures(channel)
        dfp = self.get_channel_measure_data(channel)
        dfps = self.rolling_mean(dfp)

        # Show how it los with fewer runs
        lower_run_count = self.get_lower_run_count()
        dfp2 = self.get_channel_measure_data(channel, lower_run_count)

        df = self.init_measures_summary_df(corr, sweep_values_map, ['se', 'dist', 'corr', 'prob'])
        del df['category']

        html += '<h2>{} (Detail)</h2>'.format(channel)
        html += df.to_html(**self.df_html_summary_args(4))
        html += self._html_measures_table_comment
        html += '<br>'

        html += '<h2>Time Series</h2>'
        html += '<select id="cp_w_base_means_switch" onchange="javascript:switchCompareModeImages(\'{}\')"  style="font-size: 18px;">'.format(
            data_channel)
        html += '   <option value="show_all" selected>Show all plots</option>'
        html += '   <option value="{}">Baseline vs. all means</option>'.format(self.sweep_base_value)
        for r in self.sweep_values:
            if r == self.sweep_base_value: continue
            html += '   <option value="{0}">Baseline vs. sweep value {0}</option>'.format(r)
        html += '</select>'

        html += '<select id="cp_w_base_means_runs_switch" onchange="javascript:switchCompareModeImages(\'{}\')"  style="font-size: 18px;">'.format(
            data_channel)
        html += '   <option value="{0}">{0} runs</option>'.format(self.runs_count)
        html += '   <option value="{0}">{0} runs</option>'.format(lower_run_count)
        html += '</select>'

        html += '<h3>Means with SE Intervals</h3>'
        html += plot_html
        html += plot_html2

        for r in self.sweep_values:
            if r == self.sweep_base_value: continue
            html += self.plot_time_series_interval_compare_html(dfp, sweep_values_map, data_channel, r, do_rolling=True,
                                                                is_visible=True)
            self.plot_time_series_interval_compare_html(dfp, sweep_values_map, data_channel, r, is_visible=False)

        for r in self.sweep_values:
            if r == self.sweep_base_value: continue
            html += self.plot_time_series_interval_compare_html(dfp2, sweep_values_map, data_channel, r,
                                                                do_rolling=True, lower_run_count=lower_run_count,
                                                                is_visible=False)
            self.plot_time_series_interval_compare_html(dfp2, sweep_values_map, data_channel, r,
                                                        lower_run_count=lower_run_count, is_visible=False)

        html += '<h3>Individual Runs</h3>'
        for sv in self.sweep_values:
            html += self.plot_time_series_individual_runs_html(dfp, sweep_values_map, data_channel, sv, do_rolling=True,
                                                               is_visible=True)
            self.plot_time_series_individual_runs_html(dfp, sweep_values_map, data_channel, sv, is_visible=False)

        # Show how it looks with fewer runs
        for sv in self.sweep_values:
            html += self.plot_time_series_individual_runs_html(dfp2, sweep_values_map, data_channel, sv,
                                                               do_rolling=True, lower_run_count=lower_run_count,
                                                               is_visible=False)
            self.plot_time_series_individual_runs_html(dfp2, sweep_values_map, data_channel, sv,
                                                       lower_run_count=lower_run_count, is_visible=False)

        html += '<h3>Means, Simulation End (last 10% of steps)</h2>'
        html += self.plot_time_series_zoom_end_html(dfps, sweep_values_map, data_channel, do_rolling=True)
        self.plot_time_series_zoom_end_html(dfps, sweep_values_map, data_channel, do_rolling=False)

        html += self._html_green_shaded_confidence_interval_comment
        html += '<br>'
        html += '<h2>Noise (SE) Convergence</h2>'
        html += self.plot_se_vs_runs_html(sweep_values_map, data_channel)

        html += '<h2>Correlation</h2>'
        html += self.plot_corr_html(dfps, sweep_values_map, data_channel)
        html += '<h2>Distribution</h2>'
        html += self.plot_kde_html(dfps, sweep_values_map, data_channel)
        html += '<br>'
        html += self.plot_histogram_html(dfps, sweep_values_map, data_channel)
        html += self._html_end

        # TODO: memory footprint info

        self.save_report(html, report_path)

    def save_report(self, html, report_path):
        """Saves generated HTML report into a file."""
        with open(report_path, "w") as rpt_file:
            rpt_file.write(html)

        print("Report generated in {}".format(os.path.normpath(os.path.abspath(report_path))))

    ### calculate measures

    # all measures
    def init_sweep_values_map(self, dfp, data_channel):
        """ Creates a dict containing measures and plotting info for each channel.
            Measures time series per sweep value:
                time_avg: average of sim execution times
                SE: standard error , see calc_channel_se_window method
                sim_speedup: base time / time for the given sweep value,
                MAD: mean absolute deviation, abs(value - base value)
                MAPE: MAD % where 100% is mean of base time series (channel times series for the base sweep value)
                IN1SE | IN2SE: % of values of channel mean time series which are within +/- of 1 | 2 SE around base line
                IO2SE: % of values (steps) of channel mean time series when 2 SE intervals are overlaping.
                KS: ks test showing distance of cumulatve distribution functions (CDF) for the given sweep value and the base sweep value and associated p-value
                """

        # df containing sim data for each sim
        # columns: step, node_id, Base_Individual_Sample_Rate, Run_Number, spatial_Population...
        # visual style map
        from itertools import cycle
        colors_iter = cycle(self.colors_all)
        sweep_values_map = {r: {'width': 4 if r == self.sweep_base_value else 2, 'color': next(colors_iter)} for r in
                            self.sweep_values}

        for r in self.sweep_values:
            sweep_values_map[r]['SE'] = np.nanmean(self.calc_channel_se_window(data_channel, r, do_rolling=True))

            # Avg. run time per sampling rate
            sweep_values_map[r]['time_avg'] = self.df_raw[self.df_raw[self.sweep_param] == r][
                'total_time'].unique().mean()

            # TODO: Spatial node measures: like measures avg. of per node measures, measures per population bin 100-500-1000, histogram of node values.
            # Avg. node std
            # sweep_param_std = '{}_std'.format(data_channel)
            # sweep_values_map[r]['node_count'] = self.node_count
            # sweep_values_map[r]['avg_node_std'] = self.df_raw[self.df_raw[self.sweep_param] == r][sweep_param_std].mean() if sweep_param_std in self.df_raw.columns else None

        total_steps = len(dfp.index)
        if total_steps > 0:
            dfp = np.round(dfp, 4)
            for r in self.sweep_values:
                base_time = sweep_values_map[self.sweep_base_value]['time_avg']
                r_time = sweep_values_map[r]['time_avg']
                sweep_values_map[r]['sim_speedup'] = base_time / r_time

                # MAD
                sweep_values_map[r]['MAD'] = (np.abs(dfp[self.sweep_base_value] - dfp[r])).mean()

                # MAPE
                base_values_mean = np.abs(dfp[self.sweep_base_value].mean())
                sweep_values_map[r]['MAPE'] = (100 * sweep_values_map[r][
                    'MAD']) / base_values_mean if base_values_mean != 0 else np.nan

                # % of values in 95% confidece interval, aprox. to 2 x SE (instead of 1.96)
                b1min, b1max, b2min, b2max = self.get_se_interval_col_names(self.sweep_base_value)

                sweep_values_map[r]['IN1SE'] = (100.0 * ((dfp[r] >= dfp[b1min]) & (dfp[r] <= dfp[b1max])).apply(
                    lambda x: 1 if x else 0).sum()) / total_steps
                sweep_values_map[r]['IN2SE'] = (100.0 * ((dfp[r] >= dfp[b2min]) & (dfp[r] <= dfp[b2max])).apply(
                    lambda x: 1 if x else 0).sum()) / total_steps

                r1min, r1max, r2min, r2max = self.get_se_interval_col_names(r)
                # adding 0.0001 to upper side to ensure that cases when SE is 0 (down/up values are equal) still counts as match
                sweep_values_map[r]['IO2SE'] = 100.0 * sum(dfp.apply(
                    lambda row: self.get_interval_overlap([row[b2min], row[b2max] + 0.0001],
                                                          [row[r2min], row[r2max] + 0.0001]) != 0.0,
                    axis=1)) / total_steps

                # KS test
                # K-S is small or p-value is high => cannot reject the hypothesis they are from the same distribution.
                sweep_values_map[r]['KS'] = stats.ks_2samp(dfp[self.sweep_base_value], dfp[r])
                sweep_values_map[r]['KS'] = np.round(sweep_values_map[r]['KS'], 4)

        return sweep_values_map

    def calc_channel_se_window(self, data_channel, sweep_value, run_number_count=None, do_rolling=False):
        """ Standard Error (SE) of sweep_value time series, calc as SD of means of different runs / sqrt(number of runs).
            run_number_count indicates how many runs to include in the calucation.
            Usage: calculate SE for summary measures and plots and Noise convergence bar plot.
            Returns SE time series.
        """

        # Number of runs to consider (used to measure noise vs. run count)
        rn = run_number_count or self.runs_count

        # Filter to rows for given sweep value and select columns (run number, step, channel)
        df_rs = self.df_raw[self.df_raw[self.sweep_param] == sweep_value]

        # only include specified number of runs
        df_rs = df_rs[df_rs['Run_Number'] <= rn]
        df_rs = df_rs.reset_index()
        df_rs = df_rs[['Run_Number', 'step', data_channel]]

        if self.debug:
            # SE calculation input
            sweep_label = self.get_file_name_sweep_label(data_channel, sweep_value)
            csv_path = self.get_result_path('data_calc_se_{}_input.csv'.format(sweep_label))
            df_rs.to_csv(csv_path, index=False)

        se_final = df_rs.groupby('step').std().fillna(df_rs.groupby('step').last())[data_channel] / np.sqrt(rn)

        if self.debug:
            # SE calculation output
            sweep_label = self.get_file_name_sweep_label(data_channel, sweep_value)
            csv_path = self.get_result_path('data_calc_se_{}final.csv'.format())
            pd.DataFrame(se_final, columns=['SE']).to_csv(csv_path, index=False)

        if do_rolling:
            se_final = self.rolling_mean(se_final)

        return se_final

    def init_measure_cache(self):
        """Measure cache, allows re-use of summary measures and plots. Initiates measure calculation."""
        self._measure_cache = {k: {'map': None, 'corr': None, 'plot': None} for k in self.inset_channel_names}

    def get_channel_measure_data(self, channel, run_number_count=None, ):
        """Get measure dataframe (channel mean unstacked by sweep vale, with confidence intervals)."""
        data_channel = 'inset_{}'.format(channel)

        base_se = self.calc_channel_se_window(data_channel, self.sweep_base_value, run_number_count=run_number_count)
        dfm = self.init_means_df(data_channel, run_number_count=run_number_count)
        dfp = self.init_unstacked_means_se_df(dfm, data_channel, base_se)

        return dfp

    def get_channel_summary_measures(self, channel):
        """Returns channel summary measures and plots. First call will caclulate and cache."""
        if self._measure_cache[channel]['map'] is None:
            data_channel = 'inset_{}'.format(channel)

            # dfp and dfps are not cached for scalability reasons
            dfp = self.get_channel_measure_data(channel)
            dfps = self.rolling_mean(dfp)
            sweep_values_map = self.init_sweep_values_map(dfps, data_channel)
            corr = dfps[self.sweep_values].corr().as_matrix()

            self._measure_cache[channel]['map'] = sweep_values_map
            self._measure_cache[channel]['corr'] = corr
            self._measure_cache[channel]['plot'] = self.plot_time_series_html(dfp, sweep_values_map, data_channel,
                                                                              do_rolling=True, is_visible=True)
            # plot the 'raw' version as well so that image exists but don't add it to html initially, it will be handled by javascirpt per user action
            self.plot_time_series_html(dfp, sweep_values_map, data_channel, do_rolling=False, is_visible=False)

            # Show how it los with fewer runs
            lower_run_count = self.get_lower_run_count()
            dfp2 = self.get_channel_measure_data(channel, lower_run_count)

            self._measure_cache[channel]['plot2'] = self.plot_time_series_html(dfp2, sweep_values_map, data_channel,
                                                                               do_rolling=True,
                                                                               lower_run_count=lower_run_count,
                                                                               is_visible=False)
            self.plot_time_series_html(dfp2, sweep_values_map, data_channel, do_rolling=False,
                                       lower_run_count=lower_run_count, is_visible=False)

        return self._measure_cache[channel]['map'], self._measure_cache[channel]['corr'], self._measure_cache[channel][
            'plot'], self._measure_cache[channel]['plot2']

    def get_lower_run_count(self):
        return max(int(self.runs_count / 3), 1)

    ### init dataframes

    def init_means_df(self, data_channel, run_number_count=None):
        """ Takes raw df and aggregates individual runs into means.
            Usage: in init_unstacked_means_se_df
            Returning df:
                index: step
                cols: sweep value, channel (runs) mean."""

        rn = run_number_count or self.runs_count

        dfr = self.df_raw[self.df_raw['Run_Number'] <= rn]

        # removing not needed columns and setting index
        dfm = dfr.groupby(['step', self.sweep_param], as_index=False).mean()

        for c in ['Run_Number', 'node_id']:
            if c in dfm.columns: del dfm[c]

        dfm = dfm.set_index('step')

        if self.debug:
            dfm.to_csv(self.get_result_path('data_groupby_step_sweep_param.csv'))

        return dfm

    def init_unstacked_means_se_df(self, dfm, data_channel, se, do_demaen=False):
        """ Takes channel means df and unstacks channel time series into 1 col per sweep value.
            Then adds confidence interval time series as additional columns (base sweep value +/- 1/2 SE).
            Usage: in plots: means of individual runs, individual runs
            Returning df:
                index: step
                cols: channel mean {sweep value 1},... channel mean {sweep value N}, '1se_down', '1se_up', '2se_down', '2se_up' """

        df_res = pd.DataFrame()

        for r in self.sweep_values:
            df_res[r] = dfm[dfm[self.sweep_param] == r][data_channel]

        if do_demaen:
            for r in self.sweep_values:
                df_res[r] = df_res[r] - df_res[r].mean()

        for r in self.sweep_values:
            df_res = self.df_add_se_interval(df_res, data_channel, r, se)

        if self.debug:
            df_res.to_csv(self.get_result_path('data_time_series_{}.csv'.format(data_channel)))

        return df_res

    def get_se_interval_col_names(self, col):
        """List of tupls: label, number of SE factor"""
        col_labels = ['1se_down', '1se_up', '2se_down', '2se_up']

        return ['{}_{}'.format(col, c) for c in col_labels]

    def init_base_mean_w_individual_runs_df(self, dfp, data_channel, sweep_value, lower_run_count):
        """ Constructs a dataframe containing base channel mean time series with confidence intervals and individual runs time series for (the given sweep value).
            Usage: Individual runs plots in the channel detail page.
            Returning df:
                index: step
                cols: base channel mean,'1se_down', '1se_up', '2se_down', '2se_up',  channel run 1, ...channel run N
        """

        # take  base channel mean, '1se_down', '1se_up', '2se_down', '2se_up' from dfp
        cols = [self.sweep_base_value] + self.get_se_interval_col_names(self.sweep_base_value)
        df_base = dfp[cols]

        # take raw data for the given sweep value
        dfr = self.df_raw[self.df_raw['Run_Number'] <= lower_run_count]
        df = dfr[['step', 'Run_Number', self.sweep_param, data_channel]]
        df = df[df[self.sweep_param] == sweep_value]

        # TODO: del df[self.sweep_param], pivot or unstack without self.sweep_param, use input sweep_value arg to name columns

        # unstack so that there is 1 column for each run
        dfpv = df.pivot_table(index='step', columns=[self.sweep_param, 'Run_Number'], values=[data_channel],
                              aggfunc='first')

        # rename columns to follow the pattern "sweep value {run}"
        dfpv.columns = [(c[1], int(c[2])) for c in dfpv.columns.values]

        if len(df_base) > 0 and len(dfpv) > 0 and len(df_base) != len(dfpv):
            raise Exception("Cannot join dataframes because time series differ in length.")

        dfmpv = pd.merge(dfpv, df_base, how='inner', left_index=True, right_index=True)

        if len(df_base) > 0 and len(dfmpv) > 0 and len(df_base) != len(dfmpv):
            raise Exception('The dataframe length after join differs from the control dataframe.')

        return dfmpv

    def init_se_df(self, data_channel):
        """ Construct a dataframe containing SE time series for each sweep value and number of runs included.
            Usage: Noise convergence bar plot, showing how SE decreases as more and more runs are included in calculation.
            Returning df:
                index: None
                cols: step, sweep value, run number count, SE
                """

        df_se = pd.DataFrame()

        for sv in self.sweep_values:
            for rn in range(2, self.runs_count + 1):
                # SE for the give number or runs
                se_final = self.calc_channel_se_window(data_channel, sv, run_number_count=rn, do_rolling=True)
                df_se_tmp = pd.DataFrame(
                    {'step': self.steps, self.sweep_param: sv, 'run_number_count': rn, 'SE': se_final})
                df_se = pd.concat([df_se, df_se_tmp])

        return df_se

    def init_perf_df(self):
        """ Constructs a dataframe which show, for each sweep value, what is the mean sim execution times and speed up mulitple.
            Usage: top pane speed up table.
            Returning df:
                index: labels
                cols: sweep values...
            """
        df_times = self.df_raw[[self.sweep_param, 'Run_Number', 'total_time']].groupby(
            [self.sweep_param]).mean()  # , as_index=False
        del df_times['Run_Number']
        base_time = df_times.loc[self.sweep_base_value].iloc[0]
        time_col = 'sim time (s)'
        df_times.columns = [time_col]
        df_times['sim speedup (x)'] = base_time / df_times[time_col]
        # sort by sweep value
        df_times = df_times.sort_index(ascending=self.is_sweep_ascending())

        # transpose to get labels as index and sweep values as columns
        return df_times.T

    def init_measures_summary_df(self, corr_matrix, sweep_values_map, categories=None):
        """ Constructs measure summary dataframe so that index are measure names and columsn are sweep values.
            Usage: measure summary in sumamry page, channel measure summary in summary and channel detail pages
            Returning df:
                index: labels
                cols: sweep values
        """
        cols = self.sweep_values + ['category']
        row = [sweep_values_map[r]['SE'] for r in self.sweep_values] + ['se']
        df_measures = pd.DataFrame(data=[row], columns=cols, index=[['standard error (SE)']])

        df_measures.loc[self._measure_names['IN1SE']] = [int(sweep_values_map[r]['IN1SE']) for r in
                                                         self.sweep_values] + ['se']
        df_measures.loc[self._measure_names['IN2SE']] = [int(sweep_values_map[r]['IN2SE']) for r in
                                                         self.sweep_values] + ['se']
        df_measures.loc[self._measure_names['IO2SE']] = [int(sweep_values_map[r]['IO2SE']) for r in
                                                         self.sweep_values] + ['se']
        df_measures.loc[self._measure_names['MAD']] = [sweep_values_map[r]['MAD'] for r in self.sweep_values] + ['dist']
        df_measures.loc[self._measure_names['MAPE']] = [sweep_values_map[r]['MAPE'] for r in self.sweep_values] + [
            'dist']
        df_measures.loc[self._measure_names['CORR']] = [corr_matrix[0, j] for j in range(len(self.sweep_values))] + [
            'corr']
        df_measures.loc[self._measure_names['KS']] = [sweep_values_map[r]['KS'] for r in self.sweep_values] + ['prob']

        if categories is not None:
            df_measures = df_measures[df_measures['category'].isin(categories)]

        return df_measures

    ### dataframe helpers

    def rolling_mean(self, dfp):
        """Rolling-mean on the given dataframe using report default rolling window size."""
        # min_periods = 1 ensures that resutling dataframe doesn't contain NaN values at the begining.
        dfps = dfp.rolling(self.rolling_win_size, min_periods=1, center=False).mean()

        return dfps

    def df_add_se_interval(self, df, data_channel, col, se):
        """Adds confidence interval columns by adding +|- 1|2 SE around specified col."""

        col_names = self.get_se_interval_col_names(col)
        cols_info = zip(col_names, [-1, 1, -2, 2])

        # shade 1 and 2 SE around the base line (sampling rate 1)
        for t in cols_info:
            df[t[0]] = [tt[0] + tt[1] for tt in zip(df[col], [v * t[1] for v in se])]

        df['SE'] = se

        return df

    ### plotting

    def plot_time_series_html(self, dfp, sweep_values_map, data_channel, do_rolling=False, lower_run_count=None,
                              is_visible=True):
        # TODO: consider the edge case when lower_run_count == self.runs_count and prevent dup plots.
        rn = lower_run_count or self.runs_count
        html = ''
        channel = data_channel.replace('inset_', '')

        plot_path = self.get_result_path('{}_cp_w_base_means_time_series{}.png'.format(
            self.get_file_name_sweep_label(data_channel, self.sweep_base_value, rn), '_rolling' if do_rolling else ''))
        f = plt.figure(figsize=(14, 3))
        if do_rolling:
            dfp = self.rolling_mean(dfp)
        self.plot_lines(dfp, sweep_values_map, channel)

        html += self.save_close_report_plot(plot_path, f, is_visible)

        return html

    def plot_time_series_interval_compare_html(self, dfp, sweep_values_map, data_channel, sweep_value_to_compare,
                                               do_rolling=False, lower_run_count=None, is_visible=True):
        rn = lower_run_count or self.runs_count
        html = ''
        channel = data_channel.replace('inset_', '')

        plot_path = self.get_result_path('{}_cp_w_base_means_time_series{}.png'.format(
            self.get_file_name_sweep_label(data_channel, sweep_value_to_compare, rn), '_rolling' if do_rolling else ''))

        f = plt.figure(figsize=(14, 3))
        if do_rolling:
            dfp = self.rolling_mean(dfp)

        self.plot_lines(dfp, sweep_values_map, channel, sweep_value_to_compare)

        html += self.save_close_report_plot(plot_path, f, is_visible)

        return html

    def plot_time_series_individual_runs_html(self, dfp, sweep_values_map, data_channel, sweep_value, do_rolling=False,
                                              lower_run_count=None, is_visible=True):
        rn = lower_run_count or self.runs_count
        html = ''
        channel = data_channel.replace('inset_', '')

        plot_path = self.get_result_path(
            '{}_ind_runs_time_series{}.png'.format(self.get_file_name_sweep_label(data_channel, sweep_value, rn),
                                                   '_rolling' if do_rolling else ''))

        dfmpv = self.init_base_mean_w_individual_runs_df(dfp, data_channel, sweep_value, rn)

        # 1.0, 1se_down, 1se_up, 2se_down, 2se_up, 0.3 (1), 0.3 (2)...
        value_map = {
            self.sweep_base_value: {
                'color': sweep_values_map[self.sweep_base_value]['color'],
                'width': sweep_values_map[self.sweep_base_value]['width']}
        }

        run_keys = [(sweep_value, r) for r in range(1, self.nruns + 1)]
        for k in run_keys:
            value_map[k] = {
                'color': sweep_values_map[sweep_value]['color'],
                'width': 1
            }

        f = plt.figure(figsize=(14, 3))
        if do_rolling:
            dfmpv = self.rolling_mean(dfmpv)

        ax = self.plot_lines(dfmpv, value_map, channel)
        handles, labels = ax.get_legend_handles_labels()
        labels2 = [self.sweep_base_value, str(run_keys[0][0])]
        handles2 = [[h for h in handles if h._label == str(self.sweep_base_value)][0],
                    [h for h in handles if h._label.startswith('(')][0]]
        ax.legend(handles2, labels2, loc='best')

        html += self.save_close_report_plot(plot_path, f, is_visible)

        return html

    def plot_time_series_zoom_end_html(self, dfp, sweep_values_map, data_channel, w=0.1, do_rolling=False):
        """Plots last 10% percent of the dataframe (or percent specified by w input argument)."""
        html = ''
        channel = data_channel.replace('inset_', '')

        plot_path = self.get_result_path(
            '{}_zoom_to_end_time_series{}.png'.format(data_channel, '_rolling' if do_rolling else ''))
        f = plt.figure(figsize=(14, 3))

        if do_rolling:
            dfp = self.rolling_mean(dfp)

        zoom_min = dfp.index.min()
        zoom_max = dfp.index.max()
        zoom_min = zoom_max - w * (zoom_max - zoom_min + 1)

        dfp_zoom = dfp[(dfp.index >= zoom_min) & (dfp.index <= zoom_max)]
        self.plot_lines(dfp_zoom, sweep_values_map, channel)

        html += self.save_close_report_plot(plot_path, f)

        return html

    def plot_se_vs_runs_html(self, sweep_values_map, data_channel):
        """Plots noise (SE) convergence bar chrat showing how SE decreases as more runs are considered."""
        # TODO: recommend how many runs is enough

        html = ''

        f = plt.figure()
        ax = f.gca()

        plot_path = self.get_result_path('{}_se_vs_runs_means.png'.format(data_channel))

        ax.set_xlabel('number of runs considered')

        df_se = self.init_se_df(data_channel)
        df_se_g = df_se.groupby([self.sweep_param, 'run_number_count'], as_index=False).mean()
        del df_se_g['step']
        df_se_g = df_se_g.pivot(index='run_number_count', columns=self.sweep_param, values='SE')

        bar_colors = list(reversed(self.colors_all[:len(self.sweep_values)]))
        df_se_g.plot(kind='bar', color=bar_colors, figsize=(14, 3), ax=ax)

        if self.is_sweep_ascending():
            handles, labels = ax.get_legend_handles_labels()
            labels2 = reversed(labels)
            ax.legend(handles, labels2, loc='best')

        ax.set_xlabel('runs')
        ax.set_ylabel('Noise (SE) Means')
        ax.grid(True)

        html += self.save_close_report_plot(plot_path, f)

        return html

    def plot_corr_html(self, dfp, sweep_values_map, data_channel):
        html = ''
        if len(self.sweep_values) > 1:
            # Correlation
            corr = dfp[self.sweep_values].corr().as_matrix()

            html += '<h3>Correlation with Base Time Series</h3>'
            plot_path = self.get_result_path('{}_corr_scatter.png'.format(data_channel))

            f, axs = plt.subplots(1, len(self.sweep_values) - 1, squeeze=False)
            axs = axs.flatten()
            f.set_size_inches((14, 2))

            for r in self.sweep_values:
                if r == self.sweep_base_value: continue
                color = sweep_values_map[r]['color']
                j = self.sweep_values.index(r) - 1
                axs[j].scatter(dfp[self.sweep_base_value], dfp[r],
                               color=color)  # ax=axs[i], bins=20, color=sweep_values_map[sweep_values[i]]['color'])
                axs[j].grid(True)
                # ensure that scientific notation is NOT used to label axes
                axs[j].get_xaxis().get_major_formatter().set_useOffset(False)
                axs[j].get_yaxis().get_major_formatter().set_useOffset(False)
                # writes corr value on the plot
                axs[j].annotate('{}'.format(np.round(corr[0, j + 1], 4)), (0.5, 0.9), xycoords='axes fraction',
                                ha='center', va='center')
                axs[j].set_xlabel(r)
                axs[j].set_ylabel(self.sweep_base_value)

            html += self.save_close_report_plot(plot_path, f)

        return html

    def plot_kde_html(self, dfp, sweep_values_map, data_channel):
        channel = data_channel.replace('inset_', '')
        if len(self.sweep_values) > 1:
            html = '<h3>Kernel Density Estimation (KDE)</h3>'
            html += 'KDE is a non-parametric way to estimate the probability density function (PDF) of a random variable.<br>'
            html += 'PDF is used to specify the probability (area under the function) of the random variable falling within a particular range.<br>'

            plot_path = self.get_result_path('{}_kde.png'.format(data_channel))

            f = plt.figure(figsize=(14, 3))
            ax = f.gca()
            ax.get_xaxis().get_major_formatter().set_useOffset(False)
            ax.get_yaxis().get_major_formatter().set_useOffset(False)
            ax.set_xlabel(channel)

            for i in range(len(self.sweep_values)):
                r = self.sweep_values[i]
                if dfp[r].std() == 0: continue
                dfp[r].plot.kde()
                color = sweep_values_map[r]['color']
                width = sweep_values_map[r]['width']
                if len(ax.lines) <= i:
                    html += '<div>Warning: Unable to generate KDE plot due to low variation.</div>'
                    break
                ax.lines[i].set_color(color)
                ax.lines[i].set_linewidth(width)

            ax.grid(True)
            ax.legend(loc='best')

            html += self.save_close_report_plot(plot_path, f)

        return html

    def plot_histogram_html(self, dfp, sweep_values_map, data_channel):
        html = ''  # ''<h2>Histogram</h2>'
        channel = data_channel.replace('inset_', '')
        plot_path = self.get_result_path('{}_hist_all.png'.format(data_channel))

        f = plt.figure(figsize=(14, 3))
        # histogram of all sweep values on the same plot
        dfp[self.sweep_values].plot.hist(ax=f.gca(), bins=60,
                                         color=[sweep_values_map[k]['color'] for k in self.sweep_values])
        ax = f.gca()
        # ensure that scientific notation is NOT used to label axes
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        ax.get_yaxis().get_major_formatter().set_useOffset(False)
        ax.grid(True)
        ax.set_xlabel(channel)

        self.set_ax_labels(ax)

        hist_ymax = f.gca().dataLim.max[1]

        html += self.save_close_report_plot(plot_path, f) + '<br>'

        if len(self.sweep_values) > 1:
            plot_path = self.get_result_path('{}_hist_separate.png'.format(data_channel))

            # separate histogram plots for each sweep value
            f, axs = plt.subplots(1, len(self.sweep_values), squeeze=False)
            axs = axs.flatten()
            f.set_size_inches((14, 2))

            for i in range(len(self.sweep_values)):
                dfp[self.sweep_values[i]].plot.hist(ax=axs[i], bins=20,
                                                    color=sweep_values_map[self.sweep_values[i]]['color'])
                axs[i].grid(True)
                axs[i].set_ylim(0, hist_ymax)
                axs[i].get_xaxis().get_major_formatter().set_useOffset(False)
                axs[i].get_yaxis().get_major_formatter().set_useOffset(False)
                axs[i].set_xlabel('{} ({})'.format(channel, self.sweep_values[i]))

            html += self.save_close_report_plot(plot_path, f)

        return html

    def plot_nodes_histogram_html(self, dfp, sweep_values_map, data_channel):
        html = '<h3>Spatial Node Histogram</h3>'
        html += '<i>Coming soon...</i>'

        return html

    def plot_lines(self, df_tp, sweep_values_map, channel='', sweep_value_to_compare=None):
        """Plots time series using specified colors and line widths. Also, shades confidence interval areas"""
        is_compare = sweep_value_to_compare is not None
        sweep_values_to_plot = [self.sweep_base_value,
                                sweep_value_to_compare] if is_compare else sweep_values_map.keys()
        # set color and width
        for k in sweep_values_to_plot:
            if k in df_tp.columns:
                plt.plot(df_tp[k], color=sweep_values_map[k]['color'], linewidth=sweep_values_map[k]['width'])

        ax = plt.gca()
        # ensure that scientific notation is NOT used to label axes
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        ax.get_yaxis().get_major_formatter().set_useOffset(False)
        ax.set_xlabel('step')
        ax.set_ylabel(channel)
        ax.grid(True)
        self.set_ax_labels(ax)

        sweep_values_w_interval = [self.sweep_base_value, sweep_value_to_compare] if is_compare else [
            self.sweep_base_value]

        for r in sweep_values_w_interval:
            se_int_cols = self.get_se_interval_col_names(r)
            if se_int_cols[0] in df_tp.columns.values:
                color = sweep_values_map[r]['color']
                if not is_compare:
                    plt.fill_between(df_tp.index, df_tp[se_int_cols[0]], df_tp[se_int_cols[1]],
                                     where=df_tp[se_int_cols[0]] < df_tp[se_int_cols[1]],
                                     facecolor=color, alpha=0.2, interpolate=True)
                plt.fill_between(df_tp.index, df_tp[se_int_cols[2]], df_tp[se_int_cols[3]],
                                 where=df_tp[se_int_cols[2]] < df_tp[se_int_cols[3]],
                                 facecolor=color, alpha=0.1, interpolate=True)

        return ax

    ### helper dicts and methods

    def df_html_summary_args(self, decimals=2):
        """Arguments needed for transforming df into HTML."""
        return {'classes': 'summary', 'float_format': lambda x: '%.{}f'.format(decimals) % x}

    def get_file_name_sweep_label(self, data_channel, sweep_value, run_number=None):
        lbl = '{}_sw{}'.format(data_channel, sweep_value)
        if run_number is not None:
            lbl += '_rn{}'.format(run_number)

        return lbl

    def get_result_path(self, name):
        return os.path.join(self.report_dir_path, name)

    def save_close_report_plot(self, plot_path, fig=None, is_visible=True):
        plt.savefig(plot_path, bbox_inches='tight')

        if fig:
            plt.close(fig)

        plot_html = "<img src='{}' style='display: {}'/>".format(os.path.basename(plot_path),
                                                                 '' if is_visible else 'none')

        return plot_html

    def set_ax_labels(self, ax):
        """Sorts and formats labels."""
        is_rev = True
        handles, labels = ax.get_legend_handles_labels()
        if all([self.is_float(v) for v in labels]):
            labels = [float(v) for v in labels]
            if all([int(v) == float(v) for v in labels]):
                labels = [int(v) for v in labels]

            is_rev = not self.is_sweep_ascending()

        labels2 = sorted(labels, reverse=is_rev)
        handles2 = [handles[labels.index(lab)] for lab in labels2]

        ax.legend(handles2, labels2, loc='best')

    def is_sweep_ascending(self):
        return self.sweep_base_value == min(self.sweep_values)

    @staticmethod
    def is_float(value):
        try:
            float(value)
            return True
        except:
            return False

    @staticmethod
    def get_interval_overlap(a, b):
        # https://stackoverflow.com/questions/2953967/built-in-function-for-computing-overlap-in-python
        return max(0, min(a[1], b[1]) - max(a[0], b[0]))
