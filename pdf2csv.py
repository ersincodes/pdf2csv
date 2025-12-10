#!/usr/bin/env python3
import argparse
import csv
import re
import sys
from pathlib import Path
from typing import List, Dict, Iterable, Optional

import pdfplumber
from dateutil import parser as dateparser

CSV_HEADER = [
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

DEFAULT_MERCHANT = "PPS Perfunctio Payment Services GmbH"

ERROR_REASON_MAP = {
    "KC2-BL001": "User in the Blacklist",
}

PRODUCT_AMOUNT_BY_TWO_DIGIT = {
    "35": "39.90",
    "15": "54.90",
    "25": "54.90",
}

PRODUCT_AMOUNT_BY_PREFIX = {
    "PPS_DB_VPLUS1new": "54.90",
    "PPS_DB_VPLUS2new": "39.90",
    "PPS_DB_VPLUS3": "39.90",
}


def extract_text_lines(pdf_path: Path) -> List[str]:
    lines: List[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            for line in text.splitlines():
                cleaned = line.strip()
                if cleaned:
                    lines.append(cleaned)
    return lines


def find_date_yyyymmdd_in_filename(filename: str) -> str:
    match = re.search(r"(20\d{6})", filename)
    return match.group(1) if match else ""


def yyyymmdd_to_first_of_month(yyyymmdd: str) -> str:
    if not yyyymmdd:
        return ""
    dt = dateparser.parse(yyyymmdd)
    return f"{dt.year:04d}-{dt.month:02d}-01"


def detect_amount_from_filename(filename: str) -> str:
    # Explicit prefixes override the generic two digit mapping.
    for prefix, amount in PRODUCT_AMOUNT_BY_PREFIX.items():
        if filename.startswith(prefix):
            return amount

    # Look for a pattern like 15new / 25new / 35new anywhere in the filename
    m = re.search(r"(\d{2})new", filename)
    if m:
        two = m.group(1)
        if two in PRODUCT_AMOUNT_BY_TWO_DIGIT:
            return PRODUCT_AMOUNT_BY_TWO_DIGIT[two]
    return ""


def parse_records_from_lines(lines: List[str]) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    if not lines:
        return records

    # Skip header if it matches expected German headings
    start_index = 0
    header_regex = re.compile(r"^Dateiname\s+Name\s+Kundennummer\s+Fehler$")
    if header_regex.match(lines[0]):
        start_index = 1

    for line in lines[start_index:]:
        # Expect: <file> <name ...> <customerId> <errorCode>
        parts = line.split()
        if len(parts) < 4:
            continue
        filename_token = parts[0]
        error_code = parts[-1]
        customer_id = parts[-2]
        customer_name = " ".join(parts[1:-2])

        # Basic validation of id and error code
        if not re.fullmatch(r"\d+", customer_id):
            continue

        # Compute dates and references
        yyyymmdd = find_date_yyyymmdd_in_filename(filename_token)
        mandate_date = yyyymmdd_to_first_of_month(yyyymmdd)
        id_date_value = f"{customer_id}-{mandate_date}" if mandate_date else customer_id

        record: Dict[str, str] = {
            "STATUS": "REJECTED",
            "END TO END ID": "",
            "MERCHANT": DEFAULT_MERCHANT,
            "AMOUNT": detect_amount_from_filename(filename_token),
            "DUE DATE": "",
            "CUSTOMER BIC": "",
            "CUSTOMER IBAN": "",
            "CUSTOMER NAME": customer_name,
            "CUSTOMER ID": customer_id,
            "ADDITIONAL INFO 1": "",
            "ADDITIONAL INFO 2": "",
            "IMPORTED DATE": "",
            "MANDATE REFERENCE": "",
            "TRANSACTION INFORMATION": id_date_value,
            "TRANSACTION TYPE NAME": "",
            "ERROR CODE": error_code,
            "ERROR REASON": ERROR_REASON_MAP.get(error_code, ""),
            "MERCHANT PRODUCT NAME": "",
            "HAS CHARGEBACK": "",
        }
        records.append(record)

    return records


def write_csv(records: List[Dict[str, str]], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER, delimiter=";")
        writer.writeheader()
        for rec in records:
            row = {key: rec.get(key, "") for key in CSV_HEADER}
            writer.writerow(row)


def dump_text(pdf_path: Path, out_text_path: Path) -> None:
    lines = extract_text_lines(pdf_path)
    out_text_path.write_text("\n".join(lines), encoding="utf-8")


def iter_input_pdfs(path: Path) -> Iterable[Path]:
    if path.is_dir():
        for p in sorted(path.iterdir()):
            if p.is_file() and p.suffix.lower() == ".pdf":
                yield p
    else:
        yield path


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Extract ARMANDA/NETRON Fehlerreport PDFs to CSV")
    p.add_argument("input", type=Path, help="Path to input PDF file or a directory containing PDFs")
    p.add_argument("--out", type=Path, default=None, help="Output CSV path (single input only)")
    p.add_argument("--out-dir", type=Path, default=None, help="Directory to write CSVs when processing a directory")
    p.add_argument(
        "--dump-text",
        type=Path,
        default=None,
        help="Optional path to write extracted text for parser development (single input only)",
    )
    return p


def process_single(pdf_path: Path, out: Optional[Path], dump_text_path: Optional[Path]) -> None:
    if dump_text_path is not None:
        dump_text(pdf_path, dump_text_path)
        print(f"Wrote text dump to {dump_text_path}")

    records = parse_records_from_lines(extract_text_lines(pdf_path))
    out_path = out if out is not None else pdf_path.with_suffix(".csv")
    write_csv(records, out_path)
    print(f"Wrote CSV to {out_path} with {len(records)} records")


def main(argv: List[str]) -> int:
    args = build_arg_parser().parse_args(argv)

    in_path: Path = args.input
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        return 1

    if in_path.is_dir():
        out_dir: Path = args.out_dir if args.out_dir is not None else in_path
        out_dir.mkdir(parents=True, exist_ok=True)
        for pdf in iter_input_pdfs(in_path):
            process_single(pdf, out=out_dir / pdf.with_suffix(".csv").name, dump_text_path=None)
    else:
        process_single(in_path, out=args.out, dump_text_path=args.dump_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
