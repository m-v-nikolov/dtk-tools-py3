from calibtool.analyzers.BaseComparisonAnalyzer import BaseComparisonAnalyzer


class PrevalenceAnalyzer(BaseComparisonAnalyzer):
    @classmethod
    def plot_comparison(cls, fig, data, **kwargs):
        pass

    def __init__(self, site):
        super(PrevalenceAnalyzer, self).__init__(site)

    def apply(self, parser):
        pass