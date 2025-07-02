import argparse, numpy as np, rasterio, geopandas as gpd
from rasterio import features
from scipy.ndimage import gaussian_filter
from shapely.geometry import shape, Polygon


def hillshade(z, az=315, alt=45):
    x, y = np.gradient(z)
    slope = np.pi / 2 - np.arctan(np.hypot(x, y))
    aspect = np.arctan2(-x, y)
    a, b = np.radians(az), np.radians(alt)
    return (255 * (np.sin(b) * np.sin(slope) + np.cos(b) * np.cos(slope) * np.cos(a - aspect)).clip(0, 1)).astype(
        np.uint8)


def chaikin(poly: Polygon):
    ext = list(poly.exterior.coords)
    new = [ext[0]]
    for p0, p1 in zip(ext[:-1], ext[1:]):
        new.extend([(0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1]),
                    (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])])
    new.append(ext[-1])
    return Polygon(new, [ring.coords[:] for ring in poly.interiors])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem", required=True)
    ap.add_argument("--out", default="hillshade.geojson")
    ap.add_argument("--bands", type=int, default=8)
    ap.add_argument("--sigma", type=float, default=1.8)
    ap.add_argument("--min_pixels", type=int, default=3)
    args = ap.parse_args()

    with rasterio.open('../data/' + args.dem) as src:
        arr = src.read(1).astype(np.float32)
        nodata = src.nodata
        if nodata is not None:
            arr[arr == nodata] = np.nan

        arr = gaussian_filter(np.nan_to_num(arr), sigma=args.sigma)

        hs = hillshade(arr)
        quant = (hs / (256 / args.bands)).astype(np.uint8)

        px_area = abs(src.transform.a) * abs(src.transform.e)
        polys, shades = [], []
        for geom, val in features.shapes(quant, transform=src.transform):
            poly = shape(geom)
            if poly.area < args.min_pixels * px_area: continue
            polys.append(chaikin(poly))
            shades.append(int(val))

        gpd.GeoDataFrame({"shade": shades, "geometry": polys}, crs=src.crs).to_file('../data/' + args.out, driver="GeoJSON")
        print("Wrote", args.out)
