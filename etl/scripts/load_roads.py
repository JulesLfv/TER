"""Load and filter roads into ter.road_segment.
Expected source fields: road_name (optional), road_type/class, geometry.
"""
import argparse
import geopandas as gpd
from sqlalchemy import text
from db import get_engine
from postgis_io import to_postgis_geom

DEFAULT_TYPES = {"motorway": "A", "trunk": "VR", "primary": "N", "secondary": "D", "A": "A", "N": "N", "D": "D"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--type-col", default="road_type")
    parser.add_argument("--name-col", default="name")
    parser.add_argument("--source-id-col", default="id")
    parser.add_argument("--keep", default="A,VR,N,D")
    args = parser.parse_args()

    gdf = gpd.read_file(args.input).to_crs(4326)
    gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])].copy()

    if args.type_col not in gdf.columns:
        raise ValueError(f"Missing type column: {args.type_col}")

    gdf["road_type"] = gdf[args.type_col].astype(str).map(lambda v: DEFAULT_TYPES.get(v, v))
    keep = set([k.strip() for k in args.keep.split(",") if k.strip()])
    gdf = gdf[gdf["road_type"].isin(keep)].copy()

    if args.name_col in gdf.columns:
        gdf["road_name"] = gdf[args.name_col]
    else:
        gdf["road_name"] = None

    if args.source_id_col in gdf.columns:
        gdf["source_id"] = gdf[args.source_id_col].astype(str)
    else:
        gdf["source_id"] = None

    gdf_2154 = gdf.to_crs(2154)
    gdf["length_m"] = gdf_2154.geometry.length
    gdf["region_code"] = None
    gdf["dept_code"] = None

    out = gdf[["source_id", "road_name", "road_type", "length_m", "region_code", "dept_code", "geometry"]]
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE ter.road_segment RESTART IDENTITY CASCADE"))
    to_postgis_geom(out, "road_segment", engine)


if __name__ == "__main__":
    main()
