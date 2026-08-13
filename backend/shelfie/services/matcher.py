import unicodedata
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from rapidfuzz import fuzz

from .catalog import CatalogEntry, load_catalog


# Centralized Thresholds (Heuristically tuned against the Phase 2 test matrix)
MATCH_THRESHOLD = 0.80  # Minimum top match_score required for direct addition candidate
REVIEW_THRESHOLD = 0.45 # Minimum top match_score required for human review suggestion
MIN_MARGIN = 0.12       # Minimum separation between top candidate and runner-up for unambiguous match


def remove_accents(text: str) -> str:
    """Strip diacritics and accents (e.g., 'é' -> 'e')."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])


def strip_articles(text: str) -> str:
    """Strip leading common articles ('the', 'a', 'an')."""
    return re.sub(r'^(the|a|an)\s+', '', text).strip()


def normalize_title(text: Optional[str]) -> str:
    """Clean title text for deterministic matching."""
    if not text:
        return ""
    s = remove_accents(text.strip().lower())
    s = s.replace('&', ' and ')
    # Retain alphanumeric and spaces only
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def normalize_author(text: Optional[str]) -> str:
    """Clean and standardize author names, handling 'Lastname, Firstname'."""
    if not text:
        return ""
    s = remove_accents(text.strip().lower())
    
    # Handle "Lastname, Firstname" format (e.g. "Tolkien, J. R. R." -> "J. R. R. Tolkien")
    if ',' in s and ' and ' not in s:
        parts = [p.strip() for p in s.split(',', 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            s = f"{parts[1]} {parts[0]}"
            
    # Remove dots in initials ("j. r. r." -> "j r r")
    s = s.replace('.', ' ')
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def calculate_title_similarity(norm_input: str, entry: CatalogEntry) -> float:
    """Compute title similarity against canonical and alternate titles."""
    if not norm_input:
        return 0.0

    input_no_art = strip_articles(norm_input)

    max_sim = 0.0
    for cand_title in entry.all_titles():
        norm_cand = normalize_title(cand_title)
        if not norm_cand:
            continue
            
        cand_no_art = strip_articles(norm_cand)

        # Exact match after article stripping (e.g., "clean coder" vs "the clean coder")
        if input_no_art and input_no_art == cand_no_art:
            return 1.0

        set_ratio = fuzz.token_set_ratio(norm_input, norm_cand) / 100.0
        sort_ratio = fuzz.token_sort_ratio(norm_input, norm_cand) / 100.0
        
        # 50/50 ratio blend penalizes length mismatches cleanly, preventing raw substring inflation
        sim = (0.50 * set_ratio) + (0.50 * sort_ratio)
        if sim > max_sim:
            max_sim = sim

    return round(max_sim, 4)


def calculate_author_similarity(norm_input: str, entry: CatalogEntry) -> float:
    """Compute author similarity against canonical author and aliases."""
    if not norm_input:
        return 0.0

    max_sim = 0.0
    for cand_author in entry.all_authors():
        norm_cand = normalize_author(cand_author)
        if not norm_cand:
            continue
            
        set_ratio = fuzz.token_set_ratio(norm_input, norm_cand) / 100.0
        sort_ratio = fuzz.token_sort_ratio(norm_input, norm_cand) / 100.0
        sim = (0.60 * set_ratio) + (0.40 * sort_ratio)
        if sim > max_sim:
            max_sim = sim

    return round(max_sim, 4)


@dataclass
class MatchResult:
    state: str              # "matched", "needs_review", "unmatched"
    match_score: float      # Similarity of best candidate (S1)
    runner_up_score: float  # Similarity of second-best candidate (S2)
    margin: float           # match_score - runner_up_score
    confidence: float       # Decision confidence heuristic [0, 1] incorporating margin
    best_candidate: Optional[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]
    signals: Dict[str, Any]


class CatalogMatcher:
    def __init__(self, catalog_entries: Optional[List[CatalogEntry]] = None):
        self.catalog = catalog_entries if catalog_entries is not None else load_catalog()

    def match_book(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        limit: int = 3
    ) -> MatchResult:
        """
        Deterministically match input title and author against catalog entries.
        """
        norm_title = normalize_title(title)
        norm_author = normalize_author(author)

        has_title = bool(norm_title)
        has_author = bool(norm_author)

        # Edge case: No input fields provided
        if not has_title and not has_author:
            return MatchResult(
                state="unmatched",
                match_score=0.0,
                runner_up_score=0.0,
                margin=0.0,
                confidence=0.0,
                best_candidate=None,
                alternatives=[],
                signals={
                    "title_score": 0.0,
                    "author_score": 0.0,
                    "runner_up_score": 0.0,
                    "margin": 0.0,
                    "reason": "missing_all_inputs"
                }
            )

        scored_candidates = []

        for entry in self.catalog:
            t_score = calculate_title_similarity(norm_title, entry) if has_title else 0.0
            a_score = calculate_author_similarity(norm_author, entry) if has_author else 0.0

            if has_title and has_author:
                composite = (0.70 * t_score) + (0.30 * a_score)
                # Guard 1: Author conflict guard (title matches, author explicitly conflicts <0.35)
                if t_score >= 0.60 and a_score < 0.35:
                    composite = min(composite, 0.45)
                # Guard 2: Title conflict guard (author matches, title explicitly conflicts <0.50)
                elif t_score < 0.50:
                    composite = min(composite, 0.45)
            elif has_title:
                # Title present, author missing: Apply missing author modifier
                composite = t_score * 0.85
                composite = min(composite, 0.78)
            else: # has_author only
                # Author present, title missing: Author alone is insufficient for direct match
                composite = a_score * 0.40

            composite = round(composite, 4)

            scored_candidates.append({
                "entry": entry,
                "composite_score": composite,
                "title_score": t_score,
                "author_score": a_score,
            })

        # Sort candidates descending by composite_score
        scored_candidates.sort(key=lambda x: x["composite_score"], reverse=True)

        if not scored_candidates or scored_candidates[0]["composite_score"] == 0.0:
            return MatchResult(
                state="unmatched",
                match_score=0.0,
                runner_up_score=0.0,
                margin=0.0,
                confidence=0.0,
                best_candidate=None,
                alternatives=[],
                signals={
                    "title_score": 0.0,
                    "author_score": 0.0,
                    "runner_up_score": 0.0,
                    "margin": 0.0,
                    "reason": "zero_match_score"
                }
            )

        top = scored_candidates[0]
        s1 = top["composite_score"]
        
        runner_up = scored_candidates[1] if len(scored_candidates) > 1 else None
        s2 = runner_up["composite_score"] if runner_up else 0.0
        margin = round(s1 - s2, 4)

        # Decision Confidence Heuristic Calculation:
        # Incorporates match strength (s1) AND ambiguity margin penalty
        margin_factor = min(1.0, margin / MIN_MARGIN) if MIN_MARGIN > 0 else 1.0
        confidence = round(s1 * (0.50 + 0.50 * margin_factor), 4)

        # State Determination
        if s1 >= MATCH_THRESHOLD and margin >= MIN_MARGIN:
            state = "matched"
        elif s1 >= REVIEW_THRESHOLD:
            state = "needs_review"
        else:
            state = "unmatched"

        # Format candidates for serialization
        def format_candidate(c: Dict[str, Any]) -> Dict[str, Any]:
            e: CatalogEntry = c["entry"]
            return {
                "catalog_id": e.catalog_id,
                "work_id": e.work_id,
                "title": e.title,
                "author": e.author,
                "edition": e.edition,
                "publication_year": e.publication_year,
                "score": c["composite_score"],
                "title_score": c["title_score"],
                "author_score": c["author_score"],
            }

        best_cand_dict = format_candidate(top)
        alt_dicts = [format_candidate(c) for c in scored_candidates[1:1 + limit]]

        return MatchResult(
            state=state,
            match_score=s1,
            runner_up_score=s2,
            margin=margin,
            confidence=confidence,
            best_candidate=best_cand_dict,
            alternatives=alt_dicts,
            signals={
                "title_score": top["title_score"],
                "author_score": top["author_score"],
                "runner_up_score": s2,
                "margin": margin,
                "match_threshold": MATCH_THRESHOLD,
                "min_margin": MIN_MARGIN,
            }
        )


# Global default matcher instance
_default_matcher: Optional[CatalogMatcher] = None

def get_default_matcher() -> CatalogMatcher:
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = CatalogMatcher()
    return _default_matcher


def match_book(
    title: Optional[str] = None,
    author: Optional[str] = None,
    limit: int = 3
) -> MatchResult:
    """Convenience function wrapping the default CatalogMatcher."""
    return get_default_matcher().match_book(title=title, author=author, limit=limit)
