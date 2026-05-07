"""Load administrative boundaries into ter.admin_boundary.
Expected columns (or mappable): level, code, name, geometry.
"""
import argparse
import geopandas as gpd
from sqlalchemy import text
from db import get_engine
from postgis_io import to_postgis_geom


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to admin boundaries (GeoJSON/GPKG/SHP)")
    parser.add_argument("--level", default="department", help="Boundary level label")
    parser.add_argument("--name-col", default=None, help="Name column override")
    parser.add_argument("--code-col", default=None, help="Code column override")
    args = parser.parse_args()

    gdf = gpd.read_file(args.input)
    gdf = gdf.to_crs(4326)

    name_col = args.name_col or next((col for col in ["name", "nom", "libelle", "libgeo"] if col in gdf.columns), None)
    code_col = args.code_col or next((col for col in ["code", "code_insee", "insee", "dep"] if col in gdf.columns), None)

    if not name_col:
        raise ValueError(f"Input must contain a name column. Available columns: {', '.join(gdf.columns)}")
    if code_col:
        gdf["code"] = gdf[code_col].astype(str)
    else:
        gdf["code"] = None
    gdf["name"] = gdf[name_col].astype(str)

    records = gdf[["code", "name", "geometry"]].copy()
    records["level"] = args.level

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ter.admin_boundary WHERE level = :level"), {"level": args.level})
    to_postgis_geom(records, "admin_boundary", engine)


if __name__ == "__main__":
    main()
