import heapq

class GravityModelRatesGenerator(object):
    '''
    generate rates matrix based on source-destination pairs path lengths (path weights) and graph topology input;
    see MigrationGenerator for path lengths/weights and graph topology generation 
    '''

    def __init__(self, path_lengths, graph, coeff=1):
        self.path_lengths = path_lengths

        self.graph = graph
        
        #print graph.edges()
        
        self.coeff = coeff
        
        #print coeff

        self.link_rates = None # output of gravity model based migration links generation
        
        
    '''
    gravity model based link rates
    '''
    def generate_migration_links_rates(self):
        
        paths={}
        
        migs=[]
        
        max_migs=[]
        
        mindist=1 # 1km minimum distance in gravity model for improved short-distance asymptotic behavior
        dist_cutoff=20 # beyond 20km effective distance not reached in 1 day.
        max_migration_dests=8 # limit of DTK local migration
        
        for src,v in self.path_lengths.items():
            paths[src]={}
            #print v.items()
            for dest,dist in v.items():
                #print dist
                #print src
                #print dest
                if not dist or src==dest:
                    continue
                if dist<dist_cutoff:
                    mig_rate=self.coeff*self.graph.population[int(dest)]/(mindist+dist)**2
                    mig_volume=self.graph.population[int(src)]*mig_rate
                    paths[src][dest]=mig_rate 
                    migs.append(mig_rate)
            d=paths[src]
            #print d
            #if d:
            nl=heapq.nlargest(max_migration_dests,d,key=lambda k:d[k])
            #print(len(d), nl, [int(d[k]) for k in nl])
            max_migs.append(d[nl[0]])

            paths[src]=dict([(k,d[k]) for k in nl])
        
        self.link_rates = paths
        
        return paths