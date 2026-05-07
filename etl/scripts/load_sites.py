"""Load radio sites into ter.radio_site from ARCEP CSV or vector point files."""
import argparse
import geopandas as gpd
import pandas as pd
from sqlalchemy import text
from db import get_engine
from postgis_io import to_postgis_geom


TECH_COLUMNS = {"4G": "site_4g", "5G": "site_5g"}


def read_sites(args: argparse.Namespace) -> gpd.GeoDataFrame:
    if args.format == "arcep-csv" or args.input.lower().endswith(".csv"):
        df = pd.read_csv(args.input, sep=args.csv_sep, dtype=str)
        required = [args.operator_col, args.site_id_col, args.lon_col, args.lat_col]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required ARCEP CSV columns: {', '.join(missing)}")

        rows = []
        for tech, col in TECH_COLUMNS.items():
            if col not in df.columns:
                continue
            subset = df[df[col].astype(str).str.strip().isin(["1", "true", "True", "TRUE"])].copy()
            subset["tech"] = tech
            rows.append(subset)
        if not rows:
            raise ValueError("No 4G/5G site columns found or no active 4G/5G sites")

        expanded = pd.concat(rows, ignore_index=True)
        lon = pd.to_numeric(expanded[args.lon_col].str.replace(",", ".", regex=False), errors="coerce")
        lat = pd.to_numeric(expanded[args.lat_col].str.replace(",", ".", regex=False), errors="coerce")
        valid = lon.notna() & lat.notna()
        expanded = expanded[valid].copy()
        lon = lon[valid]
        lat = lat[valid]
        return gpd.GeoDataFrame(expanded, geometry=gpd.points_from_xy(lon, lat), crs=4326)

    gdf = gpd.read_file(args.input).to_crs(4326)
    return gdf[gdf.geometry.type == "Point"].copy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--format", choices=["auto", "arcep-csv", "vector"], default="auto")
    parser.add_argument("--operator-col", default="nom_op")
    parser.add_argument("--tech-col", default="tech")
    parser.add_argument("--site-id-col", default="num_site")
    parser.add_argument("--band-col", default="band")
    parser.add_argument("--lon-col", default="longitude")
    parser.add_argument("--lat-col", default="latitude")
    parser.add_argument("--csv-sep", default=";")
    args = parser.parse_args()

    gdf = read_sites(args)

    for col in [args.operator_col, args.tech_col]:
        if col not in gdf.columns:
            raise ValueError(f"Missing required column: {col}")

    engine = get_engine()
    # Ensure operator reference exists
    operators = sorted(gdf[args.operator_col].dropna().astype(str).unique())
    with engine.begin() as conn:
        for op in operators:
            conn.execute(text("INSERT INTO ter.ref_operator(name) VALUES (:name) ON CONFLICT (name) DO NOTHING"), {"name": op})

    # map operator name to id
    with engine.begin() as conn:
        res = conn.execute(text("SELECT id, name FROM ter.ref_operator"))
        op_map = {name: oid for oid, name in res.fetchall()}

    gdf["operator_id"] = gdf[args.operator_col].astype(str).map(op_map)
    gdf["tech"] = gdf[args.tech_col].astype(str).str.upper()
    gdf = gdf[gdf["tech"].isin(["4G", "5G"])]
    gdf["site_id"] = gdf[args.site_id_col].astype(str) if args.site_id_col in gdf.columns else None
    gdf["band"] = gdf[args.band_col].astype(str) if args.band_col in gdf.columns else None
    gdf["source_name"] = args.input

    out = gdf[["site_id", "operator_id", "tech", "band", "source_name", "geometry"]]
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE ter.radio_site RESTART IDENTITY CASCADE"))
    to_postgis_geom(out, "radio_site", engine)


if __name__ == "__main__":
    main()
