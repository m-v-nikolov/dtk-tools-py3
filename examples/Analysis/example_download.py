from simtools.Analysis.AnalyzeManager import AnalyzeManager
from simtools.Analysis.BaseAnalyzers import DownloadAnalyzer

if __name__ == "__main__":
    analyzer = DownloadAnalyzer(filenames=['output\\InsetChart.json', 'config.json'])
    am = AnalyzeManager('latest', analyzers=analyzer)
    am.analyze()
