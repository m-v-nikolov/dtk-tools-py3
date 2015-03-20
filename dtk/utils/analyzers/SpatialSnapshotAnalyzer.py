from dtk.tools.demographics.visualize_nodes import ExtractNodeInfo, GetMigrationRoutes
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.collections import PatchCollection
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Polygon, Point, MultiPoint, MultiPolygon
from shapely.prepared import prep
from descartes import PolygonPatch
import numpy as np
import pandas as pd
import operator

# a class to build an analyzer of a SpatialReport.json channel
# that displays snapshots of the channel quantity at discrete times
# as a set of lat/long scatter plots
class SpatialSnapshotAnalyzer():

    def __init__(self,
                 filter_function=None,
                 channel = 'Prevalence',
                 timesteps=(1,),
                 demog_file = None,
                 mig_file = None,
                 shape_file = None,
                 max_alpha = 0.8):
        
        self.filenames = ['SpatialReport_' + channel + '.bin'] # Parser requires list
        self.timesteps = timesteps
        self.channel = channel
        self.data = {}
        if filter_function:
            self.filter_function = filter_function
        else:
            def return_true(x):
                return True
            self.filter_function = return_true
        for ts in self.timesteps:
            self.data[ts] = {}

        self.demog_file = demog_file
        self.mig_file = mig_file
        self.shape_file = shape_file

        self.max_alpha = max_alpha

    def filter(self, sim_metadata):
        return self.filter_function(sim_metadata)

    def map(self, output_data):
        emit_data = {}
        filename = self.filenames[0]
        key = filename + ' ' + self.channel
        data = [output_data[filename]['data'][i] for i in self.timesteps]
        emit_data[key] = data
        emit_data["Num_Nodes"] = output_data[filename]['n_nodes']
        emit_data["Num_Tstep"] = output_data[filename]['n_tstep']
        emit_data["Node_IDs"]  = output_data[filename]['nodeids']
        return emit_data

    def reduce(self, parsers):
        for k,p in parsers.items():

            # N.B. Let's only have one grouping option here
            group_name = 'all'

            if "Node_IDs" not in self.data:
                self.data["Node_IDs"] = {}
            if group_name not in self.data["Node_IDs"]:
                self.data["Node_IDs"][group_name] = p.output_data["Node_IDs"]

            ch_key = self.filenames[0] + ' ' + self.channel
            ch_array = p.output_data[ch_key]

            for i,ts in enumerate(self.timesteps):

                if group_name not in self.data[ts]:
                    self.data[ts][group_name] = {}
                    self.data[ts][group_name]['count']  = 1
                    self.data[ts][group_name]['sum']    = np.array(ch_array[i])
                    self.data[ts][group_name]['sumsqr'] = np.power(ch_array[i], 2)
                else:
                    self.data[ts][group_name]['count']  += 1
                    self.data[ts][group_name]['sum']    += np.array(ch_array[i])
                    self.data[ts][group_name]['sumsqr'] += np.power(ch_array[i], 2)

        # calculate means
        for ts in self.timesteps:
            #print(self.data[ts].keys())
            for group in self.data[ts]:
                gg = self.data[ts][group]
                self.data[ts][group]['mean'] = gg['sum'] / gg['count']
                self.data[ts][group]['std'] = np.sqrt(( gg['sumsqr'] / gg['count'] - np.power( gg['mean'], 2 ) ).clip(min=0))


    def finalize(self):
        #print('Finalizing...')

        cdict = {
                    'red'  :  ( (0, 1, 1), (0.2, 0.93, 0.93), (0.7, 0.5, 0.5), (1, 0.3, 0.3)),
                    'green':  ( (0, 1, 1), (0.2, 0.96, 0.96), (0.7, 0.0, 0.0), (1, 0.0, 0.0)),
                    'blue' :  ( (0, 1, 1), (0.2, 0.42, 0.42), (0.7, 0.0, 0.0), (1, 0.0, 0.0))
                    }
        yellow_red_colormap = colors.LinearSegmentedColormap('yellow_red_colormap', cdict, 50)

        fig = plt.figure('Snapshot1', figsize=(19,5))
        nrow = 1+len(self.timesteps)/4
        m=[]
        for (i,ts) in enumerate(self.timesteps):
            ax = fig.add_subplot(nrow, len(self.timesteps)/nrow, i+1)
            for (sim_key, sim_value) in self.data[ts].items():

                #print(sim_key,sim_value)

                nodeids = self.data["Node_IDs"][sim_key]
                
                #print(nodeids, sim_value['mean'])

                if not self.demog_file:
                    plt.hist(sim_value['mean'], alpha=0.2)
                else:
                    # N.B. ERAD-1200
                    (lats,lons,pops) = ExtractNodeInfo(self.demog_file)
                    max_pop = float(max(pops))
                    if max_pop <= 0:
                        raise Exception('No population found in any of the %d nodes.' % len(nodeids))

                    print('Total population of ' + '{:,}'.format(sum(pops)) + ' in ' + '{:,}'.format(len(nodeids)) + ' nodes.')

                    min_lat = min(lats)
                    min_lon = min(lons)
                    max_lat = max(lats)
                    max_lon = max(lons)
                    mean_lat = np.mean(lats)
                    mean_lon = np.mean(lons)
                    lat_range = max_lat-min_lat
                    lon_range = max_lon-min_lon

                    # create polar stereographic Basemap and draw some features
                    if not m:
                        m = Basemap(projection='stere', lat_0=mean_lat, lon_0=mean_lon,
                                    llcrnrlat=min_lat-0.3*lat_range, urcrnrlat=max_lat+0.3*lat_range,
                                    llcrnrlon=min_lon-0.3*lon_range, urcrnrlon=max_lon+0.3*lon_range,
                                    rsphere=6371200., resolution='f') # put back to 'f' for fine resolution ('c' for coarse)
                    m.drawcoastlines()
                    m.drawstates()
                    m.drawcountries()
                    m.fillcontinents(color='brown', lake_color='aqua', zorder=0, alpha=0.1)

                    # TODO: make gridding more generically applicable to different lat_range, lon_range
                    m.drawparallels(np.arange(np.round(5*(min_lat-0.3*lat_range))/5.0, np.round(5*(max_lat+0.3*lat_range))/5.0, 0.2), linewidth=0.1, labels=[1,0,0,1])
                    m.drawmeridians(np.arange(np.round(5*(min_lon-0.3*lon_range))/5.0, np.round(5*(max_lon+0.3*lon_range))/5.0, 0.2), linewidth=0.1, labels=[1,0,0,1])

                    if not self.shape_file:
                        m.scatter(lons, lats, s=[200*p/max_pop for p in pops], c=sim_value['mean'], cmap=yellow_red_colormap, vmin=0, vmax=1, alpha=0.7, latlon=True)
                    else:
                        m.readshapefile(self.shape_file.split('.')[0], 'shapes', color='none', zorder=2)
                        df_map = pd.DataFrame({'poly': [Polygon(xy) for xy in m.shapes]})

                        # Filter polygon shapes on point.within and assign prevalence values to patches below
                        # Create Point objects in map coordinates from node lon and lat values
                        pt_series = pd.Series( [Point(m(mapped_x, mapped_y)) for mapped_x, mapped_y in zip(lons, lats)] )
                        multipt = MultiPoint(list(pt_series.values))

                        polygons = [ filter(x.within, df_map['poly']) for x in multipt ]
                        patches = [ PolygonPatch(x[0], fc='#555555', ec='#787878', lw=0.25, alpha=0.1, zorder=4) for x in polygons ]
                        pc = PatchCollection(patches, match_original=True)
                        pc.set_facecolor(yellow_red_colormap(sim_value['mean']))
                        pc.set_alpha(0.4)
                        ax.add_collection(pc)
                        m.scatter(lons, lats, s=[200*p/max_pop for p in pops], c=sim_value['mean'], cmap=yellow_red_colormap, vmin=0, vmax=1, alpha=0.7, latlon=True)

                    if self.mig_file:
                        mr = GetMigrationRoutes(self.demog_file, self.mig_file, keepSorted=True)
                        max_rate=max(mr, key=operator.itemgetter(2))[2]
                        for r in mr:
                            (point1, point2, rate) = r
                            m.drawgreatcircle(point1[1], point1[0], point2[1], point2[0], c='k', linewidth=2*(rate/max_rate)**0.3, alpha=self.max_alpha*(rate/max_rate)**0.3)

                    m.drawmapscale(
                        max_lon - 0.05*lon_range, min_lat - 0.1*lon_range,
                        mean_lon, mean_lat,
                        30.,
                        barstyle='fancy', labelstyle='simple',
                        fillcolor1='w', fillcolor2='#555555',
                        fontcolor='#555555',
                        zorder=5)

            ax.text( 0.5, 0.95, 'Timestep: ' + str(ts),
                     horizontalalignment = 'center',
                     transform = ax.transAxes )

        if self.demog_file:
            cbar = plt.colorbar(use_gridspec=True)
            cbar.ax.set_yticklabels(['0%', '', '20%', '', '40%', '', '60%', '', '80%', '', '100%'])
            cbar.set_label('RDT positive', rotation=270)

        plt.tight_layout(pad=1.5, w_pad=1, h_pad=1)
