python pdf2csv.py "ARMANDA_NEW_Fehlerreport_20250808.pdf" --out "ARMANDA_NEW_Fehlerreport_20250808.csv"

python3 -m venv .venv
source .venv/bin/activate

./.venv/bin/python pdf2csv.py "NETRON_Fehlerreport_20250808.pdf"
./.venv/bin/python pdf2csv.py "ARMANDA_NEW_Fehlerreport_20250808.pdf"
./.venv/bin/python pdf2csv.py "NOVANET_Fehlerreport_20250908.pdf"
