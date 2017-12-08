import os

from calibtool.analyzers.BaseComparisonAnalyzer import BaseComparisonAnalyzer


class PrevalenceAnalyzer(BaseComparisonAnalyzer):
    @classmethod
    def plot_comparison(cls, fig, data, **kwargs):
        pass

    filenames = ['output/SpatialReport_New_Diagnostic_Prevalence.bin']

    def __init__(self, site):
        super(PrevalenceAnalyzer, self).__init__(site)

        self.result = []

    def apply(self, parser):
        date = parser.sim_data['Prevalence_date']
        serialization_date = parser.sim_data['Serialization']
        threshold = parser.sim_data['Prevalence_threshold']

        prev_data = parser.raw_data[self.filenames[0]]['data'][date]
        nodes = parser.raw_data[self.filenames[0]]['nodeids']
        nodes_idx = [i for i,val in enumerate(prev_data) if val > threshold]
        nodes_ids = [int(nodes[i]) for i in nodes_idx]

        print("Sim dir: %s" % parser.sim_dir)

        self.result.append({'NodeIDs':nodes_ids,
                            'Serialized_Population_Path': os.path.join(parser.sim_dir, 'output'),
                            'Serialized_Population_Filenames': ['state-%05d-%03d.dtk' % (serialization_date, x) for x in range(24)]
                            })

    def finalize(self):
        pass

    def cache(self):
        pass