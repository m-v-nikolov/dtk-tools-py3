"""Utilities for reading and plotting ArcGIS binary files.

This module contains some simple functions to make it easier
to read and plot the data contained in the binary grid files
produced by ArcGIS.

"""
import sys
import copy
import json
import numpy as np
from numpy import ma
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
from node import Node

def read(bingrid_name, cropX=None, cropY=None):
    """Read the data field and headers from an ArcGIS binary grid

    This function reads the header and data from the ArcGIS binary
    data files produced by the "Raster to Float" tool in ArcGIS 9.1

    """
    
    if bingrid_name[-4:] == '.flt':
        hdr_name = bingrid_name[:-4]
        bin_name = bingrid_name
    else:
        hdr_name = bingrid_name
        bin_name = bingrid_name + '.flt'

    header = read_headers(hdr_name)

    nrows = int(header['nrows'])
    rows = cropY if cropY else range(nrows)

    ncols = int(header['ncols'])
    cols = cropX if cropX else range(ncols)

    #print(rows,cols)

    a = np.zeros(shape=(len(rows),len(cols)),dtype=np.float32)

    with open(bin_name, "rb") as f:
        if rows[0] > 0:
            f.read(rows[0]*ncols*4) # skip first bunch of rows
        for i,irow in enumerate(rows):
            if cols[0] > 0:
                f.read(cols[0]*4)
            data = np.fromstring(f.read(len(cols)*4),dtype=np.float32)
            a[i][:] = data
            if cols[-1] != ncols-1:
                f.read((ncols-1-cols[-1])*4)


    return a, header

def read_headers(bingrid_name):
    """Read the ascii headers of the ArcGIS binary grid file

    The headers have the following format:
    
    ncols         62
    nrows         121
    xllcorner     -288595.47161281
    yllcorner     -3158065.5722693
    cellsize      1000
    NODATA_value  -9999
    byteorder     LSBFIRST
    """

    hdr_name = bingrid_name + '.hdr'
    f=open(hdr_name,'r')
    tab_read=f.readlines()
    f.close()

    headers={}
    for i,line in enumerate(tab_read):
        k,v=line.split()
        if i<6:
            v=float(v)
        headers[k]=v
    print(headers)
    return headers

def plot(bin_name, title='Raster Plot', mask=0, crop=None):
    """Create a plot of the data in an ArcGIS binary file."""
    
    from scipy import ndimage
    #http://scipy-lectures.github.io/advanced/image_processing/#edge-detection
    
    a, headers = read(bin_name, *crop)
    #a_mask = ma.masked_where(a < mask, a)

    fig=plt.figure(title,figsize=(12,8))
    ax=plt.subplot(111)
    cmap='YlGnBu' #'YlOrBr'
    plt.imshow(a, interpolation='nearest', cmap=cmap, norm=LogNorm(vmin=1, vmax=1e3))
    ax.set(aspect=1)
    cb=plt.colorbar()
    plt.title(title)
    cb.ax.set_ylabel(r'population ($\mathrm{km}^{-2}$)', rotation=270, labelpad=15)

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
        cellsize=headers['cellsize']
        cropY=crop[1][0]
        def lat_from_raster_idx(y):
            return headers['yllcorner']+cellsize*(headers['nrows']-(cropY+y))
        cropX=crop[0][0]
        def lon_from_raster_idx(x):
            return headers['xllcorner']+cellsize*(cropX+x)
        nodes=[]
        for y,x,p in zip(yy,xx,sum_vals):
            nodes.append(Node(lat_from_raster_idx(y),lon_from_raster_idx(x),pop=p).toDict())
        return nodes

    with open('GIS_nodes.json','w') as fjson:
        json.dump(make_nodes(), fjson)

if __name__ == '__main__':
    plot(bin_name='D:/Afripop/Nigeria/apnga10v4.flt',
         mask=30,

         #title='Greater Kano (AfriPop)',
         #crop=(range(6500,7500), 
         #      range(2000,3000))

         title='Garki District (AfriPop)',
         crop=(range(7100,9000), 
               range(1200,2400))

         )
    plt.show()
