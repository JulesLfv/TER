"""Simple orchestrator for pilot region pipeline."""
import argparse
import subprocess


def run(cmd: list[str]) -> None:
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roads", required=True)
    parser.add_argument("--sites", required=True)
    parser.add_argument("--admin", required=False)
    parser.add_argument("--coverage", required=False)
    parser.add_argument("--sample-step", default="200")
    args = parser.parse_args()

    if args.admin:
        run(["python", "scripts/load_admin.py", "--input", args.admin, "--level", "department"])
    run(["python", "scripts/load_roads.py", "--input", args.roads, "--type-col", "highway", "--source-id-col", "osm_id"])
    run(["python", "scripts/load_sites.py", "--input", args.sites, "--format", "arcep-csv"])
    if args.coverage:
        run(["python", "scripts/load_coverage.py", "--input", args.coverage])
    run(["python", "scripts/sample_points.py"])
    run(["python", "scripts/compute_coverage_a.py"])
    if args.coverage:
        run(["python", "scripts/compute_coverage_b.py"])


if __name__ == "__main__":
    main()
