import argparse, numpy as np, rasterio, geopandas as gpd
from rasterio import features
from scipy.ndimage import gaussian_filter
from shapely.geometry import shape

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem", required=True)
    ap.add_argument("--out", default="contour_polygons.geojson")
    ap.add_argument("--interval", type=float, default=50.0)
    ap.add_argument("--sigma", type=float, default=1.8)
    args = ap.parse_args()

    with rasterio.open(args.dem) as src:
        z = src.read(1).astype(np.float32)
        if src.nodata is not None:
            z[z == src.nodata] = np.nan
        z = gaussian_filter(np.nan_to_num(z), sigma=args.sigma)

        # quantise to bands
        band_ids = (np.floor(z / args.interval)).astype(np.int16)

        polys, elev_min, elev_max = [], [], []
        for geom, band_id in features.shapes(band_ids, transform=src.transform):
            if band_id == -32768:  # nodata guard
                continue
            polys.append(shape(geom))
            elev_min.append(band_id * args.interval)
            elev_max.append((band_id + 1) * args.interval)

        gdf = gpd.GeoDataFrame(
            {"elev_min": elev_min, "elev_max": elev_max, "geometry": polys},
            crs=src.crs
        )
        gdf.to_file(args.out, driver="GeoJSON")

    print("✓ wrote", args.out)
