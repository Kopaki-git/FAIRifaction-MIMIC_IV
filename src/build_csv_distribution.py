"""Package the five canonical CSV tables as the ZIP file of the CSV distribution.

The ZIP is the file behind https://w3id.org/FAIR-course-UT/2026/group04/dataset/mimic-iv/csv.
It contains the CSVs byte for byte, under a mimic_icu_vitals_4h/ folder. Timestamps and
permissions are fixed, the members are sorted and stored uncompressed (compressed bytes can
differ between zlib versions), so rebuilding from unchanged CSVs gives a byte-identical ZIP.

Usage: python src/build_csv_distribution.py [--source DIR] [--output PATH]
"""

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "derived" / "mimic_icu_vitals_4h"
DEFAULT_OUTPUT = ROOT / "data" / "derived" / "mimic_icu_vitals_4h.zip"

TABLES = [
    "careunit_intervals.csv",
    "first_ranked_diagnoses.csv",
    "hospital_admissions.csv",
    "icu_stays.csv",
    "observations.csv",
]
FIXED_TIME = (1980, 1, 1, 0, 0, 0)  # earliest date ZIP can store; the real date would vary per build


def build(source: Path, output: Path) -> None:
    """Write the ZIP, failing if any of the five tables is missing."""
    with zipfile.ZipFile(output, "w") as zf:
        for name in TABLES:
            info = zipfile.ZipInfo(f"{source.name}/{name}", date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            zf.writestr(info, (source / name).read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.source, args.output)
    print(f"Wrote {len(TABLES)} tables to {args.output}")


if __name__ == "__main__":
    main()
