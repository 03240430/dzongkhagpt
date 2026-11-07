import io
import os
import re

MAX_FILE_MB = 10
ALLOWED = (".pdf", ".docx", ".txt")


class DocumentError(Exception):
    """A readable error message that can be shown to the user."""


def clean_text(text: str) -> str:
    """Join lines that were only wrapped by the page, keep real paragraph breaks."""
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    out = []
    for paragraph in re.split(r"\n\s*\n", text):
        lines = [l.strip() for l in paragraph.split("\n") if l.strip()]
        if not lines:
            continue
        merged = lines[0]
        for line in lines[1:]:
            if re.search(r"[.!?།:;]$", merged):
                out.append(merged)
                merged = line
            elif merged.endswith("-") and line[:1].islower():
                merged = merged[:-1] + line          # re-join a hyphenated word
            else:
                merged += " " + line
        out.append(merged)
    return "\n".join(out)


def _read_txt(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def _read_docx(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(", ".join(cells))
    return "\n\n".join(parts)


def _read_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            ok = reader.decrypt("")
        except Exception:
            ok = 0
        if not ok:
            raise DocumentError("This PDF is password-protected. Please remove the password and try again.")
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    raw = "\n\n".join(pages)
    if len(raw.strip()) < 20:
        raise DocumentError(
            "No selectable text was found in this PDF. It is probably a scan or a picture. "
            "Reading scanned pages (OCR) is not available yet."
        )
    return raw


def extract_text(filename: str, data: bytes) -> str:
    """Read a PDF, DOCX or TXT file and return clean text. Raises DocumentError."""
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED:
        raise DocumentError(f"'{ext or filename}' files are not supported. Please upload a PDF, DOCX or TXT file.")
    if not data:
        raise DocumentError("The file is empty.")
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise DocumentError(f"The file is larger than {MAX_FILE_MB} MB. Please upload a smaller file.")

    try:
        if ext == ".txt":
            raw = _read_txt(data)
        elif ext == ".docx":
            raw = _read_docx(data)
        else:
            raw = _read_pdf(data)
    except DocumentError:
        raise
    except Exception:
        raise DocumentError(f"Could not open this {ext[1:].upper()} file. It may be damaged or in an unusual format.")

    text = clean_text(raw)
    if not text.strip():
        raise DocumentError("No text was found in this file.")
    return text
