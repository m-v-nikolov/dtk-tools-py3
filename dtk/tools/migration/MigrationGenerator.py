import sys, os, json, numpy, struct, array
import getopt
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from scipy.cluster.vq import *
import warnings


class KMeansLoadBalancer(object):
    
    '''
    this class implements one type of load balancing based on kmeans clustering;
    if we decide to add different load balance algorithms we could have a common interface 
    implemented by all; in this case this class would need to be refactored to reflect that
    '''
    
    def __init__(self, demographics_file_path, nclusters = 32, niterations = 50, max_equal_clusters_iterations = 5000, cluster_max_over_avg_threshold = 1.6): 
        
        self.nclusters = nclusters
        self.niterations = niterations
        self.max_equal_clusters_iterations = max_equal_clusters_iterations
        self.cluster_max_over_avg_threshold = cluster_max_over_avg_threshold
        self.demographics_file_path = demographics_file_path
        
        # plotting related attributes
        self.max_marker_size = 500

    def balance_load(self):
        
        print(' Generating load balancing using KMeansLoadBalancer')
              
        with open(self.demographics_file_path, 'r') as file:
            demogjson = json.load(file) #TODO: object_pairs_hook??

            numnodes = 0
            if 'Metadata' in demogjson:
                if 'NodeCount' in demogjson['Metadata']:
                    numnodes = demogjson['Metadata']['NodeCount']
                else:
                    print("Demographics file has no property ['Metadata']['NodeCount']")
            else:
                print("Demographics file has no property ['Metadata']")

            default_population = 0
            if 'Defaults' in demogjson:
                if 'NodeAttributes' in demogjson['Defaults']:
                    if 'InitialPopulation' in demogjson['Defaults']['NodeAttributes']:
                        default_population = demogjson['Defaults']['NodeAttributes']['InitialPopulation']
                    else:
                        print("Demographics file has no property ['Defaults']['NodeAttributes']['InitialPopulation']")
                else:
                    print("Demographics file has no property ['Defaults']['NodeAttributes']")
            else:
                print("Demographics file has no property ['Defaults']")

            print('There are ' + str(numnodes) + ' nodes in this demographics file')

            lats  = []
            longs = []
            node_ids = []
            node_pops = []
            
            for node in demogjson['Nodes']:
            #    print( 'Node ID: ' + str(node['NodeID']) + 
            #           '\tLat: ' + str(node['NodeAttributes']['Latitude']) + 
            #           '\tLong: ' + str(node['NodeAttributes']['Longitude']) )
        
                lats.append(float(node['NodeAttributes']['Latitude']))
                longs.append(float(node['NodeAttributes']['Longitude']))
                node_ids.append(node['NodeID'])
                if 'InitialPopulation' in node['NodeAttributes']:
                    node_pops.append(float(node['NodeAttributes']['InitialPopulation']))
                else:
                    node_pops.append(float(default_population))
            
        # cluster node IDs by lat/long
        # TODO: post-processing to require equal number of nodes in each cluster??
        #       find few nearest neighbors of most populous cluster; give least populous neighbor closest node; iterate??
        # OR:   use centroids as seeds for next kmeans??  or is that what iterations is already doing??
        # FOR NOW: brute force repeat of kmeans until equality threshold is passed
        iterations = 0
        while(True):
            warnings.filterwarnings("ignore")
            res, idx = kmeans2(numpy.array(zip(longs,lats)), self.nclusters, self.niterations, 1e-05, 'points')
    
            #print('kmeans centroids: ' + str(res))
            #print('kmeans indices: ', idx)
            #print('unique indices: ' + str(numpy.unique(idx)))
    
            counts, binedges = numpy.histogram(idx, bins=self.nclusters, weights=node_pops)
            #print('Population per node-cluster: ' + str(counts))
            biggest_over_avg = float(self.nclusters)*max(counts)/sum(node_pops)
            #print('Population of largest cluster (' + str(max(counts)) + ') is ' + str(int(100*(biggest_over_avg-1))) + '% bigger than average (' + str(int(sum(node_pops)/float(nclusters))) + ')')
            iterations = iterations + 1
            if biggest_over_avg < self.cluster_max_over_avg_threshold:
                break
            if iterations > self.max_equal_clusters_iterations:
                #print(' Generating load balancing using KMeansLoadBalancer: Did not find a clustering solution satisfying threshold :(')
                break
    
        # get a colormap for cluster coloring
        # TODO: is there a better way to avoid adjacent colors being nearly indistinguishable?
        #colors = ( [ cm.get_cmap('jet', i*256/self.nclusters) for i in idx ] )
        colors = ( [ cm.jet(i*256/self.nclusters) for i in idx ] )
    
        max_node_pop = max(node_pops)
        sizes = ( [self.max_marker_size*node_pop/float(max_node_pop) for node_pop in node_pops] )
    
        # get node IDs in order of cluster ID in preparation for writing load-balancing file
        node_ids_by_index = zip(idx, node_ids, lats, longs)
        node_ids_by_index.sort()
        #for node_id_index_pair in node_ids_by_index:
        #    print('Cluster idx = ' + str(node_id_index_pair[0]) + '\t Node ID = ' + str(node_id_index_pair[1]))
    
        # TODO: order clusters according to some simple lat/long grouping
        #       this way, a 32 cluster file will be still pretty good for an 8 core simulation, etc.
    
        # prepare arrays for writing binary file
        sorted_node_ids = [ int(x[1]) for x in node_ids_by_index ]
        cum_load_list = list( numpy.arange(0,1,1.0/numnodes) )
        plt.scatter(longs, lats, s=sizes, c=colors)
        plt.title('Lat/Long scatter of nodes')
        plt.axis('equal')
                 
        # may need to break that function up in a refactor so that the return is not bag of apples, oranges and potatoes  
        return {'num_nodes':numnodes, 'node_ids':sorted_node_ids, 'cum_loads':cum_load_list, 'lb_fig': plt}
