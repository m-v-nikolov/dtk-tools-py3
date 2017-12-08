import unittest
import argparse
import json
import os.path as path
import os
import dtk.tools.serialization.combine_inset_charts as cmb
import dtk.tools.serialization.ks_channel_testing as kst

PLAIN_CHART = "InsetChart.json"
START_CHART = "InsetChart_start.json"
END_CHART = "InsetChart_end.json"
FULL_CHART = "InsetChart_full.json"
COMBINED_CHART = "combined_insetchart.json"

SERIALIZED_FOLDER = "serialized_output"
RELOADED_FOLDER = "reloaded_output"

class CombineInsetChartTests(unittest.TestCase):
    def setUp(self):
        local_parser = argparse.ArgumentParser()
        self.parser = cmb.define_arguments(local_parser)
        self.flags = []
        self.expected_new_files = []
        pass

    def tearDown(self):
        self.flags = []
        for potential_file in self.expected_new_files:
            if path.isfile(potential_file):
                os.unlink(potential_file)

    # <editor-fold desc="set flags for arguments">
    def set_serialized_flags(self, from_folder=True):
        self.flags.append('-s')
        if from_folder:
            self.flags.append(SERIALIZED_FOLDER)
        else:
            self.flags.append('.')

    def set_reloaded_flags(self, from_folder=True):
        self.flags.append('-r')
        if from_folder:
            self.flags.append(RELOADED_FOLDER)
        else:
            self.flags.append('.')

    def set_default_chartname_flags(self, plain_names=False):
        self.flags.append('--serializedchartname')
        if plain_names:
            self.flags.append(PLAIN_CHART)
        else:
            self.flags.append(START_CHART)

        self.flags.append('--reloadedchartname')
        if plain_names:
            self.flags.append(PLAIN_CHART)
        else:
            self.flags.append(END_CHART)

    def set_output_filename(self, filename):
        self.flags.append('-o')
        self.flags.append(filename)
    # </editor-fold>

    def get_args(self):
        return self.parser.parse_args(self.flags)

    def verify_expected_files(self, expect_created=True):
        for potential_file in self.expected_new_files:
            self.assertEqual(expect_created, path.isfile(potential_file))

    def args_combine_charts_all_remote_output_tofull(self, custom_filename, plain_names=False):
        combined_path = path.join('.', custom_filename)
        self.expected_new_files.append(combined_path)
        self.verify_expected_files(False)
        self.set_output_filename(custom_filename)
        self.set_default_chartname_flags(plain_names)
        self.set_reloaded_flags(from_folder=True)
        self.set_serialized_flags(from_folder=True)
        return self.get_args()

    def args_combine_charts_all_local_default_output(self):
        combined_path = path.join('.', COMBINED_CHART)
        self.expected_new_files.append(combined_path)
        self.verify_expected_files(False)
        self.set_serialized_flags(from_folder=False)
        self.set_reloaded_flags(from_folder=False)
        self.set_default_chartname_flags()
        return self.get_args()

    def create_ks_tester_custom(self, reference_chart_path, test_chart_path, channel_list):
        k_t = kst.KsChannelTester(reference_chart_path, test_chart_path, channel_list)
        return k_t

    def verify_charts_combined(self, start_chart, end_chart, combined_chart):
        start_keys = sorted(start_chart["Channels"].keys())
        combined_keys = sorted(combined_chart["Channels"].keys())
        self.assertEqual(len(start_keys), len(combined_keys))
        for key in start_keys:
            self.assertTrue(key in combined_keys)
        start_channel_length = len(start_chart["Channels"]["Infected"]["Data"])
        end_channel_length = len(end_chart["Channels"]["Infected"]["Data"])
        combined_channel_length = len(combined_chart["Channels"]["Infected"]["Data"])
        self.assertEqual(combined_channel_length, start_channel_length + end_channel_length)

    def test_args_AllLocalDefaultOutput(self):
        args = self.args_combine_charts_all_local_default_output()
        self.assertEquals(args.serialized, '.')
        self.assertEquals(args.reload, '.')
        self.assertEquals(args.output, COMBINED_CHART)

    def combine_charts_default(self):
        args = self.args_combine_charts_all_local_default_output()
        cmb.combine_charts(args.serialized,
                           args.reload,
                           args.output,
                           serialized_chart_name=args.serializedchartname,
                           reloaded_chart_name=args.reloadedchartname)

    def test_combination_AllLocalDefaultOutput(self):
        self.combine_charts_default()
        self.verify_expected_files(True)
        with open(self.expected_new_files[0]) as infile:
            combined_chart = json.load(infile)
        start_chart_path = path.join(SERIALIZED_FOLDER, START_CHART)
        end_chart_path = path.join(RELOADED_FOLDER, END_CHART)
        with open(start_chart_path) as infile:
            start_chart = json.load(infile)
        with open(end_chart_path) as infile:
            end_chart = json.load(infile)
        self.verify_charts_combined(start_chart, end_chart, combined_chart)

    def test_kstest_combined_charts_allgood(self):
        self.combine_charts_default()
        full_chart_path = os.path.join('.', FULL_CHART)
        combined_chart_path = self.expected_new_files[0]
        test_channels = ["Infected","New Infections",
                         "Disease Deaths","Campaign Cost",
                         "Statistical Population"]
        k_t = self.create_ks_tester_custom(reference_chart_path=full_chart_path,
                                           test_chart_path=combined_chart_path,
                                           channel_list=test_channels)
        for channel in test_channels:
            stat, pvalue = k_t.test_channel(channel_name=channel)
            # print ("Channel is: {0}".format(channel))
            # print ("Stat is: {0}".format(stat))
            # print ("P_Value is: {0}".format(pvalue))
            self.assertGreater(pvalue, 0.05)
            self.assertLess(stat, 0.20)

    def test_kstest_populate_bad_channel(self):
        self.combine_charts_default()
        full_chart_path = os.path.join('.', FULL_CHART)
        combined_chart_path = self.expected_new_files[0]
        bad_channel_name = "booty" #https://youtu.be/dptNvn4_BnU?t=22s
        test_channels = ["Infected","New Infections",
                         "Disease Deaths",bad_channel_name,
                         "Statistical Population"]
        with self.assertRaises(ValueError) as context:
            self.create_ks_tester_custom(reference_chart_path=full_chart_path,
                                         test_chart_path=combined_chart_path,
                                         channel_list=test_channels)
        self.assertTrue(bad_channel_name in str(context.exception))
        self.assertTrue(test_channels[0] in str(context.exception))

    def test_kstest_request_bad_channel(self):
        self.combine_charts_default()
        full_chart_path = os.path.join('.', FULL_CHART)
        combined_chart_path = self.expected_new_files[0]
        bad_channel_name = "booty"
        test_channels = ["Infected","New Infections"]
        k_t = self.create_ks_tester_custom(reference_chart_path=full_chart_path,
                                           test_chart_path=combined_chart_path,
                                           channel_list=test_channels)
        with self.assertRaises(KeyError) as context:
            k_t.test_channel(bad_channel_name)
        self.assertTrue(bad_channel_name in context.exception)

    def test_args_AllFolderCustomOutput(self):
        custom_filename = "funny_insetchart.json"
        args = self.args_combine_charts_all_remote_output_tofull(custom_filename)
        self.assertEquals(args.serialized, SERIALIZED_FOLDER)
        self.assertEqual(args.reload, RELOADED_FOLDER)
        self.assertEqual(args.output, custom_filename)

    def test_args_AllFolderPlainNamesCustomOutput(self):
        custom_filename = "funny_insetchart.json"
        args = self.args_combine_charts_all_remote_output_tofull(custom_filename, plain_names=True)
        self.assertEquals(args.serialized, SERIALIZED_FOLDER)
        self.assertEqual(args.reload, RELOADED_FOLDER)
        self.assertEqual(args.output, custom_filename)

    def test_combination_AllFolderCustomOutput(self):
        custom_filename = "funny_insetchart.json"
        args = self.args_combine_charts_all_remote_output_tofull(custom_filename)
        cmb.combine_charts(args.serialized,
                           args.reload,
                           args.output,
                           serialized_chart_name=args.serializedchartname,
                           reloaded_chart_name=args.reloadedchartname)
        self.verify_expected_files(True)

        serialized_chartname = path.join(SERIALIZED_FOLDER, START_CHART)
        reloaded_chartname = path.join(RELOADED_FOLDER, END_CHART)
        with open(self.expected_new_files[0]) as infile:
            combined_chart = json.load(infile)
        with open(serialized_chartname) as infile:
            start_chart = json.load(infile)
        with open(reloaded_chartname) as infile:
            end_chart = json.load(infile)
        self.verify_charts_combined(start_chart, end_chart, combined_chart)





