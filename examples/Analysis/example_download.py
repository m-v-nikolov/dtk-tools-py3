from dtk.utils.analyzers.DownloadAnalyzer import DownloadAnalyzer
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager

if __name__ == "__main__":
    analyzer = DownloadAnalyzer(filenames=['output\\InsetChart.json', 'config.json'])
    am = AnalyzeManager('latest', analyzers=analyzer)
    am.create_dir_map = False
    am.analyze()
