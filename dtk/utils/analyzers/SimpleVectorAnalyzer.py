import matplotlib.pyplot as plt
import numpy as np

colors = ['b', 'g', 'k', 'r', 'm', 'c', 'y']

# a class to build a simple VectorSpeciesReport.json analyzer
class SimpleVectorAnalyzer():

    def __init__(self, group_by = 'Config_Name', filter_function=None, channels = ['Adult Vectors', 'Infectious Vectors', 'Daily EIR']):
        self.filenames = ['VectorSpeciesReport.json']
        self.channels = channels
        self.data = {}
        self.group_by = group_by
        if filter_function:
            self.filter_function = filter_function
        else:
            def return_true(x):
                return True
            self.filter_function = return_true
        for channel in self.channels:
            self.data[channel] = {}

    def filter(self, sim_metadata):
        return self.filter_function(sim_metadata)

    def map(self, output_data):

        emit_data = {}
        for channel in self.channels:
            key = self.filenames[0] + ' ' + channel
            data = output_data[self.filenames[0]]["Channels"][channel]["Data"]
            emit_data[key] = data
        emit_data["Species_Names"] = output_data[self.filenames[0]]["Header"]["Subchannel_Metadata"]["MeaningPerAxis"][0]
        return emit_data

    def reduce(self, parsers):

        # accumulate grouped data over parsers
        for k,p in parsers.items():

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

            if "Species_Names" not in self.data:
                self.data["Species_Names"] = {}
            if group_name not in self.data["Species_Names"]:
                self.data["Species_Names"][group_name] = p.output_data["Species_Names"]

            for channel in self.channels:
                ch_key = self.filenames[0] + ' ' + channel
                ch_array = p.output_data[ch_key]
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
        plt.figure('VectorReport1')
        ncol = 1+len(self.channels)/4
        for (i,channel) in enumerate(self.channels):
            plt.subplot(len(self.channels)/ncol, ncol, i+1)
            for j,(sim_key, sim_value) in enumerate(self.data[channel].items()):
                for k,species in enumerate(self.data["Species_Names"][sim_key][0]):
                    color = colors[k%len(colors)]
                    plt.plot(sim_value['mean'][k], color=color, alpha = 0.2 + 0.8*j/float(len(self.data[channel])), label=species + ' (' + str(sim_key) + ')')
                    plt.fill_between(range(len(sim_value['mean'][k])),
                                     sim_value['mean'][k]-sim_value['std'][k],
                                     sim_value['mean'][k]+sim_value['std'][k],
                                     color=color, facecolor=color, alpha=0.1)
            plt.title(channel)
            if not i:
                plt.legend()

        plt.tight_layout()

        #plt.show()
