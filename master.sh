#!/bin/bash

deepmip_dir="/g/data/y99/dkh157/DeepMIP2/boundary_conditions"
topogfile="${deepmip_dir}/deepmip2-eocene-paleogeography_20260624.nc"

# 1. Interp topography to ocean grid
# ./make_topog.py -i ${topogfile} -o topog_conserve.nc

# 2. Adjust for narrow straits and isolated grid cells
# Do several iterations to ensure grid cell adjustment has "converged"
# for i in {01..06}; do 
# ./adjust_topo.py -i topog_conserve.nc -o topog.nc
# done

# 2a. Make manual adjustments to topog
# TODO: David will add in manual adjustments here.

# 3. Make coupler exchange grids
# ./make_coupler_mosaic --atmos_mosaic atmos_mosaic.nc --ocean_mosaic ocean_mosaic.nc --ocean_topog topog.nc --land_mosaic land_mosaic.nc 
# mv mosaic.nc grid_spec.nc

# 4. Make atmosphere topography, and append to atmos restart file:
# ./atmos_topog.py -i ${topogfile} -o atmos_topog.nc
# ncks -A -v Surface_geopotential atmos_topog.nc fv_rst.res.nc

# 5. Create input file for mountain drag parameterisation
./mountain_topog.py -i ${topogfile} -o mountain_topog.nc

# 6. Make Vegetation from DeepMIP input files

# 7. Make soil type and groundwater field

# 8. Create river runoff

# 9. Set greenhouse gases

# 10. Set aerosol forcing

# 11. Make tidal forcing fields (bottom roughness)

# 12. Make temperature-salinity restart file for the ocean