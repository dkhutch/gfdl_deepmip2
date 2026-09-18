#!/usr/bin/env python
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import xesmf as xe
import xarray as xr
from fortranformat import FortranRecordWriter as frw
import argparse

parser = argparse.ArgumentParser(description="convert DeepMIP vegetation from LPJ-Guess types into GFDL vegetation")
parser.add_argument("-i","--input", help="input vegetation of LPJ-Guess types")
args = parser.parse_args()

atmosgridfile = 'atmos_hgrid.nc'
landmaskfile = 'land_mask.nc'
coverncfile = 'cover_type_field.nc'
coverfile = 'cover_type_field'
groundfile = 'ground_type_field'


'''
LM2 types (for CM2.1):
0      ocean
1 (BE) broadleaf evergreen trees
2 (BD) broadleaf deciduous trees
3 (BN) broadleaf/needleleaf trees
4 (NE) needleleaf evergreen trees
5 (ND) needleleaf deciduous trees
6 (G)  grassland
7 (D)  desert
8 (T)  tundra
9 (A)  agriculture
10 (I)  ice
'''

'''
LPJ_Guess types:
2: Mixed temperate forest
3: Mixed warm temperate / subtropical forest
4: Broadleaf evergreen tropical forest
5: Broadleaf deciduous tropical forest
6: temperate woodland
7: tropical woodland
8: semidesert shrubland
9: desert 
'''

def lpj_convert(v):
    vo = np.zeros(v.shape, 'i4')
    vo[v==2] = 3
    vo[v==3] = 3
    vo[v==4] = 1
    vo[v==5] = 2
    vo[v==6] = 5
    vo[v==7] = 4
    vo[v==8] = 8
    vo[v==9] = 7

    return vo


f = nc.Dataset(args.input,'r')
pft = f.variables['DeepMIP_Biome_Hybrid_RASTER3'][:]
lat = f.variables['lat'][:]
lon = f.variables['lon'][:]
f.close()

lonmat, latmat = np.meshgrid(lon,lat)

ny, nx = pft.shape

f = nc.Dataset(atmosgridfile,'r')
at_x = f.variables['x'][:]
at_y = f.variables['y'][:]
f.close()

f = nc.Dataset(landmaskfile,'r')
mask = f.variables['mask'][:]
f.close()

cm2_veg = lpj_convert(pft)

vmask = ~pft.mask # using ESMF conventions

surf_grid = xr.Dataset(coords={
    "lon": (("y","x"), lonmat),
    "lat": (("y","x"), latmat),
    "mask": (("y","x"), vmask)
    },
    data_vars={
    "veg": (("y","x"), pft)
    })

at_grid = xr.Dataset(coords={
    "lon": (("y","x"), at_x[1::2, 1::2]),
    "lat": (("y","x"), at_y[1::2, 1::2])
    })

regridder = xe.Regridder(surf_grid, at_grid, method="nearest_s2d")

d_in = surf_grid["veg"]
veg_at = regridder(d_in)
veg_at = veg_at.data

veg_at[mask == 0] = 0
lat_at = at_y[1::2,0]
lon_at = at_x[0,1::2]

nlat, nlon = veg_at.shape

ground = 2 * np.ones((nlat, nlon), 'i4')
ground[mask == 0] = 0

f = nc.Dataset(coverncfile,'w')
f.history = f'convert_lpj_cm2.1.py on {args.input} \n'

f.createDimension('lat', nlat)
f.createDimension('lon', nlon)

lat_o = f.createVariable('lat', 'f8', ('lat'))
lat_o.units = 'degrees_north'
lat_o[:] = lat_at[:]

lon_o = f.createVariable('lon', 'f8', ('lon'))
lon_o.units = 'degrees_east'
lon_o[:] = lon_at[:]

veg_o = f.createVariable('veg', 'i4', ('lat','lon'), fill_value=0)
veg_o.units = 'CM2.1 veg types'
veg_o[:] = veg_at[:]

f.close()


nline = 40
ntot = nlat * nlon

nblock = nlon // nline
nrem = nlon % nline

fmt = frw('40i2')

f = open(coverfile,'w')
f2 = open(groundfile, 'w')
f.write(' %d,  %d,   0.\n' % (nlon, nlat))
f.write('(40i2)\n')
f2.write(' %d,  %d,   0.\n' % (nlon, nlat))
f2.write('(40i2)\n')
for i in range(nlat):
    for j in range(nblock):
        f.write(fmt.write(veg_at[i,j*nline:(j+1)*nline]) + '\n')
        f2.write(fmt.write(ground[i,j*nline:(j+1)*nline]) + '\n')
    if nrem != 0:
        f.write(fmt.write(veg_at[i,nline*nblock:]) + '\n')
        f2.write(fmt.write(ground[i,nline*nblock:]) + '\n')
f.close()
f2.close()

