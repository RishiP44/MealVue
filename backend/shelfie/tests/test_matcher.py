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


def test_catalog_work_id_consistency():
    """Verify different editions of the same work share work_id, distinct works do not."""
    catalog = load_catalog()
    by_id = {e.catalog_id: e for e in catalog}

    # The Hobbit editions share WORK0001
    assert by_id["BK0001"].work_id == by_id["BK0002"].work_id == "WORK0001"

    # Clean Code editions share WORK0019
    assert by_id["BK0023"].work_id == by_id["BK0024"].work_id == "WORK0019"

    # Steve Jobs editions share WORK0030
    assert by_id["BK0035"].work_id == by_id["BK0036"].work_id == "WORK0030"

    # Fahrenheit 451 editions share WORK0038
    assert by_id["BK0044"].work_id == by_id["BK0113"].work_id == "WORK0038"

    # Distinct works must not share work_id
    assert by_id["BK0023"].work_id != by_id["BK0025"].work_id  # Clean Code vs Clean Coder
    assert by_id["BK0015"].work_id != by_id["BK0017"].work_id  # Dune vs Dune Messiah


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
    assert len(same_title_diff_authors) >= 2, "Expected >= 2 titles with different authors (e.g. Island, Nemesis, Inferno)"

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
    assert res.match_score == 1.0
    assert res.confidence >= MATCH_THRESHOLD
    assert res.best_candidate["catalog_id"] == "BK0059"


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
    res = match_book(title="The Golden Compass", author="Philip Pullman")
    assert res.best_candidate["catalog_id"] in ["BK0012", "BK0013"]
    # Margin is 0.0 between US and UK edition -> routes to needs_review
    assert res.state == "needs_review"
    assert res.confidence == 0.5000  # Low decision confidence due to tie!


def test_match_same_title_different_authors_disambiguation():
    # "Island" by Aldous Huxley vs "The Island" by Victoria Hislop
    res_huxley = match_book(title="Island", author="Aldous Huxley")
    assert res_huxley.state == "matched"
    assert res_huxley.best_candidate["catalog_id"] == "BK0027"

    res_hislop = match_book(title="The Island", author="Victoria Hislop")
    assert res_hislop.state == "matched"
    assert res_hislop.best_candidate["catalog_id"] == "BK0028"


def test_match_multiple_editions_perfect_tie_confidence():
    res = match_book(title="The Hobbit", author="J. R. R. Tolkien")
    assert res.match_score == 1.0000
    assert res.margin == 0.0000
    assert res.confidence == 0.5000  # Low decision confidence despite 1.0 match_score!
    assert res.state == "needs_review"


def test_match_omnibus_vs_individual_volume():
    res = match_book(title="The Fellowship of the Ring", author="J. R. R. Tolkien")
    assert res.best_candidate["title"] == "The Fellowship of the Ring"
    assert res.best_candidate["catalog_id"] == "BK0003"


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


def test_match_noisy_vlm_ocr_transcription():
    res = match_book(title="Sapens: Brief History", author="Yuval N Harari")
    assert res.best_candidate["catalog_id"] == "BK0063"
    assert res.state in ["matched", "needs_review"]


# =====================================================================
# 4. ADVERSARIAL SUBSTRING & WRONG AUTHOR TESTS
# =====================================================================

def test_adversarial_substring_collisions():
    # "Dune Mesiah" / "Frank Herbert" -> matches Dune Messiah (BK0017) over Dune (BK0015)
    res_messiah = match_book(title="Dune Mesiah", author="Frank Herbert")
    assert res_messiah.best_candidate["catalog_id"] == "BK0017"

    # "Foundation Empire" / "Isaac Asimov" -> matches Foundation and Empire (BK0020) over Foundation (BK0019)
    res_empire = match_book(title="Foundation Empire", author="Isaac Asimov")
    assert res_empire.best_candidate["catalog_id"] == "BK0020"

    # "Clean Coder" / "Robert Martin" -> matches The Clean Coder (BK0025) over Clean Code (BK0023)
    res_coder = match_book(title="Clean Coder", author="Robert Martin")
    assert res_coder.best_candidate["catalog_id"] == "BK0025"


def test_adversarial_wrong_author_guard():
    # "1984" by "Aldous Huxley" (George Orwell's 1984)
    res_1984 = match_book(title="1984", author="Aldous Huxley")
    assert res_1984.match_score <= 0.45  # Author conflict guard caps score
    assert res_1984.confidence <= 0.45
    assert res_1984.state in ["needs_review", "unmatched"]

    # "Inferno" by "Isaac Asimov" (Dante / Dan Brown's Inferno)
    res_inferno = match_book(title="Inferno", author="Isaac Asimov")
    assert res_inferno.match_score < 0.50
    assert res_inferno.confidence <= 0.45
    assert res_inferno.state in ["needs_review", "unmatched"]

    # "Island" by wrong author
    res_island = match_book(title="Island", author="George Orwell")
    assert res_island.match_score <= 0.45
    assert res_island.confidence <= 0.45
    assert res_island.state in ["needs_review", "unmatched"]


# =====================================================================
# 5. CONFIDENCE SEMANTICS & INVARIANTS
# =====================================================================

def test_match_weak_candidate_low_confidence():
    """Verify weak candidate returns low confidence below review threshold."""
    res = match_book(title="Quantum Physics", author="Unknown")
    assert res.confidence < REVIEW_THRESHOLD
    assert res.state == "unmatched"


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


def test_row_order_invariance():
    """Catalog order must not change the winning candidate for unambiguous matches."""
    catalog = load_catalog()
    matcher_forward = CatalogMatcher(catalog)
    matcher_reverse = CatalogMatcher(list(reversed(catalog)))

    res_fwd = matcher_forward.match_book("Designing Data-Intensive Applications", "Martin Kleppmann")
    res_rev = matcher_reverse.match_book("Designing Data-Intensive Applications", "Martin Kleppmann")

    assert res_fwd.best_candidate["catalog_id"] == res_rev.best_candidate["catalog_id"]
    assert res_fwd.confidence == res_rev.confidence
    assert res_fwd.state == res_rev.state
