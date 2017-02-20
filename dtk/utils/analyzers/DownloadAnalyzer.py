import os

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer


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
    def __init__(self, output_path=None, filenames=None):
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
            os.mkdir(self.output_path)

    def apply(self, parser):
        # Create a folder for the current simulation
        sim_folder = os.path.join(self.output_path, parser.sim_id)
        if not os.path.exists(sim_folder):
            os.mkdir(sim_folder)

        # Create the requested files
        for filename in self.filenames:
            file_path = os.path.join(sim_folder, os.path.basename(filename))
            with open(file_path, 'wb') as outfile:
                outfile.write(parser.raw_data[filename])
