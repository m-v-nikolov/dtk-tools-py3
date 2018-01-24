import json
import os
from io import BytesIO

from simtools.Analysis.BaseAnalyzers.BaseAnalyzer import BaseAnalyzer


class DownloadAnalyzer(BaseAnalyzer):
    """
    Download Analyzer
    A simple base class that will download the files specified in filenames without further treatment.

    Can be used by creating a child class:

    .. code-block:: python

        class InsetDownloader(DownloadAnalyzer):
            filenames = ['output/InsetChart.json']

    Or by directly calling it:

    .. code-block:: python

        analyzer = DownloadAnalyzer(filenames=['output/InsetChart.json'])

    """
    def __init__(self, filenames=None, output_path=None):
        super(DownloadAnalyzer, self).__init__()

        # Process the output_path
        self.output_path = output_path or "output"

        # We only want the raw files -> disable parsing
        self.parse = False

        if filenames:
            self.filenames = filenames

    def initialize(self):
        self.output_path = os.path.join(self.working_dir, self.output_path)

        # Create the output path
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def get_sim_folder(self, sim_id):
        """
        Concatenate the specified top-level output folder with the simulation ID
        :param parser: A simulation output parsing thread
        :return: The name of the folder to download this simulation's output to
        """
        return os.path.join(self.output_path, sim_id)

    def select_simulation_data(self, data,simulation):
        # Create a folder for the current simulation
        sim_folder = self.get_sim_folder(simulation.id)
        if not os.path.exists(sim_folder):
            os.makedirs(sim_folder)
        # Create the requested files
        for filename in self.filenames:
            file_path = os.path.join(sim_folder, os.path.basename(filename))
            with open(file_path, 'w') as outfile:
                if isinstance(data[filename], BytesIO):
                    outfile.write(data[filename].read())
                else:
                    json.dump(data[filename], outfile)
