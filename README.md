# pdf-marker

Kötegelt PDF-ből Markdown konverter, a [`marker-pdf`](https://github.com/VikParuchuri/marker) AI könyvtár segítségével.

## Követelmények

- Python 3.12.11+
- [`uv`](https://github.com/astral-sh/uv) csomagkezelő

## Telepítés

```powershell
uv sync
```

Az első futtatáskor a szükséges AI modell súlyok automatikusan letöltődnek a Hugging Face-ről (ez néhány percet vehet igénybe).

## Használat

1. Másold a PDF fájlokat az `input_pdfs/` mappába.
2. Futtasd a konvertert:

```powershell
uv run python main.py
```

3. Az eredmények az `output_markdowns/<fájlnév>/` mappában találhatók:
   - `<fájlnév>.md` — a kinyert Markdown szöveg
   - a PDF-ből kivont képek a Markdown fájl mellett

Mindkét mappa automatikusan létrejön, ha még nem létezik.

## Működési elv

A `main.py` megkeresi az `input_pdfs/` mappában lévő `*.pdf` fájlokat, egyszer betölti az AI modelleket a `ModelRegistry` segítségével, majd a megosztott `artifact_dict`-et átadja a `PdfConverter`-nek — ezzel elkerülve a modellek ismételt betöltését minden egyes fájlnál. Minden PDF-et a saját almappájába ment az `output_markdowns/` könyvtáron belül.
