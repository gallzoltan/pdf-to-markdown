# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses `uv` for dependency and environment management (Python 3.12.11).

```powershell
# Install dependencies
uv sync

# Run the converter
uv run python main.py
```

## Architecture

A single-script batch PDF-to-Markdown converter built on the [`marker-pdf`](https://github.com/VikParuchuri/marker) library.

**Flow in `main.py`:**
1. Scans `./input_pdfs/` for `*.pdf` files.
2. Loads AI models via `ModelRegistry` (downloads weights from Hugging Face on first run).
3. Passes a shared `artifact_dict` (loaded models) into `PdfConverter` — this avoids reloading models for each file.
4. For each PDF: runs conversion, writes `./output_markdowns/<stem>/<stem>.md` and any extracted images alongside it.

**I/O directories** are created automatically if missing; dropping PDFs into `input_pdfs/` and running `main.py` is the full workflow.
