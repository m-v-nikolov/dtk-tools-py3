import math
import json
import matplotlib.pyplot as plt
import numpy as np

#colors = ['b', 'g', 'k', 'r', 'm', 'c', 'y']
def rgbcolor(h, f):
    """Convert a color specified by h-value and f-value to an RGB
    three-tuple."""

    v = 1.0
    s = 1.0
    p = 0.0

    # q = 1 - f
    # t = f
    if h == 0:
        return v, f, p
    elif h == 1:
        return 1 - f, v, p
    elif h == 2:
        return p, v, f
    elif h == 3:
        return p, 1 - f, v
    elif h == 4:
        return f, p, v
    elif h == 5:
        return v, p, 1 - f

def uniquecolors(n):
    """Compute a list of distinct colors, each of which is
    represented as an RGB three-tuple"""
    hues = [(215+360.0 / n * i)%360 for i in range(n)]
    hs = [math.floor(hue / 60) % 6 for hue in hues]
    fs = [hue / 60 - math.floor(hue / 60) for hue in hues]
    return [rgbcolor(h, f) for h, f in zip(hs, fs)]

# a class to build a simple SpatialReport.json analyzer
class SimpleSpatialAnalyzer():

    def __init__(self, 
                 group_by = 'Config_Name', 
                 filter_function=None, 
                 channels = ['Prevalence', 'Daily_EIR'], 
                 node_names={},
                 write_output=''):
        self.filenames = ['SpatialReport_' + c + '.bin' for c in channels]
        self.channels = channels
        self.data = {}
        self.group_by = group_by
        self.node_names = node_names
        self.write_output = write_output
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
        for i,channel in enumerate(self.channels):
            key = self.filenames[i] + ' ' + channel
            data = output_data[self.filenames[i]]['data']
            emit_data[key] = data
        emit_data["Num_Nodes"] = output_data[self.filenames[0]]['n_nodes']
        emit_data["Num_Tstep"] = output_data[self.filenames[0]]['n_tstep']
        emit_data["Node_IDs"]  = output_data[self.filenames[0]]['nodeids']
        #print(emit_data)
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

            if "Node_IDs" not in self.data:
                self.data["Node_IDs"] = {}
            if group_name not in self.data["Node_IDs"]:
                self.data["Node_IDs"][group_name] = p.output_data["Node_IDs"]

            for i,channel in enumerate(self.channels):
                ch_key = self.filenames[i] + ' ' + channel
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
        plt.figure('SpatialReport1')
        ncol = 1+len(self.channels)/4
        #print(self.data["Node_IDs"].values()[0])
        colors = uniquecolors(len(self.data["Node_IDs"].values()[0]))
        for (i,channel) in enumerate(self.channels):
            #print(channel)
            plt.subplot(len(self.channels)/ncol, ncol, i+1)
            for j,(sim_key, sim_value) in enumerate(self.data[channel].items()):
                #print(j,sim_key,sim_value)
                for k,nodeid in enumerate(self.data["Node_IDs"][sim_key]):
                    #print(k,nodeid)
                    color = colors[k%len(colors)]

                    # Legend with Node names instead of IDs if specified
                    if self.node_names and nodeid in self.node_names.keys():
                        label = self.node_names[nodeid] + ' (' + str(sim_key) + ')'
                    else:
                        label='NodeID: ' + str(nodeid) + ' (' + str(sim_key) + ')'

                    plt.plot(sim_value['mean'][:,k], color=color, alpha = 0.2 + 0.8*j/float(len(self.data[channel])), label=label)
                    plt.fill_between(range(len(sim_value['mean'][:,k])),
                                     sim_value['mean'][:,k]-sim_value['std'][:,k],
                                     sim_value['mean'][:,k]+sim_value['std'][:,k],
                                     color=color, facecolor=color, alpha=0.1)
            plt.title(channel)
            if not i:
                plt.legend(ncol=1+len(self.data["Node_IDs"][sim_key])//10)

        plt.tight_layout()

        # dump output to file
        if self.write_output:
            if not self.node_names:
                print('Trying to write JSON output without node names that are used for dictionary keys.')
            elif self.group_by != 'all':
                print("Trying to write JSON output with more simulation group_by != 'all'.")
            else:
                json_output={}
                for nname in self.node_names.values():
                    json_output[nname]={}
                for channel in self.channels:
                    for k,nodeid in enumerate(self.data["Node_IDs"]['all']):
                        aa=self.data[channel]['all']['mean'][:,k]
                        json_output[self.node_names[nodeid]][channel] = aa.tolist()
            #print(json_output.keys())

            with open(self.write_output,'w') as of:
                of.write( json.dumps( json_output, sort_keys=True, indent=4 ) )

        #plt.show()
