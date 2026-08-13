import time
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from shelfie.services.catalog import load_catalog
from shelfie.services.matcher import match_book, get_default_matcher


def run_benchmark():
    catalog = load_catalog()
    matcher = get_default_matcher()

    test_queries = [
        ("Designing Data-Intensive Applications", "Martin Kleppmann"),  # 1. Exact match
        ("Sapens: Brief History", "Yuval N Harari"),                    # 2. Typo/noisy transcription
        ("The Golden Compass", "Philip Pullman"),                       # 3. Alternate title
        ("1984", "Eric Arthur Blair"),                                 # 4. Author alias
        ("The Island", "Aldous Huxley"),                               # 5. Shared title / correct author
        ("Dune Messiah", "Frank Herbert"),                             # 6. Substring collision
        ("The Hobbit", "J. R. R. Tolkien"),                            # 7. Ambiguous editions
        ("Quantum Mechanical Superconductivity", "Unknown"),           # 8. Unrelated book
    ]

    print("=========================================================")
    print(f"SHELFIE CATALOG MATCHER BENCHMARK")
    print("=========================================================")
    print(f"Catalog Entry Count: {len(catalog)}")
    print(f"Test Query Suite: {len(test_queries)} representative cases")
    print("---------------------------------------------------------")

    # Run query preview
    print("\nREPRESENTATIVE CASE PREVIEW:")
    for title, author in test_queries:
        res = matcher.match_book(title, author)
        best_id = res.best_candidate["catalog_id"] if res.best_candidate else "NONE"
        best_title = res.best_candidate["title"] if res.best_candidate else "N/A"
        runner_up = res.signals.get("runner_up_score", 0.0)
        margin = res.signals.get("margin", 0.0)
        print(f"Query: [{title} | {author}]")
        print(f"  -> State: {res.state:<12} Conf: {res.confidence:.4f}  Margin: {margin:.4f}")
        print(f"  -> Best:  {best_id} - {best_title} (S1={res.confidence:.4f}, S2={runner_up:.4f})\n")

    # Measure performance over repeated calls
    iterations = 125 # 125 * 8 = 1,000 matcher calls
    total_calls = len(test_queries) * iterations
    
    start_time = time.perf_counter()
    for _ in range(iterations):
        for title, author in test_queries:
            matcher.match_book(title, author)
    end_time = time.perf_counter()

    elapsed_s = end_time - start_time
    avg_call_ms = (elapsed_s / total_calls) * 1000.0
    calls_per_sec = total_calls / elapsed_s

    print("---------------------------------------------------------")
    print("BENCHMARK TIMING RESULTS:")
    print(f"Total Matcher Calls:  {total_calls:,}")
    print(f"Total Elapsed Time:   {elapsed_s:.4f} seconds")
    print(f"Average Latency:      {avg_call_ms:.4f} ms / call")
    print(f"Throughput:           {calls_per_sec:.2f} calls / sec")
    print("=========================================================\n")

    return {
        "catalog_count": len(catalog),
        "total_calls": total_calls,
        "total_elapsed_s": round(elapsed_s, 4),
        "avg_call_ms": round(avg_call_ms, 4),
        "throughput_cps": round(calls_per_sec, 2)
    }


if __name__ == "__main__":
    run_benchmark()
