#!/usr/bin/env python
import numpy as np
import netCDF4 as nc
import os
import argparse

parser = argparse.ArgumentParser(description="Script to adjust isolated grid cells and narrow gateways")
parser.add_argument("-i","--input", help="interpolated topography without adjustments")
parser.add_argument("-o","--output", help="output ocean bathymetry for GFDL model with adjustment")
args = parser.parse_args()

straitfile = 'straits.txt'
autofillfile = 'fill.nc'

if not os.path.exists(args.output):
    cmd = f'cp {args.input} {args.output}'
    os.system(cmd)

f = nc.Dataset(args.output,'r+')
f.history = 'adjust_topo.py on %s \n' % args.input

if 'ntiles' not in f.dimensions:
    f.createDimension('ntiles',1)

depth = f.variables['depth']

data = depth[:]
ny, nx = data.shape

min_depth = 40.
shallow = np.logical_and(data > 0., data < min_depth)
data[shallow] = min_depth

fill = np.zeros((ny,nx), 'bool')
dig = np.zeros((ny,nx), 'bool')

fill[0, :] = True

if os.path.exists(autofillfile):
    fa = nc.Dataset(autofillfile,'r')
    autofill = fa.variables['fill'][:]
    fa.close()
    autofill = autofill.astype('bool')
    fill[autofill] = True
else:
    autofill = np.zeros((ny,nx), 'bool')

### Begin insert manual adjustments


### End insert manual adjustments

data[fill] = 0.
data[dig] = min_depth


depth0 = np.reshape(data[:,-1], (ny, 1))
depth1 = np.reshape(data[:,0], (ny, 1))
depth_pad = np.concatenate((depth0, data, depth1), axis=1)



for j in range(1,ny-1):
    for i in range(1,nx):
        if depth_pad[j,i] > 0:
            upper = depth_pad[j+1,i] == 0
            lower = depth_pad[j-1,i] == 0
            right = depth_pad[j,i+1] == 0
            left = depth_pad[j,i-1] == 0

            if ((upper and lower) or (right and left)):
                # straits[j,i] = 2
                # fs.write('fill[%d, %d] = True\n' % (j, i-1))
                autofill[j, i-1] = True

auto_sum = np.sum(autofill)
print('sum of autofill', auto_sum)

fo = nc.Dataset(autofillfile,'w')

fo.createDimension('ny',ny)
fo.createDimension('nx',nx)

fill_o = fo.createVariable('fill', 'b', ('ny','nx'))
fill_o[:] = autofill[:]

fo.close()

depth[:] = data[:]
f.close()