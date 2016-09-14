import os

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer


class DownloadAnalyzer(BaseAnalyzer):
    # Specify here all the files needed to be downloaded for a given simulation
    filenames = ['output/InsetChart.json']

    # Specifies the path of the output directory
    output_path = "output"

    def __init__(self, output_path=None, filenames=None):
        if output_path:
            self.output_path = output_path

        if filenames:
            self.filenames = filenames

        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

    def apply(self, parser):
        # Create a folder for the current simulation
        sim_folder = os.path.join(self.output_path, parser.sim_id)
        if not os.path.exists(sim_folder):
            os.mkdir(sim_folder)

        # Create the requested files
        for filename in self.filenames:
            out_filename = filename.replace('/','-').replace('\\','-')
            with open(os.path.join(sim_folder,out_filename),'w') as handle:
                handle.write(str(parser.raw_data[filename]))
