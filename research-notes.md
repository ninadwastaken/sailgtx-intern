# Week 1 Research Notes

Goal: Run Surya + Marker locally, capture outputs, compare runtime, size, and quality.  
Deliverable: Notes and logs that show the pipeline works and that we understand tool behavior.

---

## Document 1: image-based-pdf-sample.pdf (scanned)

**Surya**  
- Runtime: ~19s on warm run (initial run was ~67s due to model download/init)  
- Return code: 0 (success)  
- Output: `out/image-based-pdf-sample.surya/` (1 JSON file, ~190 KB)  
- Quality: OCR line recognition completed, progress bar showed all 12 pages processed. Good fit for image/scanned input.  
- Issues: First-ever run needed longer timeout for model download; after warmup, runs are ~20s.  

**Marker**  
- Runtime: ~178s  
- Return code: 0 (success)  
- Output: out/image-based-pdf-sample.marker.md  
- Quality: Markdown produced, but processing is very slow on scanned PDFs due to CPU OCR fallback.  
- Notes: Warning shows table model not compatible with MPS and defaults to CPU; for scanned/image PDFs, prefer Surya.  

**Conclusion:** For scanned PDFs, Surya is clearly the right choice. Marker is not practical on CPU for these.

---

## Document 2: sample-local-pdf.pdf (digital/text-based)

**Surya**  
- Not tested yet. Expected to still work but not needed for digital PDFs.  

**Marker**  
- Runtime: ~24s  
- Return code: 0  
- Output: out/sample-local-pdf.marker.md (~9 KB)  
- Quality: Clean Markdown output with headings and paragraphs preserved  

---

## General Notes

- Surya CLI: `surya_ocr INPUT --output_dir OUT_DIR`  
- Marker CLI: `marker IN_DIR --output_dir OUT_DIR` (no `convert`, no `--paginate_output false`).  
- Timeouts: Surya ~20–90s after warmup (first run may need 180–600s for model download). Marker ~20–30s for digital PDFs; ~3+ minutes for scanned PDFs on this Mac due to CPU OCR fallback.  
- Hardware: On Mac (MPS backend), Marker’s table model falls back to CPU. That’s acceptable for digital PDFs, but too slow for scans.  

---

## Router Implication

- Route **scanned/image-heavy PDFs → Surya**  
- Route **digital/text PDFs → Marker**  

This matches the benchmarks and avoids Marker’s CPU fallback issues on scans.
