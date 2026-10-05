import os
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class ParsedPage(BaseModel):
    page_number: int
    text: str
    headings: List[str] = []
    statutory_references: List[str] = []
    tables: List[str] = []


class ParsedDocument(BaseModel):
    title: str
    file_format: str
    pages: List[ParsedPage]
    total_pages: int
    raw_text: str
    detected_chapters: List[str] = []
    detected_sections: List[str] = []


# Statutory reference regex pattern (Sections, Rules, Standards, Clauses)
STATUTORY_PATTERN = re.compile(
    r"\b(Section\s+\d+[A-Z]?(?:\(\d+\))*(?:\([a-z]\))*|Rule\s+\d+[A-Z]?|SA\s+\d+|AS\s+\d+|Ind\s+AS\s+\d+|Clause\s+\d+)\b",
    re.IGNORECASE
)

# Chapter heading pattern
CHAPTER_PATTERN = re.compile(
    r"^(?:CHAPTER|UNIT|MODULE)\s*[:\-]?\s*(\d+|[IVXLCDM]+)?\s*[:\-]?\s*([^\n]+)",
    re.IGNORECASE | re.MULTILINE
)

# Section heading pattern
SECTION_HEADING_PATTERN = re.compile(
    r"^(?:\d+\.\d+|\b[A-Z]\.|\bSection\s+\d+)\s+([^\n]+)",
    re.MULTILINE
)


class BaseDocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: str, title: Optional[str] = None) -> ParsedDocument:
        pass


class PDFDocumentParser(BaseDocumentParser):
    """Production PDF parser preserving page numbers, headings, tables and statutory clauses."""
    
    def parse(self, file_path: str, title: Optional[str] = None) -> ParsedDocument:
        if not HAS_PYPDF:
            raise RuntimeError("pypdf is required to parse PDF documents.")
        
        doc_title = title or os.path.splitext(os.path.basename(file_path))[0]
        pages: List[ParsedPage] = []
        all_text = []
        detected_chapters = set()
        detected_sections = set()

        reader = pypdf.PdfReader(file_path)
        total_pages = len(reader.pages)

        # Check metadata title if available
        if not title and reader.metadata and reader.metadata.title:
            doc_title = reader.metadata.title.strip()

        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.replace("\x00", "")  # remove null bytes
            
            # Find statutory references
            stat_matches = list(set(STATUTORY_PATTERN.findall(text)))
            for sm in stat_matches:
                detected_sections.add(sm)

            # Find headings
            headings = []
            for ch_match in CHAPTER_PATTERN.finditer(text):
                ch_title = f"{ch_match.group(0).strip()}"
                headings.append(ch_title)
                detected_chapters.add(ch_title)

            for sec_match in SECTION_HEADING_PATTERN.finditer(text):
                sec_title = sec_match.group(0).strip()
                if len(sec_title) < 120:
                    headings.append(sec_title)

            # Extract basic text table representations (lines with multiple delimiters / columns)
            tables = []
            table_lines = [line for line in text.split("\n") if line.count("\t") >= 2 or line.count("|") >= 2]
            if table_lines:
                tables.append("\n".join(table_lines))

            pages.append(ParsedPage(
                page_number=idx,
                text=text,
                headings=headings,
                statutory_references=stat_matches,
                tables=tables
            ))
            all_text.append(text)

        return ParsedDocument(
            title=doc_title,
            file_format="PDF",
            pages=pages,
            total_pages=total_pages,
            raw_text="\n\n".join(all_text),
            detected_chapters=list(detected_chapters),
            detected_sections=list(detected_sections)
        )


class MarkdownDocumentParser(BaseDocumentParser):
    """Markdown parser preserving # headings, section clauses, and page indicators."""

    def parse(self, file_path: str, title: Optional[str] = None) -> ParsedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        doc_title = title or os.path.splitext(os.path.basename(file_path))[0]
        
        # Check for # Title at top
        title_match = re.search(r"^#\s+([^\n]+)", content, re.MULTILINE)
        if title_match and not title:
            doc_title = title_match.group(1).strip()

        # Split into simulated pages if page markers exist, e.g. "<!-- page 2 -->" or "--- Page 2 ---"
        page_splits = re.split(r"(?:<!--\s*page\s*(\d+)\s*-->|---\s*Page\s*(\d+)\s*---)", content, flags=re.IGNORECASE)
        
        pages: List[ParsedPage] = []
        detected_chapters = set()
        detected_sections = set()

        if len(page_splits) > 1:
            # Reconstruct pages with detected numbers
            current_num = 1
            for chunk in page_splits:
                if chunk is None:
                    continue
                if chunk.isdigit():
                    current_num = int(chunk)
                elif chunk.strip():
                    stat_matches = list(set(STATUTORY_PATTERN.findall(chunk)))
                    headings = [h.group(1).strip() for h in re.finditer(r"^(?:#{1,3})\s+([^\n]+)", chunk, re.MULTILINE)]
                    for sm in stat_matches:
                        detected_sections.add(sm)
                    for h in headings:
                        detected_chapters.add(h)
                    pages.append(ParsedPage(
                        page_number=current_num,
                        text=chunk.strip(),
                        headings=headings,
                        statutory_references=stat_matches
                    ))
                    current_num += 1
        else:
            # Single page document
            stat_matches = list(set(STATUTORY_PATTERN.findall(content)))
            headings = [h.group(1).strip() for h in re.finditer(r"^(?:#{1,3})\s+([^\n]+)", content, re.MULTILINE)]
            for sm in stat_matches:
                detected_sections.add(sm)
            for h in headings:
                detected_chapters.add(h)
            pages.append(ParsedPage(
                page_number=1,
                text=content.strip(),
                headings=headings,
                statutory_references=stat_matches
            ))

        return ParsedDocument(
            title=doc_title,
            file_format="MD",
            pages=pages,
            total_pages=len(pages),
            raw_text=content,
            detected_chapters=list(detected_chapters),
            detected_sections=list(detected_sections)
        )


class TextDocumentParser(BaseDocumentParser):
    """Plain text parser with structural boundary detection."""

    def parse(self, file_path: str, title: Optional[str] = None) -> ParsedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        doc_title = title or os.path.splitext(os.path.basename(file_path))[0]
        stat_matches = list(set(STATUTORY_PATTERN.findall(content)))
        
        # Split on form-feed \x0c or double newlines with page marks
        raw_pages = content.split("\x0c")
        pages: List[ParsedPage] = []
        for idx, p_text in enumerate(raw_pages, start=1):
            if not p_text.strip():
                continue
            p_stats = list(set(STATUTORY_PATTERN.findall(p_text)))
            pages.append(ParsedPage(
                page_number=idx,
                text=p_text.strip(),
                statutory_references=p_stats
            ))

        if not pages:
            pages = [ParsedPage(page_number=1, text=content.strip(), statutory_references=stat_matches)]

        return ParsedDocument(
            title=doc_title,
            file_format="TXT",
            pages=pages,
            total_pages=len(pages),
            raw_text=content,
            detected_sections=stat_matches
        )


def get_parser_for_file(file_path: str) -> BaseDocumentParser:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return PDFDocumentParser()
    elif ext in [".md", ".markdown"]:
        return MarkdownDocumentParser()
    elif ext in [".txt", ".text"]:
        return TextDocumentParser()
    else:
        # Default to text parser
        return TextDocumentParser()
