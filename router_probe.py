"""
router_probe.py
Quick heuristic to suggest Surya vs Marker for a PDF.

Usage:
    python router_probe.py path/to/file.pdf
"""

from typing import Literal, Tuple
from pypdf import PdfReader
from pdfminer.high_level import extract_text
import sys, json

Decision = Literal["surya", "marker", "both"]

def probe_pdf(path: str) -> dict:
    # Try to extract text with pdfminer
    try:
        txt = extract_text(path) or ""
    except Exception:
        txt = ""
    text_len = len(txt.strip())

    # Count images with pypdf
    reader = PdfReader(path)
    n_pages = len(reader.pages)
    image_count = 0
    for page in reader.pages:
        rsrc = page.get("/Resources")
        if rsrc:
            xobj = rsrc.get("/XObject")
            if xobj:
                for _, obj in xobj.items():
                    try:
                        if obj.get("/Subtype") == "/Image":
                            image_count += 1
                    except Exception:
                        pass
    density = image_count / max(n_pages, 1)

    return {
        "pages": n_pages,
        "text_len": text_len,
        "image_count": image_count,
        "image_density": density
    }

def route(path: str) -> Tuple[Decision, float, dict]:
    m = probe_pdf(path)

    # Heuristic rules:
    #  - If almost no text, or images dominate (density >= 0.8) → Surya (OCR)
    #  - If lots of text and low image density (<0.3) → Marker
    #  - Else, fall back to "both"
    if m["text_len"] < 200 or m["image_density"] >= 0.8:
        return "surya", 0.8, m
    if m["text_len"] > 1500 and m["image_density"] < 0.3:
        return "marker", 0.8, m
    return "both", 0.6, m

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python router_probe.py file.pdf")
        sys.exit(1)

    decision, conf, metrics = route(sys.argv[1])
    print(json.dumps({
        "decision": decision,
        "confidence": conf,
        "metrics": metrics
    }, indent=2))
