import matplotlib.pyplot as plt
import numpy as np
import os
import json

colors = ['b', 'g', 'k', 'r', 'm', 'c', 'y']

# a class to build a simple InsetChart.json analyzer
class SimpleInsetChartAnalyzer():

    def __init__(self, group_by='Config_Name', filter_function=None, report_range=None, saveOutput=False, channels=['Statistical Population', 'Rainfall', 'Adult Vectors', 'Daily EIR', 'Infected', 'Parasite Prevalence']):
        self.filenames = ['InsetChart.json']
        self.channels = channels
        self.data = {}
        self.group_by = group_by
        self.saveOutput = saveOutput
        if filter_function:
            self.filter_function = filter_function
        else:
            def return_true(x):
                return True
            self.filter_function = return_true
        if report_range:
            self.report_range = report_range
        else:
            def return_all(x):
                return x
            self.report_range = return_all
        for channel in self.channels:
            self.data[channel] = {}

    def filter(self, sim_metadata):
        return self.filter_function(sim_metadata)

    def map(self, output_data):
        emit_data = {}
        for channel in self.channels:
            key = self.filenames[0] + ' ' + channel
            data = output_data[self.filenames[0]]["Channels"][channel]["Data"]
            emit_data[key] = self.report_range(data)
        return emit_data

    def reduce(self, parsers):

        # accumulate grouped data over parsers
        for k,p in parsers.items():

            print(k,p.sim_data)

            # TODO: the choice of key-grouping would normally be done in the 'map' step
            if not self.group_by:
                group_name = k # the unique simId
            elif self.group_by.lower() == 'all':
                group_name = 'all'
            elif self.group_by in p.sim_data:
                group_name = p.sim_data[self.group_by] # e.g. 'Config_Name'
            else:
                print('The key %s is not found in the sim_data for grouping' % self.group_by)
                group_name = k # the unique simId

            # If there are different filters applied to two analyzers,
            # one might end up with parsers coming into this function
            # that do not have any information relevant to this analyzer
            # Check if the filename is output_data.
            # TODO: extend this check to other analyzers.
            if not any([self.filenames[0] in pk for pk in p.output_data.keys()]):
                continue

            for channel in self.channels:
                ch_key = self.filenames[0] + ' ' + channel
                if ch_key not in p.output_data.keys():
                    print("Couldn't find %s in %s" % (ch_key, p.output_data.keys()))
                    continue
                ch_array = np.array(p.output_data[ch_key], dtype=np.float32)
                if group_name not in self.data[channel]:
                    self.data[channel][group_name] = {}
                    self.data[channel][group_name]['count']  = 1
                    self.data[channel][group_name]['sum']    = np.array(ch_array)
                    self.data[channel][group_name]['sumsqr'] = np.power(ch_array, 2)
                else:
                    self.data[channel][group_name]['count']  += 1
                    self.data[channel][group_name]['sum']    += np.array(ch_array)
                    self.data[channel][group_name]['sumsqr'] += np.power(ch_array, 2)


        # calculate means
        for channel in self.channels:
            #print(self.data[channel].keys())
            for group in self.data[channel]:
                gg = self.data[channel][group]
                self.data[channel][group]['mean'] = gg['sum'] / gg['count']
                self.data[channel][group]['std'] = np.sqrt(( gg['sumsqr'] / gg['count'] - np.power( gg['mean'], 2 ) ).clip(min=0))

    def finalize(self):
        #print('Finalizing...')
        plt.figure('InsetChart1')
        ncol = 1+len(self.channels)/4
        for (i,channel) in enumerate(self.channels):
            plt.subplot(np.ceil(float(len(self.channels))/ncol), ncol, i+1)
            for (j,sim_value) in enumerate(self.data[channel].values()):
                color = colors[j%len(colors)]
                plt.plot(sim_value['mean'], color=color)
                plt.fill_between(range(len(sim_value['mean'])),
                                 sim_value['mean']-sim_value['std'],
                                 sim_value['mean']+sim_value['std'],
                                 color=color, facecolor=color, alpha=0.1)
            plt.title(channel)
            if not i:
                plt.legend(self.data[channel].keys())
            if 'sim_value' in locals():
                plt.xlim([0,len(sim_value['mean'])])

        plt.tight_layout()

        if self.saveOutput:

            # from dtk.utils.analyzers.JsonEncoders import NumpyAwareJSONEncoder
            #with open(os.path.join('plots', 'insetchart_summary.json'), 'w') as output_file:
            #    json.dumps(self.data, output_file, indent=4, sort_keys=True, cls=NumpyAwareJSONEncoder)

            np.save(os.path.join('plots', 'insetchart_summary.npy'), self.data)

            #hack
            #if 'Prevalence' in channel:
            #    plt.ylim([0,0.7])
            #    plt.xticks(range(0,365*5,365))
            #    plt.gca().set_xticklabels(range(2011,2016))

        #plt.show()
