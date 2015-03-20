## Execute directly: 'python example_plots.py'
## or via the dtk.py script: 'dtk analyze example_plots.py'

from dtk.utils.analyzers.SimpleInsetChartAnalyzer import SimpleInsetChartAnalyzer
from dtk.utils.analyzers.SimpleVectorAnalyzer import SimpleVectorAnalyzer

channels = ['Statistical Population', 'Rainfall', 'Air Temperature', 
            'Adult Vectors', 'Daily EIR', 'Infected']

# TODO: make channel analyzers robust enough to throw warning on missing channels
# if sim_manager.exp_data['sim_type'] == 'MALARIA_SIM':
#     channels.extend(['Parasite Prevalence', 'New Clinical Cases', 'New Severe Cases'])

inset_chart_analyzer = SimpleInsetChartAnalyzer(channels=channels, group_by='all')
vector_analyzer = SimpleVectorAnalyzer(group_by='all')

analyzers = [ inset_chart_analyzer, # InsetChart.json analyzer
              vector_analyzer       # VectorSpeciesReport.json analyzer
            ]

# The following is only for when running directly from the command-line
if __name__ == "__main__":

    import os
    import glob
    import matplotlib.pyplot as plt
    from dtk.utils.simulation.SimulationManager import SimulationManagerFactory

    print('Getting most recent experiment in current directory...')
    expfiles = glob.glob('simulations/*.json')
    if expfiles:
        filepath = max(expfiles, key=os.path.getctime)
    else:
        raise Exception('Unable to find experiment meta-data file in local directory.')

    sm = SimulationManagerFactory.from_file(filepath)

    # run the analyses
    for analyzer in analyzers:
        sm.AddAnalyzer(analyzer)
    sm.AnalyzeSimulations()
    plt.show()