import struct, array

from KMeansLoadBalancer import KMeansLoadBalancer 


class LoadBalanceGenerator(object):
    
    
    '''
    Generate multi-core simulation load balancing depending 
    on number of nodes, population size per node, etc..
    '''
    def __init__(self, num_cores, demographics_file_path, load_balanace_algo = 'kmeans'):
        
        self.num_cores = num_cores # number of cores to load balance nodes' populations
        self.demographics_file_path = demographics_file_path # contains population size per node
        self.load_balanace_algo = load_balanace_algo # load balance algorithm
        self.load_balance_nodes_list = None # output of load balance algo 
        self.load_balance_cum_loads_list = None # output of load balance algo
        self.num_nodes = 0 # number of nodes to load balance, output of load balance algo
        
        # load balance visualization figure; returned by algo
        self.load_balance_fig = None
        
    
    def generate_load_balance(self):
        
        if self.load_balanace_algo == 'kmeans':
            self.generate_kmeans_load_balance()
        else:
            raise ValueError("The " + str(self.load_balanace_algo) + " is not implemented yet.")
            
    
    def generate_kmeans_load_balance(self):
        
        
        #kmeans load balance parameters
        niterations = 50 
        cluster_max_over_avg_threshold = 1.6
        max_equal_clusters_iterations = 5000
        
        lb = KMeansLoadBalancer(self.demographics_file_path, self.num_cores, niterations, max_equal_clusters_iterations, cluster_max_over_avg_threshold)
        
        load_balance = lb.balance_load()
        
        self.num_nodes = load_balance['num_nodes']
        self.load_balance_nodes_list = load_balance['node_ids']
        self.load_balance_cum_loads_list = load_balance['cum_loads']
        self.load_balance_fig = load_balance['lb_fig']
        
        
    # save loadbalance binary for DTK input
    def save_load_balance_binary_file(self, load_balance_file_path):
           
        with open(load_balance_file_path, 'wb') as newfile:
            newfile.write(struct.pack('I',self.num_nodes))
            node_id_array = array.array('I')
            node_id_array.fromlist(self.load_balance_nodes_list)
            node_id_array.tofile(newfile)
            cum_load_array = array.array('f')
            cum_load_array.fromlist(self.load_balance_cum_loads_list)
            cum_load_array.tofile(newfile)
    
    
    # save load balance visualization
    def save_load_balance_figure(self, load_balance_fig_path):
        
        self.load_balance_fig.savefig(load_balance_fig_path, format='png', dpi = 300)
        self.load_balance_fig.close()