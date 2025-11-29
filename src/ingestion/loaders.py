from pathlib import Path
from typing import List, Dict
import pypdf

def load_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def load_md(path: str) -> str:
    return load_txt(path)

def load_pdf(path: str) -> List[str]:
    """Memory-safe PDF loader that returns pages instead of 1 huge string."""
    pages = []
    reader = pypdf.PdfReader(path)
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except:
            pages.append("")
    return pages

def load_document(path: str) -> Dict:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        pages = load_pdf(path)
        return {"source": path, "pages": pages}
    else:
        content = load_txt(path) if ext != ".md" else load_md(path)
        return {"source": path, "content": content}
