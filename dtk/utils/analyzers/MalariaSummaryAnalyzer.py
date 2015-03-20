import matplotlib.pyplot as plt
import numpy as np
import os
import json

# a class to do the analysis of malaria summary reporting
class MalariaSummaryAnalyzer():

    def __init__(self, group_by='Config_Name', filter_function=None, report_range=None, summaryOnly=False, semilogAge=True, saveOutput=False):
        self.filenames = ['MalariaSummaryReport_AnnualAverage.json']
        self.channels = ['Annual EIR', 'Average Population by Age Bin', 'PfPR_2to10', 'PfPR by Age Bin', 'RDT PfPR by Age Bin', 'Annual Clinical Incidence by Age Bin', 'Annual Severe Incidence by Age Bin']
        self.summaryOnly = summaryOnly
        self.semilogAge = semilogAge
        self.saveOutput = saveOutput
        self.agebins = []
        self.data = {}
        self.group_by = group_by
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
            emit_data[self.filenames[0] + ' ' + channel] = self.report_range(output_data[self.filenames[0]][channel])

        if not self.agebins:
            self.agebins = output_data[self.filenames[0]]['Age Bins']

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
                ch_arrays = np.array(p.output_data[ch_key], dtype=np.float32)

                # treating year-to-year variation on same footing as random seeds
                for iyr,ch_array in enumerate(ch_arrays):
                    weight = 1
                    if channel != 'Average Population by Age Bin' and not isinstance(ch_array,np.float32):
                        weight = p.output_data[self.filenames[0] + ' ' + 'Average Population by Age Bin'][iyr]

                    if group_name not in self.data[channel]:
                        self.data[channel][group_name] = {}
                        self.data[channel][group_name]['count']  = np.array(weight)
                        self.data[channel][group_name]['sum']    = weight * np.array(ch_array)
                        self.data[channel][group_name]['sumsqr'] = weight * np.power(ch_array, 2)
                    else:
                        self.data[channel][group_name]['count']  += np.array(weight)
                        self.data[channel][group_name]['sum']    += weight * np.array(ch_array)
                        self.data[channel][group_name]['sumsqr'] += weight * np.power(ch_array, 2)

        # calculate means
        for channel in self.channels:
            for group in self.data[channel]:
                gg = self.data[channel][group]
                self.data[channel][group]['mean'] = gg['sum']/gg['count']
                self.data[channel][group]['std'] = np.sqrt(( gg['sumsqr'] / gg['count'] - np.power( gg['mean'], 2 ) ).clip(min=0))

    def finalize(self):
        print('Finalizing...')
        
        if not self.summaryOnly:
            bincenters = (np.array([0] + self.agebins[:-1]) + np.array(self.agebins[:-1] + [80]))/2
            detection_tech = 'slide microscopy' #  'RDT'  'slide microscopy'
            pfpr_channel = ('RDT ' if detection_tech == 'RDT' else '') + 'PfPR by Age Bin'
            plt.figure('PfPR Summary')
            legend_entries = []
            for (k, pfpr) in self.data[pfpr_channel].items():
                #plt.errorbar(bincenters, pfpr['mean'], yerr=pfpr['std'], fmt='o-')
                plt.errorbar(bincenters, pfpr['mean'], yerr=pfpr['mean']/np.sqrt(pfpr['sum']), fmt='o-')
                legend_entry = k
                legend_entry += ': EIR=' + str( float( '%0.2f' % self.data['Annual EIR'][k]['mean'] ) )
                legend_entry += ', PfPR_2to10=' + str( float( '%0.2f' % self.data['PfPR_2to10'][k]['mean'] ) )
                legend_entries.append(legend_entry)
            plt.title('PfPR by age')
            plt.legend(legend_entries, numpoints=1, loc='lower center')
            plt.xlabel('Age (years)')
            plt.ylabel('Parasite Prevalence (%s)' % detection_tech)
            plt.ylim([0.0, 1.0])
            if self.semilogAge:
                plt.xscale('log')

            plt.figure('Clinical Incidence Summary')
            for (k, clinical) in self.data['Annual Clinical Incidence by Age Bin'].items():
                #plt.errorbar(bincenters, clinical['mean'], yerr=clinical['std'], fmt='o-')
                plt.errorbar(bincenters, clinical['mean'], yerr=clinical['mean']/np.sqrt(clinical['sum']), fmt='o-')
            plt.title('Clinical Incidence by age')
            plt.legend(legend_entries, numpoints=1, loc='upper right')
            plt.xlabel('Age (years)')
            plt.ylabel('Clinical Incidence per Year')
            plt.ylim([0.0, 10.0])
            if self.semilogAge:
                plt.xscale('log')
                
            plt.figure('Severe Disease Summary')
            for (k, severe) in self.data['Annual Severe Incidence by Age Bin'].items():
                #plt.errorbar(bincenters, severe['mean'], yerr=severe['std'], fmt='o-')
                plt.errorbar(bincenters, severe['mean'], yerr=severe['mean']/np.sqrt(severe['sum']), fmt='o-')
            plt.title('Severe Incidence by age')
            plt.legend(legend_entries, numpoints=1, loc='upper right')
            plt.xlabel('Age (years)')
            plt.ylabel('Severe Incidence per Year')
            plt.ylim([0.0, 1.0])
            if self.semilogAge:
                plt.xscale('log')

            if self.saveOutput:
                
                output_json = {'detection tech': detection_tech,
                               'bincenters': bincenters,
                               'PfPR': self.data[pfpr_channel],
                               'Clinical Incidence':self.data['Annual Clinical Incidence by Age Bin'],
                               'Severe Disease':self.data['Annual Severe Incidence by Age Bin'],
                               'PfPR_2to10': self.data['PfPR_2to10'],
                               'Annual EIR': self.data['Annual EIR'],
                               'Population': self.data['Average Population by Age Bin']
                               }             
                #with open(os.path.join('plots', 'summary.json'), 'w') as output_file:
                #    json.dumps(output_json, output_file, indent=4, sort_keys=True, cls=NumpyAwareJSONEncoder)
                np.save(os.path.join('plots', 'summary.npy'), output_json)
                
        plt.figure('Transmission Dependences')
        plt.subplot(131)
        for (k, pfpr) in self.data['PfPR_2to10'].items():
            plt.errorbar(self.data['Annual EIR'][k]['mean'], pfpr['mean'], xerr=self.data['Annual EIR'][k]['std'], yerr=pfpr['std'], fmt='o-')
        plt.xlabel('Annual EIR') 
        plt.ylabel('PfPR 2-10 (slide microscopy)')
        plt.ylim([0,1])

        plt.subplot(132)
        for (k, clinical) in self.data['Annual Clinical Incidence by Age Bin'].items():
            clinical_means = clinical['mean']
            clinical_means[np.isnan(clinical_means)]=0
            population_means = self.data['Average Population by Age Bin'][k]['mean']
            weighted_clinical_mean = sum([m*w for m,w in zip(clinical_means, population_means)])/sum(population_means) # TODO: configurability of ages to average?
            #print(weighted_clinical_mean) # TODO: weighting of errors?
            plt.errorbar(self.data['PfPR_2to10'][k]['mean'], weighted_clinical_mean, xerr=self.data['PfPR_2to10'][k]['std'], fmt='o-')   
        plt.ylabel('Annual clinical incidence per person')
        plt.xlabel('PfPR 2-10 (slide microscopy)')
        plt.ylim([0,2])

        plt.subplot(133)
        for (k, severe) in self.data['Annual Severe Incidence by Age Bin'].items():
            severe_means = severe['mean']
            severe_means[np.isnan(severe_means)]=0
            population_means = self.data['Average Population by Age Bin'][k]['mean']
            weighted_severe_mean = sum([m*w for m,w in zip(severe_means, population_means)])/sum(population_means)
            #print(weighted_severe_mean) # TODO: weighting of errors?
            plt.errorbar(self.data['PfPR_2to10'][k]['mean'], weighted_severe_mean, xerr=self.data['PfPR_2to10'][k]['std'], fmt='o-')    
        plt.ylabel('Annual severe incidence per person')
        plt.xlabel('PfPR 2-10 (slide microscopy)')       
        plt.ylim([0,0.2])
        
        #plt.show()
