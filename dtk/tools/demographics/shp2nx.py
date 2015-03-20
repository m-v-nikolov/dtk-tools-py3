import os
import shapefile
import matplotlib.pyplot as plt

title='Garki (ESRI roads)'
bbox=(8.66, 12.1, 9.7, 12.7)

roads_folder='D:/polio_gis/NIE/Shapefiles/Roads_shp/Jigawa_roads'
roads_file_base='Jigawa_roads'

def plot_roads(road_class,color):
    sf = shapefile.Reader(os.path.join(roads_folder,'-'.join([roads_file_base,road_class])))
    for i,s in enumerate(sf.iterShapes()):
        (xx,yy)=zip(*s.points)
        plt.plot(xx,yy,color)
    print('%d segments with road class %s' %(i,road_class))

categories=[('Major','firebrick'), #('Principal','green'),
            ('Tertiary','gray'), #('Residential','lightgray')
            ]
fig=plt.figure(title,figsize=(12,7))
ax = fig.add_subplot(111, aspect='equal')
for cat in categories:
    plot_roads(*cat)

ax.set_xlim([bbox[0],bbox[2]])
ax.set_ylim([bbox[1],bbox[3]])
ax.set_title(title)

plt.show()