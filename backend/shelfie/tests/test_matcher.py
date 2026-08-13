import pytest
from shelfie.services.catalog import load_catalog, CatalogEntry
from shelfie.services.matcher import (
    match_book,
    CatalogMatcher,
    normalize_title,
    normalize_author,
    MATCH_THRESHOLD,
    REVIEW_THRESHOLD,
    MIN_MARGIN,
)


# =====================================================================
# 1. CATALOG INTEGRITY & AMBIGUITY VALIDATION TESTS
# =====================================================================

def test_catalog_load_and_minimum_count():
    """Verify catalog.csv loads cleanly and contains at least 100 entries."""
    catalog = load_catalog()
    assert len(catalog) >= 100, f"Expected >= 100 catalog entries, got {len(catalog)}"


def test_catalog_unique_ids_and_required_fields():
    """Verify all catalog entries have unique catalog_id and non-empty fields."""
    catalog = load_catalog()
    seen_ids = set()
    for entry in catalog:
        assert entry.catalog_id not in seen_ids, f"Duplicate ID: {entry.catalog_id}"
        seen_ids.add(entry.catalog_id)
        assert entry.title.strip(), f"Empty title in {entry.catalog_id}"
        assert entry.author.strip(), f"Empty author in {entry.catalog_id}"
        assert entry.work_id.strip(), f"Empty work_id in {entry.catalog_id}"


def test_catalog_deliberate_messy_categories():
    """Assert all mandatory ambiguity categories exist in catalog.csv."""
    catalog = load_catalog()
    
    # Category A: Same work, multiple editions
    work_id_counts = {}
    for entry in catalog:
        work_id_counts[entry.work_id] = work_id_counts.get(entry.work_id, 0) + 1
    multi_editions = [wid for wid, count in work_id_counts.items() if count > 1]
    assert len(multi_editions) >= 3, "Expected multiple works with >= 2 editions"

    # Category B: Alternate titles
    with_alt_titles = [e for e in catalog if len(e.alternate_titles) > 0]
    assert len(with_alt_titles) >= 5, "Expected >= 5 entries with alternate titles"

    # Category C: Same title, different authors
    title_authors = {}
    for e in catalog:
        norm_t = normalize_title(e.title)
        title_authors.setdefault(norm_t, set()).add(e.author)
    same_title_diff_authors = [t for t, authors in title_authors.items() if len(authors) > 1]
    assert len(same_title_diff_authors) >= 2, "Expected >= 2 titles with different authors (e.g. The Island, Nemesis, Inferno)"

    # Category D: Omnibus vs individual volumes
    omnibus_entries = [e for e in catalog if "omnibus" in e.title.lower() or "trilogy" in e.title.lower() or any("omnibus" in alt.lower() for alt in e.alternate_titles)]
    assert len(omnibus_entries) >= 2, "Expected omnibus editions in catalog"

    # Category E: Substring collisions
    titles = [normalize_title(e.title) for e in catalog]
    substring_collisions = []
    for t1 in titles:
        for t2 in titles:
            if t1 != t2 and t1 in t2:
                substring_collisions.append((t1, t2))
    assert len(substring_collisions) >= 3, "Expected substring collision title pairs (e.g. Dune / Dune Messiah)"

    # Category F: Author aliases
    with_aliases = [e for e in catalog if len(e.author_aliases) > 0]
    assert len(with_aliases) >= 10, "Expected >= 10 entries with author aliases"


# =====================================================================
# 2. NORMALIZATION UNIT TESTS
# =====================================================================

def test_normalize_title():
    assert normalize_title("  The   Hobbit:  ") == "the hobbit"
    assert normalize_title("Crime & Punishment") == "crime and punishment"
    assert normalize_title("1984!") == "1984"
    assert normalize_title("Cáncer & Éxito") == "cancer and exito"
    assert normalize_title("") == ""
    assert normalize_title(None) == ""


def test_normalize_author():
    assert normalize_author("J. R. R. Tolkien") == "j r r tolkien"
    assert normalize_author("Tolkien, J. R. R.") == "j r r tolkien"
    assert normalize_author("  Dostoevsky,  Fyodor ") == "fyodor dostoevsky"
    assert normalize_author("") == ""
    assert normalize_author(None) == ""


# =====================================================================
# 3. DETERMINISTIC MATCHER CORE TESTS
# =====================================================================

def test_match_exact_canonical_title_and_author_unique():
    res = match_book(title="Designing Data-Intensive Applications", author="Martin Kleppmann")
    assert res.state == "matched"
    assert res.best_candidate["catalog_id"] == "BK0059"
    assert res.confidence >= MATCH_THRESHOLD


def test_match_case_insensitivity():
    res = match_book(title="sapiens", author="yuval noah harari")
    assert res.state == "matched"
    assert res.best_candidate["catalog_id"] == "BK0063"


def test_match_punctuation_differences():
    res = match_book(title="Crime and Punishment", author="Fyodor Dostoevsky")
    assert res.state == "matched"
    assert res.best_candidate["catalog_id"] == "BK0048"


def test_match_accent_normalization():
    res = match_book(title="The Brothers Karamazov", author="Fyodor Dostoyevsky")
    assert res.state == "matched"
    assert res.best_candidate["catalog_id"] == "BK0049"


def test_match_small_title_typo():
    res = match_book(title="Design Patterns", author="Erich Gamma")
    assert res.state == "matched"
    assert res.best_candidate["catalog_id"] == "BK0054"


def test_match_author_initials():
    res = match_book(title="The Catcher in the Rye", author="J.D. Salinger")
    assert res.state == "matched"
    assert res.best_candidate["catalog_id"] == "BK0047"


def test_match_author_alias():
    res = match_book(title="1984", author="Eric Arthur Blair")
    assert res.state == "matched"
    assert res.best_candidate["catalog_id"] == "BK0041"


def test_match_lastname_firstname_author():
    res = match_book(title="1984", author="Orwell, George")
    assert res.state == "matched"
    assert res.best_candidate["catalog_id"] == "BK0041"


def test_match_alternate_published_title():
    # Northern Lights alt_title = The Golden Compass
    res = match_book(title="The Golden Compass", author="Philip Pullman")
    assert res.best_candidate["catalog_id"] in ["BK0012", "BK0013"]
    assert res.best_candidate["title"] in ["Northern Lights", "The Golden Compass"]


def test_match_same_title_different_authors_disambiguation():
    # "The Island" by Aldous Huxley vs "The Island" by Victoria Hislop
    res_huxley = match_book(title="The Island", author="Aldous Huxley")
    assert res_huxley.state == "matched"
    assert res_huxley.best_candidate["catalog_id"] == "BK0027"

    res_hislop = match_book(title="The Island", author="Victoria Hislop")
    assert res_hislop.state == "matched"
    assert res_hislop.best_candidate["catalog_id"] == "BK0028"


def test_match_multiple_editions_routes_to_review_if_ambiguous():
    # Query "The Hobbit" without edition specified. Both BK0001 and BK0002 score identically.
    res = match_book(title="The Hobbit", author="J. R. R. Tolkien")
    assert res.signals["margin"] < MIN_MARGIN
    # Margin is 0.0 -> routes to needs_review for human choice!
    assert res.state == "needs_review"


def test_match_omnibus_vs_individual_volume():
    # Query "The Fellowship of the Ring" vs "The Lord of the Rings" omnibus
    res = match_book(title="The Fellowship of the Ring", author="J. R. R. Tolkien")
    assert res.best_candidate["title"] == "The Fellowship of the Ring"
    assert res.best_candidate["catalog_id"] == "BK0003"


def test_match_substring_collision_does_not_overfire():
    # Query "Dune" vs "Dune Messiah"
    res_dune = match_book(title="Dune", author="Frank Herbert")
    assert res_dune.best_candidate["title"] == "Dune"
    assert res_dune.best_candidate["catalog_id"] in ["BK0015", "BK0016"]

    res_messiah = match_book(title="Dune Messiah", author="Frank Herbert")
    assert res_messiah.best_candidate["title"] == "Dune Messiah"
    assert res_messiah.best_candidate["catalog_id"] == "BK0017"


def test_match_title_present_author_missing():
    res = match_book(title="Designing Data-Intensive Applications", author=None)
    assert res.state in ["matched", "needs_review"]
    assert res.best_candidate["catalog_id"] == "BK0059"


def test_match_author_present_title_missing():
    res = match_book(title=None, author="James Clear")
    assert res.state == "unmatched"  # Author alone is insufficient for direct match
    assert res.confidence < REVIEW_THRESHOLD


def test_match_both_fields_missing():
    res = match_book(title=None, author=None)
    assert res.state == "unmatched"
    assert res.confidence == 0.0
    assert res.best_candidate is None


def test_match_obviously_unrelated_input():
    res = match_book(title="Quantum Mechanical Superconductivity 101", author="Unknown Researcher")
    assert res.state == "unmatched"
    assert res.confidence < REVIEW_THRESHOLD


def test_match_high_top_score_tiny_margin_routes_to_review():
    # Query matching multiple close editions (Clean Code 1st vs Special Edition)
    res = match_book(title="Clean Code", author="Robert C. Martin")
    assert res.signals["margin"] < MIN_MARGIN
    assert res.state == "needs_review"


def test_match_high_top_score_large_margin_routes_to_matched():
    # Unique title with large margin over second candidate
    res = match_book(title="Designing Data-Intensive Applications", author="Martin Kleppmann")
    assert res.state == "matched"
    assert res.signals["margin"] >= MIN_MARGIN
    assert res.confidence >= MATCH_THRESHOLD


def test_match_noisy_vlm_ocr_transcription():
    res = match_book(title="Sapens: Brief History", author="Yuval N Harari")
    assert res.best_candidate["catalog_id"] == "BK0063"
    assert res.state in ["matched", "needs_review"]


# =====================================================================
# 4. INVARIANT & PROPERTY TESTS
# =====================================================================

def test_matcher_invariants():
    """Enforce mathematical and structural invariants on MatchResult."""
    res = match_book(title="Sapiens", author="Yuval Noah Harari")
    assert 0.0 <= res.confidence <= 1.0
    assert 0.0 <= res.signals["title_score"] <= 1.0
    assert 0.0 <= res.signals["author_score"] <= 1.0
    assert 0.0 <= res.signals["runner_up_score"] <= 1.0
    assert 0.0 <= res.signals["margin"] <= 1.0
    
    # Alternatives are ordered descending by score
    alt_scores = [alt["score"] for alt in res.alternatives]
    assert alt_scores == sorted(alt_scores, reverse=True)
    
    # Best candidate is not duplicated in alternatives
    alt_ids = [alt["catalog_id"] for alt in res.alternatives]
    assert res.best_candidate["catalog_id"] not in alt_ids
