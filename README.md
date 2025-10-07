# SAIL GTX – PDF Conversion Runner (Surya + Marker)

This repo compares two PDF-to-text pipelines:

- **Surya**: best for scanned or image-heavy PDFs (OCR).
- **Marker**: best for digital PDFs with selectable text (layout-aware Markdown).

It includes a runner script, a CSV log of runs, and example PDFs so anyone can reproduce results.

---

## 1) Requirements

- macOS or Linux
- Python 3.12
- Git

---

## 2) Setup the environment (pip + venv)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt` should contain:
```
marker-pdf
surya-ocr
psutil
pillow
pypdf
```

Notes:
- First runs may download model weights. Allow several minutes the first time Surya or Marker executes.
- Keep `.venv/` out of git. A `.gitignore` is provided.

---

## 3) Project layout

```
sailgtx-intern/
├── runner.py
├── research-notes.md
├── runs_log.csv
├── requirements.txt
├── README.md
├── examples/
│   ├── digital/
│   │   └── sample-local-pdf.pdf
│   ├── scanned/
│   │   └── image-based-pdf-sample.pdf
│   └── large/
│       └── 2025HTSRev24.pdf
└── out/                 # created by runs; ignored by git
```

- `examples/digital/` holds PDFs with selectable text.
- `examples/scanned/` holds image-based or scanned PDFs.
- `examples/large/` holds very large PDFs for stress tests (for example, the 2025 HTS book).

---

## 4) Verify the CLIs

After installing requirements, confirm the tools are on PATH:

```bash
marker --help
surya_ocr --help
```

Expected:
- Marker usage looks like: `marker [OPTIONS] IN_FOLDER`
- Surya usage looks like: `surya_ocr [OPTIONS] INPUT_PATH`

---

## 5) Quick start: run the examples (single PDF per run)

Activate your venv, then run:

### A) Digital PDF with Marker
```bash
python runner.py examples/digital/sample-local-pdf.pdf --tool marker --timeout 300
```
Result:
- Markdown at `out/sample-local-pdf.marker.md`
- Row appended to `runs_log.csv`

### B) Scanned PDF with Surya
```bash
python runner.py examples/scanned/image-based-pdf-sample.pdf --tool surya --timeout 300
```
Result:
- Surya output directory at `out/image-based-pdf-sample.surya/`
- Row appended to `runs_log.csv`

### C) Compare both on the same file
```bash
python runner.py <path/to.pdf> --tool both --timeout 600
```

### D) Large PDF stress test
```bash
python runner.py examples/large/2025HTSRev24.pdf --tool both --timeout 600
```

---

## 6) What the runner does

For a single input PDF, the runner:

- Executes the selected tool(s).
  - **Surya**: runs `surya_ocr INPUT_PDF --output_dir <temp>` then copies outputs to `out/<stem>.surya/`.
  - **Marker**: requires a folder input; the runner creates a temp folder and calls `marker <IN_DIR> --output_dir <OUT_DIR>`, then copies the first `.md` to `out/<stem>.marker.md`.
- Measures runtime and captures the last lines of output for debugging.
- Appends a row to `runs_log.csv` with:
  
  `tool,input_pdf,output_path,runtime_s,return_code,output_bytes,output_files,stderr_tail`

Return code:
- `0` means success.
- Nonzero means failure or timeout (runner uses `124` for timeouts).

---

## 7) Command-line reference

`runner.py` arguments (single-PDF runner):

- `pdf` (positional): path to the PDF to process.
- `--tool {surya|marker|both}`: which pipeline to run. Default is `both`.
  - Use `surya` for scanned or image-heavy PDFs.
  - Use `marker` for digital PDFs with selectable text.
- `--outdir DIR`: where outputs are written. Default `out`.
- `--logcsv FILE`: CSV log file. Default `runs_log.csv`.
- `--timeout SECONDS`: per-tool timeout. Default `120`. Use `300–600` for first runs or large PDFs.

Examples:
```bash
python runner.py examples/digital/sample-local-pdf.pdf --tool marker --timeout 300
python runner.py examples/scanned/image-based-pdf-sample.pdf --tool surya --timeout 300
python runner.py examples/large/2025HTSRev24.pdf --tool both --timeout 600
```

---

## 8) Replicating reference results

Observed on a Mac laptop with CPU:

- `image-based-pdf-sample.pdf` (scanned):
  - Surya: about 19 s after warmup (first-ever run was about 67 s due to model download).
  - Marker: completed in about 178 s because OCR models ran on CPU.
- `sample-local-pdf.pdf` (digital):
  - Marker: about 24 s. Produced Markdown.

Times vary by hardware and load. First runs can be slower if model weights need to download.

---

## 9) Adding and organizing test PDFs

Place files under `examples/`:

- `examples/digital/`: product pages, product catalogs, spec sheets where text is selectable. Include files with headings, lists, and tables.
- `examples/scanned/`: scans and image-only PDFs. Include pages with rotated text, varied fonts and sizes, and embedded images.
- `examples/large/`: very large PDFs to stress test throughput and memory.

Then run the runner as shown above and review outputs in `out/` and timings in `runs_log.csv`.

---

## 10) Troubleshooting

- **Marker says “unexpected extra argument”**:
  - Use the minimal supported form: `marker <IN_DIR> --output_dir <OUT_DIR>`.
- **Marker seems very slow on scans**:
  - On macOS, some OCR models fall back to CPU. Prefer Surya for scanned PDFs.
- **Surya is slow on first run**:
  - Models are downloading and initializing. Increase `--timeout` for the first run, then reduce.
- **Command not found**:
  - Ensure your venv is active: `source .venv/bin/activate`.

---

## 11) Notes on routing

A simple rule of thumb:
- If the PDF has little selectable text or many images, use **Surya**.
- If the PDF has abundant selectable text and light images, use **Marker**.

You can implement a triage step by inspecting text length and image density, then choose the tool accordingly.

---

## 12) Repro checklist

- Create venv and `pip install -r requirements.txt`.
- Verify `marker --help` and `surya_ocr --help`.
- Run Marker on `examples/digital/sample-local-pdf.pdf`.
- Run Surya on `examples/scanned/image-based-pdf-sample.pdf`.
- Optional: run both on the large HTS book with a higher timeout.
- Confirm outputs in `out/` and rows in `runs_log.csv`.
