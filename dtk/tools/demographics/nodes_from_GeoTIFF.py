"""
Utilities for reading and plotting GeoTIFF binary files.
"""
import gdal
import gdalconst
import json
import sys
import struct
import numpy as np
from numpy import ma
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
from node import Node

def read(bingrid_name, cropX=None, cropY=None):
    """Read the data and meta-data from GeoTIFF
    """
    
    if bingrid_name[-4:] != '.tif':
        raise Exception('Expecting .tif extension for GeoTIFF files')

    dataset = gdal.Open(bingrid_name, gdalconst.GA_ReadOnly)
    geotransform = dataset.GetGeoTransform()

    nrows = dataset.RasterYSize
    rows = cropY if cropY else range(nrows)

    ncols = dataset.RasterXSize
    cols = cropX if cropX else range(ncols)

    #print(rows,cols)

    band = dataset.GetRasterBand(1)
    bandtype = gdal.GetDataTypeName(band.DataType)
    a = np.zeros(shape=(len(rows),len(cols)),dtype=np.float32)
    for i,irow in enumerate(rows):
        scanline=band.ReadRaster( cols[0], irow, len(cols), 1, len(cols), 1, band.DataType)
        data = struct.unpack('f' * len(cols), scanline)
        a[i][:] = data

    return a, geotransform

def plot(bin_name, title='Raster Plot', mask=0, crop=None):
    """Create a plot of the data in an ArcGIS binary file."""
    
    from scipy import ndimage
    #http://scipy-lectures.github.io/advanced/image_processing/#edge-detection
    
    a, geotransform = read(bin_name, *crop)
    #a_mask = ma.masked_where(a < mask, a)

    fig=plt.figure(title + '_Afripop',figsize=(12,8))
    ax=plt.subplot(111)
    cmap='YlGnBu' #'YlOrBr'
    plt.imshow(a, interpolation='nearest', cmap=cmap, norm=LogNorm(vmin=1, vmax=1e3))
    ax.set(aspect=1)
    cb=plt.colorbar()
    plt.title(title + ' (Afripop)')
    cb.ax.set_ylabel(r'population ($\mathrm{km}^{-2}$)', rotation=270, labelpad=15)

    # correct no data (?) value of -3.4e38 to zero
    # so sums don't get messed up for cities by the ocean (e.g. Dakar)
    a[a<0]=0

    binary_img = a > mask
    open_img = ndimage.binary_opening(binary_img)
    close_img = ndimage.binary_closing(open_img)
    label_im, nb_labels = ndimage.label(close_img)
    print('Found %d labeled objects' % nb_labels)

    fig=plt.figure('village_labeling', figsize=(8,7))
    ax=plt.subplot(221)
    plt.title('binary')
    plt.imshow(binary_img, cmap='gray')
    ax=plt.subplot(222)
    plt.title('open')
    plt.imshow(open_img, cmap='gray')
    ax=plt.subplot(223)
    plt.title('close')
    plt.imshow(close_img, cmap='gray')
    ax=plt.subplot(224)
    plt.title('label')
    plt.imshow(label_im, cmap='spectral')

    pixel_sizes = ndimage.sum(close_img, label_im, range(nb_labels + 1))
    sum_vals = ndimage.sum(a, label_im, range(1, nb_labels + 1))

    fig=plt.figure('village_population_hist')
    plt.title('Population of labeled villages')
    plt.hist(sum_vals, bins=np.logspace(1, 7, num=50), alpha=0.5)
    plt.xscale("log")

    center_of_masses = ndimage.center_of_mass(a, label_im, range(1, nb_labels + 1))

    fig=plt.figure('nodes',figsize=(9,8))
    ax=plt.subplot(111)
    yy,xx = zip(*center_of_masses)
    sizes=[min(3e3,5+v/250.) for v in sum_vals]
    plt.title('Assignment of node populations')
    plt.imshow(a, interpolation='nearest', cmap=cmap, norm=LogNorm(vmin=1, vmax=1e3), alpha=0.8)
    plt.scatter(xx,yy,s=sizes, c=np.log10(sum_vals), cmap='RdYlBu_r', vmin=1, vmax=4, alpha=0.5)

    def make_nodes():
        ulX,cellsizeX,rotateX,ulY,rotateY,cellsizeY = geotransform
        cropY=crop[1][0] if crop[1] else 0
        def lat_from_raster_idx(y):
            return ulY+cellsizeY*(cropY+y)
        cropX=crop[0][0] if crop[0] else 0
        def lon_from_raster_idx(x):
            return ulX+cellsizeX*(cropX+x)
        nodes=[]
        for y,x,p in zip(yy,xx,sum_vals):
            n=Node(lat_from_raster_idx(y),lon_from_raster_idx(x),pop=p).toDict()
            nodes.append(n)
        return nodes

    with open('cache/GIS_nodes_%s.json' % title,'w') as fjson:
        json.dump(make_nodes(), fjson)

if __name__ == '__main__':
    plot(#bin_name='D:/Afripop/Nigeria-2013/NGA10adjv4.tif',
         #bin_name='D:/Afripop/Senegal/SEN10adjv5.tif',
         #bin_name='D:/Afripop/Guinee/GIN14adjv1.tif',
         #bin_name='D:/Afripop/Sierra_Leone/SLE14adjv1.tif',
         bin_name='D:/Afripop/Liberia/LBR14adjv1.tif',
         mask=3,

         #title='Kano',
         #crop=(range(6500,7500), 
         #      range(2000,3000))

         #title='Garki',
         #crop=(range(7100,9000), 
         #      range(1200,2400))

         #title='Senegal',
         #title='Guinee',
         #title='Sierra_Leone',
         title='Liberia',
         crop=(None,None)

         )
    plt.show()
