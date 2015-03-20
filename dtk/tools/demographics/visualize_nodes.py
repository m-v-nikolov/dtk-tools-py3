import sys
import os
import json
import struct
import collections
import numpy as np
import matplotlib.pyplot as plt

def ShowUsage():
    print ('\nUsage: %s [demographics-file] [optional:migration-file]' % os.path.basename(sys.argv[0]))

def CheckFiles(infilename):
    print('Source file:  %s' % infilename)

    if not os.path.exists(infilename):
        print('Source file doesn\'t exist!')
        return False

    return True

def ExtractNodeInfo(demogfile):
    if not CheckFiles(demogfile):
        exit(-1)

    with open(demogfile, 'r') as file:
        demogjson = json.load(file)

    nodes = demogjson['Nodes']

    # Note: assuming these are in the Nodes block.
    #       if plotting anything else, one might need to check default block
    lats = [ n['NodeAttributes']['Latitude'] for n in nodes ]
    lons = [ n['NodeAttributes']['Longitude'] for n in nodes ]

    try:
        default_pop = demogjson['Defaults']['NodeAttributes']['InitialPopulation']
    except:
        default_pop = 0
        pass

    try:
        pops = [ n['NodeAttributes']['InitialPopulation'] if 'InitialPopulation' in n['NodeAttributes'] else default_pop for n in nodes ]
    except:
        raise Exception('Failed to parse InitialPopulation values correctly for all %d nodes in simulation.'% len(nodes))

    return(lats, lons, pops)

def VisualizeNodes(demogfile):
    (lats, lons, pops) = ExtractNodeInfo(demogfile)
    max_pop = float(max(pops))
    if max_pop <= 0:
        raise Exception('No population found in any of the %d nodes.' % len(nodes))

    print('Total population of ' + '{:,}'.format(sum(pops)) + ' in ' + '{:,}'.format(len(nodes)) + ' nodes.')

    plt.scatter(lons, lats, [20*p/max_pop for p in pops], color=[0.6, 0, 0], linewidth=0.1, alpha=0.5)
    #plt.title(os.path.basename(demogfile))
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.axis('equal')
    plt.figtext(0.95, 0.93, 'Nodes: ' + '{:,}'.format(len(nodes)), ha='right', va='top', fontsize=10)
    plt.figtext(0.95, 0.9, 'Total population: ' + '{:,}'.format(sum(pops)), ha='right', va='top', fontsize=10)
    plt.figtext(0.15, 0.20, 'Input file(s): \n' + os.path.basename(demogfile), ha='left', va='top', fontsize=10)

def DrawMigrationRoutes(migration_routes, filename=None):

    for r in migration_routes:
        DrawMigrationRoute(*r)

    if filename:
        plt.figtext(0.15, 0.14, filename, ha='left', va='top', fontsize=10)

def DrawMigrationRoute(point1, point2, rate):
    plt.plot([point1[1],point2[1]], [point1[0], point2[0]], 'k', linewidth=0.05*np.log(rate), alpha=0.2)

def GetMigrationRoutes(demogfile, migfile, keepSorted=False):

    if not CheckFiles(migfile):
        exit(-1)

    with open(demogfile, 'r') as file:
        demogjson = json.load(file)

    nodes = demogjson['Nodes']

    node_map = collections.OrderedDict()
    for node in nodes:
        node_map[node['NodeID']] = (node['NodeAttributes']['Latitude'], node['NodeAttributes']['Longitude'])

    with open(migfile + '.json', 'r') as header_file:
        headerjson = json.load(header_file)
        n_nodes = headerjson['Metadata']['NodeCount']
        data_count = headerjson['Metadata']['DatavalueCount']

    # TODO: switch to NodeOffsets, since the binary migration data can be sparse
    #       e.g. sea migration in Madagascar only has 4 nodes with ports
    migration_routes = []
    with open(migfile, 'rb') as bin_file:
        if keepSorted:
            ordered_nodes = sorted(node_map.keys()) # for Gwembe with NodeOffsets sorted by NodeID
        else:
            ordered_nodes = node_map.keys() # for legacy files with migration file packed using node ordering of demographics file
        for nodeid in ordered_nodes: 
            data = bin_file.read(12*data_count) # 4 bytes for the long and 8 for the double
            migrates = struct.unpack( '%dL%dd' % (data_count,data_count), data)
            dests = [m for m in migrates[:data_count] if m>0]
            dest_rates = [m for m in migrates[-data_count:] if m>0]
            for i,d in enumerate(dests):
                migration_routes.append((node_map[nodeid], node_map[dests[i]], dest_rates[i]))

    return migration_routes

if __name__ == "__main__":
    if len(sys.argv) < 2:
        ShowUsage()
        exit(0)

    demogfile = sys.argv[1]
    VisualizeNodes(demogfile)

    if len(sys.argv) == 3:
        migfile = sys.argv[2]
        mr = GetMigrationRoutes(demogfile, migfile)
        DrawMigrationRoutes(mr, os.path.basename(migfile))

    plt.tight_layout()
    plt.show()
