"""Download public source datasets for TER and report missing/failed sources."""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests

DEFAULT_TIMEOUT = 45
PROJECT_ROOT = Path(__file__).resolve().parent
ARCEP_COVERAGE_INDEX = "https://data.arcep.fr/mobile/couvertures_theoriques/last/Metropole/00_Metropole/"
ARCEP_OPERATORS = {
    "bouygues": "BOUY",
    "free": "FREE",
    "orange": "OF",
    "sfr": "SFR0",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.links.append(value)


@dataclass
class Source:
    key: str
    filename: str
    required: bool = True
    note: str = ""
    url: str | None = None
    index_url: str | None = None
    pattern: str | None = None


def build_sources() -> list[Source]:
    sources = [
        Source(
            key="roads_fr_geofabrik_pbf",
            url="https://download.geofabrik.de/europe/france-latest.osm.pbf",
            filename="roads/france-latest.osm.pbf",
            required=True,
            note="Routes OSM (à convertir/filtrer ensuite)",
        ),
        Source(
            key="arcep_sites_metropole",
            index_url="https://data.arcep.fr/mobile/sites/last/",
            pattern=r"_sites_Metropole\.csv$",
            filename="sites/arcep_sites_2g_3g_4g_5g.csv",
            required=True,
            note="Sites radio ARCEP Métropole (dernier millésime)",
        ),
        Source(
            key="admin_dept_geojson",
            url="https://france-geojson.gregoiredavid.fr/repo/departements.geojson",
            filename="admin/departements.geojson",
            required=True,
            note="Limites départements (fallback simple)",
        ),
    ]

    for operator_name, operator_code in ARCEP_OPERATORS.items():
        for tech in ("4G", "5G"):
            sources.append(
                Source(
                    key=f"arcep_coverage_{operator_name}_{tech.lower()}",
                    index_url=ARCEP_COVERAGE_INDEX,
                    pattern=rf"_couv_Metropole_{operator_code}_{tech}_data\.gpkg\.7z$",
                    filename=f"coverage/{operator_name}/arcep_couverture_{operator_name}_{tech.lower()}.gpkg.7z",
                    required=False,
                    note=f"Couverture ARCEP {operator_name} {tech} Métropole (archive 7z)",
                )
            )

    return sources


SOURCES: list[Source] = build_sources()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def resolve_url(src: Source, timeout: int = DEFAULT_TIMEOUT) -> tuple[bool, str]:
    if src.url:
        return True, src.url
    if not src.index_url or not src.pattern:
        return False, "missing url or index_url/pattern"

    try:
        response = requests.get(src.index_url, timeout=timeout)
        if response.status_code != 200:
            return False, f"index HTTP {response.status_code}"
    except requests.RequestException as e:
        return False, f"index error: {e}"

    parser = LinkParser()
    parser.feed(response.text)
    matcher = re.compile(src.pattern)
    for link in parser.links:
        absolute = urljoin(src.index_url, link)
        if matcher.search(absolute):
            return True, absolute
    return False, f"no link matching {src.pattern}"


def stream_download(url: str, output: Path, timeout: int = DEFAULT_TIMEOUT) -> tuple[bool, str]:
    try:
        headers = {"User-Agent": "TER-data-downloader/0.1"}
        with requests.get(url, stream=True, timeout=timeout, headers=headers) as r:
            if r.status_code != 200:
                return False, f"HTTP {r.status_code}"
            ensure_parent(output)
            with output.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        return True, "ok"
    except requests.RequestException as e:
        return False, str(e)


def write_report(rows: Iterable[dict], report_path: Path) -> None:
    ensure_parent(report_path)
    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["key", "required", "status", "message", "url", "local_path", "note"],
        )
        writer.writeheader()
        writer.writerows(rows)


def extract_7z_archives(output_dir: Path, extract_dir: Path) -> list[dict]:
    rows = []
    seven_zip = shutil.which("7z") or shutil.which("7za")
    archives = sorted(output_dir.glob("coverage/**/*.7z"))

    if not archives:
        return rows

    if not seven_zip:
        return [
            {
                "archive": str(archive),
                "status": "failed",
                "message": "7z/7za not found",
                "extract_dir": str(extract_dir),
            }
            for archive in archives
        ]

    for archive in archives:
        relative_parent = archive.relative_to(output_dir).parent
        target_dir = extract_dir / relative_parent / archive.stem
        target_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [seven_zip, "x", "-y", f"-o{target_dir}", str(archive)],
            check=False,
            capture_output=True,
            text=True,
        )
        rows.append(
            {
                "archive": str(archive),
                "status": "extracted" if result.returncode == 0 else "failed",
                "message": "ok" if result.returncode == 0 else (result.stderr or result.stdout).strip(),
                "extract_dir": str(target_dir),
            }
        )
    return rows


def write_extract_report(rows: Iterable[dict], report_path: Path) -> None:
    rows = list(rows)
    if not rows:
        return
    ensure_parent(report_path)
    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["archive", "status", "message", "extract_dir"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "data/raw"), help="Base output directory")
    parser.add_argument("--report", default=str(PROJECT_ROOT / "data/raw/download_report.csv"), help="CSV report path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--skip-existing", action="store_true", help="Do not download files that already exist")
    parser.add_argument("--dry-run", action="store_true", help="Resolve URLs and write the report without downloading")
    parser.add_argument("--extract", action="store_true", help="Extract downloaded .7z coverage archives with 7z/7za")
    parser.add_argument(
        "--extract-dir",
        default=str(PROJECT_ROOT / "data/processed"),
        help="Base folder for extracted coverage archives",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    report_path = Path(args.report).resolve()

    print(f"[INFO] Download folder: {output_dir}")
    results: list[dict] = []

    for src in SOURCES:
        target = output_dir / src.filename
        print(f"[GET] {src.key} -> {target}")
        ok, resolved = resolve_url(src, timeout=args.timeout)
        if ok and args.skip_existing and target.exists():
            status = "skipped"
            msg = "already exists"
            url = resolved
        elif ok and args.dry_run:
            status = "resolved"
            msg = "dry run"
            url = resolved
        elif ok:
            url = resolved
            ok, msg = stream_download(url, target, timeout=args.timeout)
            status = "downloaded" if ok else "failed"
        else:
            url = src.index_url or src.url or ""
            msg = resolved
            status = "failed"

        results.append(
            {
                "key": src.key,
                "required": "yes" if src.required else "no",
                "status": status,
                "message": msg,
                "url": url,
                "local_path": str(target),
                "note": src.note,
            }
        )

    write_report(results, report_path)

    if args.extract and not args.dry_run:
        extract_rows = extract_7z_archives(output_dir, Path(args.extract_dir).resolve())
        extract_report = report_path.with_name("extract_report.csv")
        write_extract_report(extract_rows, extract_report)
        print(f"Extract report: {extract_report}")

    failed_required = [r for r in results if r["status"] == "failed" and r["required"] == "yes"]
    failed_optional = [r for r in results if r["status"] == "failed" and r["required"] == "no"]

    print("\n=== DOWNLOAD SUMMARY ===")
    print(f"Report: {report_path}")
    print(f"Required failed: {len(failed_required)}")
    for r in failed_required:
        print(f"  - {r['key']}: {r['message']}")
    print(f"Optional failed: {len(failed_optional)}")
    for r in failed_optional:
        print(f"  - {r['key']}: {r['message']}")

    if failed_required:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
