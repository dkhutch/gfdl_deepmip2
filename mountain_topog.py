#!/usr/bin/env python
import numpy as np 
import netCDF4 as nc 
import xarray as xr
import xesmf as xe
import argparse

parser = argparse.ArgumentParser(description="script to convert DeepMIP topo into subgrid-scale mountain topography")
parser.add_argument("-i","--input", help="input topography at high resolution")
parser.add_argument("-o","--output", help="output mountain drag topography for GFDL model")
args = parser.parse_args()

f = nc.Dataset(args.input,'r')
lat = f.variables['lat'][:]
lon = f.variables['lon'][:]
topo = f.variables['topo'][:]
f.close()

topo = topo.astype('f8')

# here use knowledge of the fact that it's a 0.25 deg grid that ends at 180 lon
grid_025 = xe.util.grid_global(0.25, 0.25, lon1=180)

grid_corners = xr.Dataset(coords={
    "lon": (("y","x"), grid_025.lon_b.data),
    "lat": (("y","x"), grid_025.lat_b.data)
})

# First remap the corner grid to centred grid
print('doing first remapping')
remap_1 = xe.Regridder(grid_corners, grid_025, method="bilinear")
topo_cent = remap_1(topo.data)

# Get rid of negative topography
topo_cent[topo_cent<0] = 0.
ny, nx = topo_cent.shape

xdat_deg = grid_corners.lon[0,:]
ydat_deg = grid_corners.lat[:,0]

xdat = np.deg2rad(xdat_deg)
ydat = np.deg2rad(ydat_deg)

fo = nc.Dataset(args.output,'w')
fo.history = f'make_mountain_topog_mio.py on {args.input} \n '

fo.createDimension('x',nx)
fo.createDimension('y',ny)
fo.createDimension('x1',1)
fo.createDimension('x2',nx+1)
fo.createDimension('x3',ny+1)

z_o = fo.createVariable('zdat','f4',('y','x'))
z_o[:] = topo_cent[:]
z_o.units = 'metres'

x_o = fo.createVariable('xdat','f4',('x2'))
x_o[:] = xdat[:]
x_o.units = 'longitude radians'

y_o = fo.createVariable('ydat','f4',('x3'))
y_o[:] = ydat[:]
y_o.units = 'latitude radians'

ipts = fo.createVariable('ipts','f4',('x1'))
ipts[:] = nx

jpts = fo.createVariable('jpts','f4',('x1'))
jpts[:] = ny

fo.close()

