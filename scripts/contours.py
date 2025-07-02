import os
import rasterio
import numpy as np
from scipy.ndimage import uniform_filter, median_filter

def smooth(input_path, window_size):
    output_path = "../data/contours_smoothed.tif"

    with rasterio.open(input_path) as src:
        dem = src.read(1).astype(np.float32)  # convert to float for NaN support
        profile = src.profile
        nodata = src.nodata

    # mask nodata
    if nodata is not None:
        dem[dem == nodata] = np.nan

    # apply uniform (mean) filter
    # smoothed = uniform_filter(np.nan_to_num(dem), size=window_size)
    smoothed = median_filter(np.nan_to_num(dem), size=window_size)

    # restore nodata if needed
    if nodata is not None:
        smoothed[np.isnan(dem)] = nodata

    # save output
    profile.update(dtype='float32')
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(smoothed.astype(np.float32), 1)

    return output_path

def generate_geojson(input_path):
    contours_path = "../data/contours.geojson" # output contour lines

    contour_interval = 10.0  # elevation step in meters
    os.system(f"gdal_contour -a elev -i {contour_interval} {input_path} {contours_path}")

    return contours_path

input_path = "../data/AW3D30.tif"

# 3x3 smoothing
window_size = 3 # focal window size (5 = 5x5 mean filter)
smoothed_path = smooth(input_path, window_size)
#print(f"Done: saved smoothed contours to", smoothed_path)

generate_geojson(smoothed_path)
