import csv
import re
from html.parser import HTMLParser
from openpyxl import Workbook

TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
SEPARATOR_CELL_RE = re.compile(r"^[-: ]+$")
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
HTML_TABLE_RE = re.compile(r"<table\b.*?</table>", re.IGNORECASE | re.DOTALL)

class _HtmlTableParser(HTMLParser):
    """Egy HTML <table> sorait és celláit gyűjti ki (colspan/rowspan nélkül)."""
    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append("\n")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

def extract_html_tables(text):
    """A szövegben található HTML táblázatokat listák listájaként adja vissza."""
    tables = []
    for match in HTML_TABLE_RE.finditer(text):
        parser = _HtmlTableParser()
        parser.feed(match.group(0))
        if parser.rows:
            tables.append(parser.rows)
    return tables

def extract_tables_from_markdown(md_text):
    """A markdown szövegben található pipe-táblázatokat listák listájaként adja vissza."""
    tables = []
    current_table = []
    for line in md_text.splitlines():
        if TABLE_ROW_RE.match(line):
            cells = [
                BR_RE.sub("\n", cell).strip()
                for cell in line.strip().strip("|").split("|")
            ]
            if all(SEPARATOR_CELL_RE.match(cell) for cell in cells):
                continue  # fejléc-elválasztó sor
            if not any(cells):
                continue  # teljesen üres sor (a marker táblázatok végén gyakori)
            current_table.append(cells)
        elif current_table:
            tables.append(current_table)
            current_table = []
    if current_table:
        tables.append(current_table)
    return tables

def save_tables(tables, file_output_dir, stem):
    for i, table in enumerate(tables, start=1):
        csv_path = file_output_dir / f"{stem}_table_{i}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            csv.writer(csvfile).writerows(table)

    wb = Workbook()
    wb.remove(wb.active)
    for i, table in enumerate(tables, start=1):
        ws = wb.create_sheet(title=f"Table_{i}")
        for row in table:
            ws.append(row)
    wb.save(file_output_dir / f"{stem}_tables.xlsx")
