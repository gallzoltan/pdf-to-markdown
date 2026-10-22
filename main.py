import csv
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from tables import extract_tables_from_markdown, save_tables

INPUT_DIR = Path("./input_pdfs")
OUTPUT_DIR = Path("./output_markdowns")

def create_csv_report(pdf_files, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Fájl Név", "Feldolgozás Eredménye"])
        for pdf in pdf_files:
            writer.writerow([pdf.name, "Sikeres" if pdf.exists() else "Nem található"])

def batch_convert_pdfs():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[-] Nem található PDF fájl a '{INPUT_DIR}' mappában.")
        return

    print(f"[*] {len(pdf_files)} fájl található. Konverter inicializálása...")
    print("[*] (Az első futtatáskor a háttérben letöltődnek a szükséges AI modellek, ez eltarthat pár percig.)")

    print("[*] AI modellek betöltése...")
    artifact_dict = create_model_dict()

    converter = PdfConverter(artifact_dict=artifact_dict)
    
    for pdf_path in pdf_files:
        print(f"\n[+] Feldolgozás alatt: {pdf_path.name}")
        try:
            # 4. Konvertálás futtatása
            rendered = converter(str(pdf_path))
            
            # Az eredmények kinyerése
            full_text = rendered.markdown
            images = rendered.images
            
            # Kimeneti mappa a fájl nevével
            file_output_dir = OUTPUT_DIR / pdf_path.stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # 5. A Markdown szöveg mentése
            md_file_path = file_output_dir / f"{pdf_path.stem}.md"
            with open(md_file_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            # 6. Táblázatok mentése CSV-be és XLSX-be (ha vannak)
            tables = extract_tables_from_markdown(full_text)
            if tables:
                save_tables(tables, file_output_dir, pdf_path.stem)
                print(f"[✓] {len(tables)} táblázat mentve CSV és XLSX formátumban.")

            # 7. A képek mentése (ha vannak)
            if images:
                for img_name, img_data in images.items():
                    img_path = file_output_dir / img_name
                    img_data.save(img_path)
            
            print(f"[✓] Sikeresen mentve ide: {md_file_path}")
            
        except Exception as e:
            print(f"[X] Hiba történt a {pdf_path.name} feldolgozása közben: {e}")

if __name__ == "__main__":
    batch_convert_pdfs()