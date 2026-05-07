"""Convert OSM PBF roads to a GeoJSON file consumable by load_roads.py."""
import argparse
import shutil
import subprocess
from pathlib import Path


DEFAULT_WHERE = "highway IN ('motorway','trunk','primary','secondary')"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input .osm.pbf file")
    parser.add_argument("--output", required=True, help="Output roads GeoJSON")
    parser.add_argument("--where", default=DEFAULT_WHERE)
    args = parser.parse_args()

    ogr2ogr = shutil.which("ogr2ogr")
    if not ogr2ogr:
        raise SystemExit("ogr2ogr not found. Install GDAL: sudo apt install gdal-bin")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ogr2ogr,
        "-f",
        "GeoJSON",
        str(output),
        str(Path(args.input)),
        "lines",
        "-where",
        args.where,
        "-select",
        "osm_id,name,highway",
        "-lco",
        "RFC7946=YES",
        "-overwrite",
    ]
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
