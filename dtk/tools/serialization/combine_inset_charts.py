import json
import argparse
import os.path as path

CHANNELS_KEY = "Channels"
INSETCHART_NAME = "InsetChart.json"
PROPERTYCHART_NAME = "PropertyReport.json"
METADATA_KEY = "Header"
DATA_KEY = "Data"
UNITS_KEY = "Units"
TIMESTEPS_KEY = "Timesteps"
STARTTIME_KEY = "Start_Time"

CUMULATIVE_CHANNELS = ["Births","Campaign Cost","Cumulative Infections","Cumulative Reported Infections", "Disease Deaths"]


def ping():
    """
    Method to validate that this script has been imported and is accessible
    """
    print("File {0} is here!".format(__name__))


def define_arguments(parser=argparse.ArgumentParser()):
    """
    Method that sets up the argparse parser for easier argument testing

    :param parser: ArgumentParser (argparse.ArgumentParser())
    :return: parser with arguments defined
    """
    parser.add_argument("-s", "--serialized", help="Folder with serialized output")
    parser.add_argument("--serializedchartname", help="Serialized chart name (InsetChart.json)", default=INSETCHART_NAME)
    parser.add_argument("-r", "--reload", help="Folder with reloaded output")
    parser.add_argument("--reloadedchartname", help="Reloaded chart name (InsetChart.json)", default=INSETCHART_NAME)
    parser.add_argument("-o", "--output", help="Name of file to generate (combined_insetchart.json)", default="combined_insetchart.json")
    return parser


def combine_channels(serialized_insetchart_name, reloaded_insetchart_name):
    """
    Given the full path and name of two insetchart.json files, combines them into one file.
    This is for validating that serialized and reloaded simulations compare favorably with
    simulations that were run all at once. This has been validated for generic, vector, and malaria simulations

    :param serialized_insetchart_name: path and name of the insetchart from the simulation that serialized and stopped
    :param reloaded_insetchart_name: path and name of the insetchart generated from the reloaded simulation
    :return: json object representing the full insetchart with metadata
    """
    reloaded_metadata = None
    serialized_timesteps = -1
    with open(serialized_insetchart_name) as infile:
        serialized_insetchart = json.load(infile)
        channels_s = serialized_insetchart[CHANNELS_KEY]
        serialized_timesteps = serialized_insetchart[METADATA_KEY][TIMESTEPS_KEY]
        serialized_starttime = serialized_insetchart[METADATA_KEY][STARTTIME_KEY]
    with open(reloaded_insetchart_name) as infile:
        reloaded_insetchart = json.load(infile)
        channels_r = reloaded_insetchart[CHANNELS_KEY]
        reloaded_metadata = reloaded_insetchart[METADATA_KEY]

    # First, make sure the keys are the same
    if sorted(channels_s.keys()) != sorted(channels_r.keys()):
        err_msg_template = "InsetCharts have different keys.  Serialized has: {0}  Reloaded has: {1}"
        raise ValueError(err_msg_template.format(channels_s.keys(), channels_r.keys()))

    combined_insetchart = {}
    combined_insetchart[CHANNELS_KEY] = {}
    for key in channels_s.keys():
        combined_channel_object = {}
        serialized_channel = channels_s[key]
        combined_channel_object = serialized_channel
        data_r = None
        reloaded_data = channels_r[key][DATA_KEY]
        is_cumulative_channel = False
        for channel in CUMULATIVE_CHANNELS:
            if key.startswith(channel):
                is_cumulative_channel = True
                break
        if not is_cumulative_channel:
            data_r = reloaded_data
        else:
            temp_channel = []
            s_cumulative_final = channels_s[key][DATA_KEY][-1]
            for item in reloaded_data:
                temp_channel.append(item + s_cumulative_final)
            data_r = temp_channel
        combined_channel_object[DATA_KEY] += data_r
        combined_insetchart[CHANNELS_KEY][key] = combined_channel_object

    combined_metadata = make_combined_metadata(reloaded_metadata, serialized_timesteps, serialized_starttime)
    combined_insetchart[METADATA_KEY] = combined_metadata
    return combined_insetchart


def make_combined_metadata(reloaded_metadata, serialized_timesteps, serialized_starttime):
    """
    Attempts to make a metadata object representing the two combined insetcharts

    {"DateTime":"Tue Mar  7 09:35:14 2017","DTK_Version":"2662 master (29a4e55) Mar  7 2017 05:09:06",
    "Report_Type":"InsetChart","Report_Version":"3.2","Start_Time":0,"Simulation_Timestep":1,
    "Timesteps":90,"Channels":17}
    :return:
    """
    total_timesteps = reloaded_metadata[TIMESTEPS_KEY]
    total_timesteps += serialized_timesteps
    combined_metadata = reloaded_metadata
    combined_metadata[TIMESTEPS_KEY] = total_timesteps
    combined_metadata[STARTTIME_KEY] = serialized_starttime
    return combined_metadata

def combine_charts(serialized_chart_path, reloaded_chart_path, output_filename,
                   serialized_chart_name=INSETCHART_NAME, reloaded_chart_name=INSETCHART_NAME,
                   is_insetchart=True, compact=False):
    if is_insetchart:
        serialized_chart_name = path.join(serialized_chart_path, serialized_chart_name)
        reloaded_chart_name = path.join(reloaded_chart_path, reloaded_chart_name)
    else:
        serialized_chart_name = path.join(serialized_chart_path, PROPERTYCHART_NAME)
        reloaded_chart_name = path.join(reloaded_chart_path, PROPERTYCHART_NAME)
    smush = combine_channels(serialized_chart_name, reloaded_chart_name)
    with open(output_filename, 'w') as outfile:
        if compact:
            json.dump(smush, outfile)
        else:
            json.dump(smush, outfile, indent=4, sort_keys=True)


if __name__ == "__main__":
    parser = define_arguments()
    args = parser.parse_args()
    serialized_chart_name = path.join(args.serialized, args.serializedchartname)
    reloaded_chart_name = path.join(args.reload, args.reloadedchartname)
    smush = combine_channels(serialized_chart_name, reloaded_chart_name)
    with open(args.output, "w") as outfile:
        json.dump(smush, outfile, indent=4, sort_keys=True)

    serialized_property_chart_name = path.join(args.serialized, PROPERTYCHART_NAME)
    reloaded_property_chart_name = path.join(args.reload, PROPERTYCHART_NAME)
    if path.isfile(serialized_property_chart_name) and path.isfile(reloaded_property_chart_name):
        smush = combine_channels(serialized_property_chart_name, reloaded_property_chart_name)
        with open("combined_property_chart.json","w") as outfile:
            json.dump(smush, outfile, indent=4, sort_keys=True)
