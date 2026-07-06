"""Malaysia lom.agc.gov.my (Laws of Malaysia Online) parsing + citation helpers.

lom.agc.gov.my serves each principal Act as a server-rendered page addressed by a numeric
`act` coordinate (e.g. `act-detail.php?act=883`). The page embeds a pdf.js viewer whose
`data-src` attribute points at the official consolidated PDF - there is no HTML body text and
no JSON-LD metadata block (unlike Malta), so the title is derived from the official PDF's own
filename (never invented - it is the filename the Attorney-General's Chambers itself assigns).

Citation contract:
- `eli_uri`: Malaysia has no ELI. This is the durable lom.agc.gov.my act page URL, keyed on the
  portal's own numeric act coordinate. NEVER invented.
- `human_readable_citation`: the Act title as derived from the official PDF filename.
- `source_url`: the same lom.agc.gov.my act page URL.
"""

from __future__ import annotations

import re
from io import BytesIO
from typing import Any
from urllib.parse import unquote

BASE_URL = "https://lom.agc.gov.my"
_PDF_SRC_RE = re.compile(r'data-src="pdfjs/web/viewer\.html\?file=([^"&]+)&', re.IGNORECASE)
_TRAILING_PAREN_RE = re.compile(r"\s*\((?:Revised|Reprint)[^)]*\)\s*$", re.IGNORECASE)


def act_page_url(act_number: int, language: str = "BI") -> str:
    return f"{BASE_URL}/act-detail.php?language={language}&act={act_number}"


def extract_pdf_path(html: str) -> str | None:
    """Extract the (relative, URL-encoded) PDF path from the pdf.js viewer's ``data-src``."""
    m = _PDF_SRC_RE.search(html)
    return unquote(m.group(1)) if m else None


def resolve_pdf_url(relative_path: str) -> str:
    """Resolve a viewer-relative PDF path (e.g. ``../../../ilims/upload/...pdf``) against the
    site root - the portal serves ``act-detail.php`` at the root, so any number of leading
    ``../`` segments collapses to the root, exactly as a browser would resolve it."""
    path = relative_path.lstrip("./")
    while path.startswith("../"):
        path = path[3:]
    return f"{BASE_URL}/{path}"


def title_from_pdf_path(relative_path: str) -> str | None:
    """Derive a human-readable title from the official PDF's own filename."""
    filename = relative_path.rsplit("/", 1)[-1]
    if filename.lower().endswith(".pdf"):
        filename = filename[:-4]
    filename = _TRAILING_PAREN_RE.sub("", filename).strip()
    return filename or None


def build_record(html: str, act_number: int, language: str = "BI") -> dict[str, Any]:
    """Build a citation-bearing record from an ``act-detail.php`` page."""
    pdf_path = extract_pdf_path(html)
    title = title_from_pdf_path(pdf_path) if pdf_path else None
    page_url = act_page_url(act_number, language)
    return {
        "act_number": act_number,
        "title": title,
        "pdf_path": pdf_path,
        "eli_uri": page_url,
        "human_readable_citation": title,
        "source_url": page_url,
    }


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract plain text from an Act PDF using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    parts = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt.strip())
    text = "\n".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
