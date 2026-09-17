#!/usr/bin/env python
import numpy as np
import netCDF4 as nc
import xarray as xr
import xesmf as xe
import argparse

parser = argparse.ArgumentParser(description="script to convert DeepMIP topo into GFDL ocean bathymetry")
parser.add_argument("-i","--input", help="input topography at high resolution")
parser.add_argument("-o","--output", help="output ocean bathymetry for GFDL model")
args = parser.parse_args()

gridfile = 'ocean_hgrid.nc'

f = nc.Dataset(gridfile,'r')
oc_x = f.variables['x'][:]
oc_y = f.variables['y'][:]
f.close()

f = nc.Dataset(args.input,'r')
topo = f.variables['topo'][:]
lat = f.variables['lat'][:]
lon = f.variables['lon'][:]
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

# Then make conservative remapping to ocean grid
grid_oc = xr.Dataset(coords={
    "lon": (("y","x"), oc_x[1::2,1::2]),
    "lat": (("y","x"), oc_y[1::2,1::2]),
    "lon_b": (("y_b","x_b"), oc_x[0::2,0::2]),
    "lat_b": (("y_b","x_b"), oc_y[0::2,0::2])  
    })

print('doing second remapping')
remap_2 = xe.Regridder(grid_025, grid_oc, method="conservative_normed")
bathy = -1.0 * remap_2(topo_cent) # flip sign for bathymetry
bathy[bathy < 0] = 0

ny, nx = bathy.shape

f = nc.Dataset(args.output,'w')
f.history = f'make_topog.py on {args.input} \n'

f.createDimension('ny' ,ny)
f.createDimension('nx', nx)
f.createDimension('ntiles', 1)

topo_o = f.createVariable('depth', 'f8', ('ny','nx'))
topo_o.units = 'metres'
topo_o[:] = bathy[:]

f.close()
