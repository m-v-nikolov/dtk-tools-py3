from calibtool.analyzers.BaseComparisonAnalyzer import BaseComparisonAnalyzer


class PrevalenceAnalyzer(BaseComparisonAnalyzer):
    @classmethod
    def plot_comparison(cls, fig, data, **kwargs):
        pass

    def __init__(self, site):
        super(PrevalenceAnalyzer, self).__init__(site)

        self.result = []

    def apply(self, parser):
        self.result.append({'NodeIds':[1,2,3]})
        pass

    def finalize(self):
        pass

    def cache(self):
        pass