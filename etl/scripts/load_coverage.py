"""Load official/theoretical coverage polygons into ter.coverage_official."""
import argparse
from pathlib import Path

import geopandas as gpd
import pyogrio
from sqlalchemy import text
from pyproj import Transformer

from db import get_engine
from postgis_io import to_postgis_geom


OPERATOR_ALIASES = {
    "BOUY": "Bouygues Telecom",
    "FREE": "Free Mobile",
    "OF": "Orange",
    "SFR0": "SFR",
    "bouygues": "Bouygues Telecom",
    "free": "Free Mobile",
    "orange": "Orange",
    "sfr": "SFR",
}


def infer_operator(path: Path) -> str | None:
    text = path.name.lower()
    for token, name in OPERATOR_ALIASES.items():
        if token.lower() in text:
            return name
    return None


def infer_tech(path: Path) -> str | None:
    text = path.name.upper()
    if "_4G_" in text or "4G" in text:
        return "4G"
    if "_5G_" in text or "5G" in text:
        return "5G"
    return None


def parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    parts = [float(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("--bbox must be minx,miny,maxx,maxy in EPSG:4326")
    return parts[0], parts[1], parts[2], parts[3]


def bbox_for_source(path: Path, bbox_4326: tuple[float, float, float, float] | None) -> tuple[float, float, float, float] | None:
    if not bbox_4326:
        return None

    info = pyogrio.read_info(path)
    source_crs = info.get("crs")
    if not source_crs:
        return bbox_4326

    transformer = Transformer.from_crs("EPSG:4326", source_crs, always_xy=True)
    minx, miny, maxx, maxy = bbox_4326
    corners = [
        transformer.transform(minx, miny),
        transformer.transform(minx, maxy),
        transformer.transform(maxx, miny),
        transformer.transform(maxx, maxy),
    ]
    xs = [x for x, _ in corners]
    ys = [y for _, y in corners]
    return min(xs), min(ys), max(xs), max(ys)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="GPKG/SHP/GeoJSON coverage file or folder")
    parser.add_argument("--operator", default=None, help="Operator name override")
    parser.add_argument("--tech", choices=["4G", "5G"], default=None)
    parser.add_argument("--quality-col", default="niveau")
    parser.add_argument("--bbox", default=None, help="Optional EPSG:4326 bbox: minx,miny,maxx,maxy")
    parser.add_argument("--append", action="store_true", help="Append instead of replacing ter.coverage_official")
    args = parser.parse_args()
    bbox = parse_bbox(args.bbox)

    input_path = Path(args.input)
    files = sorted(path for path in input_path.rglob("*.gpkg") if path.is_file()) if input_path.is_dir() else [input_path]
    if not files:
        raise ValueError(f"No coverage files found in {input_path}")

    engine = get_engine()
    with engine.begin() as conn:
        if not args.append:
            conn.execute(text("TRUNCATE ter.coverage_official RESTART IDENTITY CASCADE"))

    for file_path in files:
        operator_name = args.operator or infer_operator(file_path)
        tech = args.tech or infer_tech(file_path)
        if not operator_name or not tech:
            raise ValueError(f"Cannot infer operator/tech from {file_path}; pass --operator and --tech")

        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO ter.ref_operator(name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
                {"name": operator_name},
            )
            operator_id = conn.execute(text("SELECT id FROM ter.ref_operator WHERE name = :name"), {"name": operator_name}).scalar_one()

        source_bbox = bbox_for_source(file_path, bbox)
        print(f"[LOAD] {file_path}")
        if source_bbox:
            print(f"[BBOX] {source_bbox}")
        gdf = gpd.read_file(file_path, bbox=source_bbox)
        if gdf.crs is None:
            gdf = gdf.set_crs(4326)
        else:
            gdf = gdf.to_crs(4326)
        gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
        if gdf.empty:
            print(f"[SKIP] {file_path}: no polygons in selected area")
            continue

        gdf["operator_id"] = operator_id
        gdf["tech"] = tech
        gdf["quality_class"] = gdf[args.quality_col].astype(str) if args.quality_col in gdf.columns else None
        gdf["source_name"] = str(file_path)
        out = gdf[["operator_id", "tech", "quality_class", "source_name", "geometry"]]
        print(f"[WRITE] {len(out)} polygons")
        to_postgis_geom(out, "coverage_official", engine)


if __name__ == "__main__":
    main()
