#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path
from typing import List

EXPECTED_HEADER = [
    "STATUS",
    "END TO END ID",
    "MERCHANT",
    "AMOUNT",
    "DUE DATE",
    "CUSTOMER BIC",
    "CUSTOMER IBAN",
    "CUSTOMER NAME",
    "CUSTOMER ID",
    "ADDITIONAL INFO 1",
    "ADDITIONAL INFO 2",
    "IMPORTED DATE",
    "MANDATE REFERENCE",
    "TRANSACTION INFORMATION",
    "TRANSACTION TYPE NAME",
    "ERROR CODE",
    "ERROR REASON",
    "MERCHANT PRODUCT NAME",
    "HAS CHARGEBACK",
]

MANDATE_LIKE_RE = re.compile(r"^\d{6,}-\d{4}-\d{2}-\d{2}$")


def normalize_row(fields: List[str]) -> List[str]:
    if len(fields) == len(EXPECTED_HEADER):
        return fields

    fixed = [""] * len(EXPECTED_HEADER)

    # Copy early stable columns 0..8 (up to CUSTOMER ID)
    for i in range(min(9, len(fields))):
        fixed[i] = fields[i]

    # Detect the ID-date value and error code region
    id_date_idx = next((i for i, v in enumerate(fields) if MANDATE_LIKE_RE.match(v or "")), None)

    if id_date_idx is not None:
        # Place into TRANSACTION INFORMATION (index 13)
        fixed[13] = fields[id_date_idx]

    # Attempt to locate error code and reason near the end
    # Find last non-empty tokens and place them into 15 and 16 if plausible
    tail = [i for i, v in enumerate(fields) if v]
    if tail:
        # Error code often before reason
        if len(tail) >= 2:
            fixed[15] = fields[tail[-2]]
            fixed[16] = fields[tail[-1]]
        else:
            fixed[15] = fields[tail[-1]]

    return fixed


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: fix_csv.py <input.csv> <output.csv>", file=sys.stderr)
        return 2
    src = Path(argv[0])
    dst = Path(argv[1])

    with src.open(encoding="utf-8") as f_in, dst.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.reader(f_in, delimiter=";")
        writer = csv.writer(f_out, delimiter=";")
        # Always write expected header
        writer.writerow(EXPECTED_HEADER)
        header = next(reader, None)
        for fields in reader:
            fixed = normalize_row(fields)
            writer.writerow(fixed)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
