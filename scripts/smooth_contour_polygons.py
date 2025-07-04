import argparse, geopandas as gpd, rasterio
from shapely.geometry import Polygon, LineString

def chaikin(poly: Polygon):
    ext = list(poly.exterior.coords)
    new = [ext[0]]
    for p0, p1 in zip(ext[:-1], ext[1:]):
        new.extend([
            (0.75*p0[0] + 0.25*p1[0], 0.75*p0[1] + 0.25*p1[1]),
            (0.25*p0[0] + 0.75*p1[0], 0.25*p0[1] + 0.75*p1[1])
        ])
    new.append(ext[-1])
    return Polygon(new, [ring.coords[:] for ring in poly.interiors])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="inp", required=True, help="input GeoJSON (polygons)")
    ap.add_argument("--dem", required=True, help="original DEM GeoTIFF (needed for pixel size)")
    ap.add_argument("--out", default="contour_polygons_smooth.geojson")
    ap.add_argument("--min_pixels", type=int, default=3)
    ap.add_argument("--iterations", type=int, default=1, help="Chaikin iterations")
    args = ap.parse_args()

    with rasterio.open(args.dem) as src:
        px_area = abs(src.transform.a * src.transform.e)   # width * height (metres²)

    min_area = args.min_pixels * px_area if args.min_pixels > 0 else 0

    gdf = gpd.read_file(args.inp)

    kept_rows = []

    for idx, row in gdf.iterrows():
        geom = row.geometry
        if isinstance(geom, Polygon) and geom.area < min_area:
            continue
        if isinstance(geom, Polygon) and args.iterations:
            for _ in range(args.iterations):
                geom = chaikin(geom)
        row.geometry = geom # update geometry in-place
        kept_rows.append(row)

    out_gdf = gpd.GeoDataFrame(kept_rows, columns=gdf.columns, crs=gdf.crs)
    out_gdf.to_file(args.out, driver="GeoJSON")
    print(f"✓ wrote {args.out}  – kept {len(out_gdf)} features")
