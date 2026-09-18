#!/usr/bin/env python
import numpy as np
import netCDF4 as nc
import xarray as xr
import xesmf as xe
import argparse

parser = argparse.ArgumentParser(description="script to convert DeepMIP topo into GFDL atmos topography")
parser.add_argument("-i","--input", help="input topography at high resolution")
parser.add_argument("-o","--output", help="output atmos topography for GFDL model")
args = parser.parse_args()

atmosgridfile = 'atmos_hgrid.nc'
maskfile = 'land_mask.nc'

f = nc.Dataset(args.input,'r')
topo = f.variables['topo'][:]
f.close()

f = nc.Dataset(atmosgridfile,'r')
at_x = f.variables['x'][:]
at_y = f.variables['y'][:]
f.close()

f = nc.Dataset(maskfile,'r')
lmask = f.variables['mask'][:]
f.close()

topo = topo.astype('f8')

# here use knowledge of the fact that it's a 0.25 deg grid that ends at 180 lon
grid_025 = xe.util.grid_global(0.25, 0.25, lon1=180)

grid_corners = xr.Dataset(coords={
    "lon": (("y","x"), grid_025.lon_b.data),
    "lat": (("y","x"), grid_025.lat_b.data)
})

grid_at = xr.Dataset(coords={
    "lon": (("y","x"), at_x[1::2, 1::2]),
    "lat": (("y","x"), at_y[1::2, 1::2]),
    "lon_b": (("y_b","x_b"), at_x[0::2,0::2]),
    "lat_b": (("y_b","x_b"), at_y[0::2,0::2])  
    })

# First remap the corner grid to centred grid
print('doing first remapping')
remap_1 = xe.Regridder(grid_corners, grid_025, method="bilinear")
topo_cent = remap_1(topo.data)

print('doing second remapping')
remap_2 = xe.Regridder(grid_025, grid_at, method="conservative_normed")
topo_at = remap_2(topo_cent)
topo_at[topo_at < 0] = 0
topo_s = np.mean(topo_at[0,:])
topo_at[0,:] = topo_s

topo_at[lmask < 0.001] = 0

grav = 9.8

phis = topo_at * grav
phis = phis[np.newaxis, :, :]

lat_at = at_y[1::2,0]
lon_at = at_x[0,1::2]

nlat, nlon = topo_at.shape

f = nc.Dataset(args.output,'w')
f.history = f'atmos_topog.py on {args.input} \n'

f.createDimension('lat', nlat)
f.createDimension('lon', nlon)
f.createDimension('Time', 1)

lat_o = f.createVariable('lat', 'f8', ('lat'))
lat_o.units = 'degrees_north'
lat_o[:] = lat_at[:]

lon_o = f.createVariable('lon', 'f8', ('lon'))
lon_o.units = 'degrees_east'
lon_o[:] = lon_at[:]

topo_o = f.createVariable('topo', 'f8', ('lat','lon'))
topo_o.units = 'metres a.s.l.'
topo_o[:] = topo_at[:]

phis_o = f.createVariable('Surface_geopotential', 'f8', ('Time','lat','lon'))
phis_o.long_name = 'Surface Geopotential'
phis_o.units = 'm**2/s**2'
phis_o[:] = phis[:]

f.close()

