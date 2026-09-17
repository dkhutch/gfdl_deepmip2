#!/bin/bash

deepmip_dir="/g/data/y99/dkh157/DeepMIP2/boundary_conditions"
topogfile="${deepmip_dir}/deepmip2-eocene-paleogeography_20260624.nc"

# 1. Interp topography to ocean grid
./make_topog.py -i ${topogfile} -o topog_conserve.nc

# 2. Adjust for narrow straits and isolated grid cells

# 3. Make coupler exchange grids

# 4. Make atmosphere topography

# 5. Create input file for mountain drag parameterisation

# 6. Create river runoff

# 7. Make Vegetation from DeepMIP input files

# 8. Make soil type and groundwater field

# 9. Set greenhouse gases

# 10. Set aerosol forcing

# 11. Make tidal forcing fields (bottom roughness)

# 12. Make temperature-salinity restart file for the ocean