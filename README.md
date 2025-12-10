## PDF2CSV

Convert PPS Fehlerreport PDFs into normalized CSV files.

### Features

- Extracts customer, error code, and transaction info from PPS Fehlerreport PDFs.
- Detects amounts from filename patterns and fills the CSV header expected by PPS.
- Optional helper `fix_csv.py` to normalize semi-broken CSV exports into the exact header shape.

### Requirements

- Python 3.10+
- `pdfplumber`, `python-dateutil` (see `requirements.txt`)

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage

Convert a single PDF to CSV (auto-creates `<pdfname>.csv` next to the PDF):

```bash
./.venv/bin/python pdf2csv.py "ARMANDA_NEW_Fehlerreport_20250808.pdf"
```

Specify a custom output path:

```bash
./.venv/bin/python pdf2csv.py "ARMANDA_NEW_Fehlerreport_20250808.pdf" --out "ARMANDA_NEW_Fehlerreport_20250808.csv"
```

Process all PDFs in a directory and write CSVs beside them:

```bash
./.venv/bin/python pdf2csv.py /path/to/pdf-folder
```

Dump extracted text for debugging the parser:

```bash
./.venv/bin/python pdf2csv.py "NETRON_Fehlerreport_20250808.pdf" --dump-text out.txt
```

Normalize an existing semi-broken CSV export to the expected header (semicolon-delimited):

```bash
./.venv/bin/python fix_csv.py input.csv output-fixed.csv
```

### CSV Header (output)

`STATUS;END TO END ID;MERCHANT;AMOUNT;DUE DATE;CUSTOMER BIC;CUSTOMER IBAN;CUSTOMER NAME;CUSTOMER ID;ADDITIONAL INFO 1;ADDITIONAL INFO 2;IMPORTED DATE;MANDATE REFERENCE;TRANSACTION INFORMATION;TRANSACTION TYPE NAME;ERROR CODE;ERROR REASON;MERCHANT PRODUCT NAME;HAS CHARGEBACK`
