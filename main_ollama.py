import base64
import io
import json
import os
import sys
import urllib.request
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pypdfium2 as pdfium
from tables import extract_html_tables, extract_tables_from_markdown, save_tables

INPUT_DIR = Path("./input_pdfs")
OUTPUT_DIR = Path("./output_markdowns_ollama")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "glm-ocr")
PROMPT = "Text Recognition:"  # GLM-OCR dokumentum-feldolgozó promptja
RENDER_SCALE = 2  # 72 dpi * 2 = 144 dpi
REQUEST_TIMEOUT = 600

def ollama_generate(image_png):
    """Egy oldalkép felismerése az Ollama natív /api/generate végpontján."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": PROMPT,
        "images": [base64.b64encode(image_png).decode("ascii")],
        "stream": False,
        "options": {"temperature": 0},
    }
    request = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return json.load(response)["response"].strip()

def check_ollama():
    """Ellenőrzi, hogy fut-e az Ollama és le van-e töltve a modell."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=10) as response:
            models = [m["name"] for m in json.load(response)["models"]]
    except OSError as e:
        print(f"[-] Az Ollama nem érhető el ({OLLAMA_HOST}): {e}")
        return False
    if not any(name.split(":")[0] == OLLAMA_MODEL.split(":")[0] for name in models):
        print(f"[-] A '{OLLAMA_MODEL}' modell nincs letöltve. Futtasd: ollama pull {OLLAMA_MODEL}")
        return False
    return True

def render_pages(pdf_path):
    """A PDF oldalait PNG képekként adja vissza."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        for page in pdf:
            image = page.render(scale=RENDER_SCALE).to_pil()
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            yield buffer.getvalue()
    finally:
        pdf.close()

def batch_convert_pdfs():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[-] Nem található PDF fájl a '{INPUT_DIR}' mappában.")
        return

    if not check_ollama():
        return

    print(f"[*] {len(pdf_files)} fájl található. Modell: {OLLAMA_MODEL} ({OLLAMA_HOST})")

    for pdf_path in pdf_files:
        print(f"\n[+] Feldolgozás alatt: {pdf_path.name}")
        try:
            pages = []
            for page_no, image_png in enumerate(render_pages(pdf_path), start=1):
                print(f"    - {page_no}. oldal...")
                pages.append(ollama_generate(image_png))
            full_text = "\n\n".join(pages)

            # Kimeneti mappa a fájl nevével
            file_output_dir = OUTPUT_DIR / pdf_path.stem
            file_output_dir.mkdir(parents=True, exist_ok=True)

            md_file_path = file_output_dir / f"{pdf_path.stem}.md"
            with open(md_file_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            # A GLM-OCR a táblázatokat HTML-ként vagy markdownként is adhatja
            tables = extract_html_tables(full_text) + extract_tables_from_markdown(full_text)
            if tables:
                save_tables(tables, file_output_dir, pdf_path.stem)
                print(f"[✓] {len(tables)} táblázat mentve CSV és XLSX formátumban.")

            print(f"[✓] Sikeresen mentve ide: {md_file_path}")

        except Exception as e:
            print(f"[X] Hiba történt a {pdf_path.name} feldolgozása közben: {e}")

if __name__ == "__main__":
    batch_convert_pdfs()
