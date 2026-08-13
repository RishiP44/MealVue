import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class CatalogEntry:
    catalog_id: str
    work_id: str
    title: str
    author: str
    alternate_titles: List[str] = field(default_factory=list)
    author_aliases: List[str] = field(default_factory=list)
    edition: str = ""
    publication_year: str = ""

    def all_titles(self) -> List[str]:
        """Return list of canonical title and all alternate titles."""
        return [self.title] + [t for t in self.alternate_titles if t.strip()]

    def all_authors(self) -> List[str]:
        """Return list of canonical author and all author aliases."""
        return [self.author] + [a for a in self.author_aliases if a.strip()]


def find_catalog_file() -> Path:
    """Locate catalog.csv at repository root or backend root."""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    root_catalog = base_dir / "catalog.csv"
    if root_catalog.exists():
        return root_catalog
    
    backend_catalog = Path(__file__).resolve().parent.parent.parent / "catalog.csv"
    if backend_catalog.exists():
        return backend_catalog
        
    raise FileNotFoundError(f"catalog.csv not found at {root_catalog} or {backend_catalog}")


def load_catalog(filepath: Optional[str | Path] = None) -> List[CatalogEntry]:
    """Parse, validate, and return entries from catalog.csv."""
    path = Path(filepath) if filepath else find_catalog_file()
    if not path.exists():
        raise FileNotFoundError(f"Catalog file does not exist: {path}")

    entries: List[CatalogEntry] = []
    seen_ids = set()

    with open(path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required_cols = {"catalog_id", "work_id", "title", "author"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            raise ValueError(f"catalog.csv missing required columns: {missing}")

        for line_num, row in enumerate(reader, start=2):
            cid = (row.get("catalog_id") or "").strip()
            title = (row.get("title") or "").strip()
            author = (row.get("author") or "").strip()

            if not cid:
                raise ValueError(f"Line {line_num}: Empty catalog_id")
            if cid in seen_ids:
                raise ValueError(f"Line {line_num}: Duplicate catalog_id '{cid}'")
            seen_ids.add(cid)

            if not title:
                raise ValueError(f"Line {line_num}: Empty title for catalog_id '{cid}'")
            if not author:
                raise ValueError(f"Line {line_num}: Empty author for catalog_id '{cid}'")

            alt_titles_raw = (row.get("alternate_titles") or "").strip()
            alt_titles = [t.strip() for t in alt_titles_raw.split("|") if t.strip()]

            aliases_raw = (row.get("author_aliases") or "").strip()
            aliases = [a.strip() for a in aliases_raw.split("|") if a.strip()]

            entries.append(
                CatalogEntry(
                    catalog_id=cid,
                    work_id=(row.get("work_id") or "").strip(),
                    title=title,
                    author=author,
                    alternate_titles=alt_titles,
                    author_aliases=aliases,
                    edition=(row.get("edition") or "").strip(),
                    publication_year=(row.get("publication_year") or "").strip(),
                )
            )

    if not entries:
        raise ValueError("catalog.csv contains zero entries")

    return entries
