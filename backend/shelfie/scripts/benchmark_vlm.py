import sys
import os
import time
import csv
from pathlib import Path
from PIL import Image

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from shelfie.services.vlm import VLMService, VLMBatchResult


# 12 Representative crops across varied conditions (clear, narrow, partial, low-light, difficult)
REPRESENTATIVE_CROPS = [
    {
        "crop_id": "easy_001",
        "rel_path": "test-images/results/crops/shelf_easy/book_001.jpg",
        "source_image": "shelf_easy.jpg",
        "expected_readability_manual": "readable",
        "notes": "Clear wide spine: Goodnight Crested Butte",
    },
    {
        "crop_id": "easy_002",
        "rel_path": "test-images/results/crops/shelf_easy/book_002.jpg",
        "source_image": "shelf_easy.jpg",
        "expected_readability_manual": "readable",
        "notes": "Clear tall spine: Handbook of Bird Biology",
    },
    {
        "crop_id": "easy_003",
        "rel_path": "test-images/results/crops/shelf_easy/book_003.jpg",
        "source_image": "shelf_easy.jpg",
        "expected_readability_manual": "readable",
        "notes": "Clear spine: Mars The Pristine Beauty",
    },
    {
        "crop_id": "easy_004",
        "rel_path": "test-images/results/crops/shelf_easy/book_004.jpg",
        "source_image": "shelf_easy.jpg",
        "expected_readability_manual": "partial",
        "notes": "Partial spine: The Flower In...",
    },
    {
        "crop_id": "easy_005",
        "rel_path": "test-images/results/crops/shelf_easy/book_005.jpg",
        "source_image": "shelf_easy.jpg",
        "expected_readability_manual": "readable",
        "notes": "Clear spine: Sylvia Plath Drawings",
    },
    {
        "crop_id": "easy_008",
        "rel_path": "test-images/results/crops/shelf_easy/book_008.jpg",
        "source_image": "shelf_easy.jpg",
        "expected_readability_manual": "readable",
        "notes": "Clear spine: The Art of Doing Science and Engineering",
    },
    {
        "crop_id": "low_light_001",
        "rel_path": "test-images/results/crops/shelf_low_light/book_001.jpg",
        "source_image": "shelf_low_light.jpg",
        "expected_readability_manual": "partial",
        "notes": "Low-light spine with dark contrast",
    },
    {
        "crop_id": "low_light_002",
        "rel_path": "test-images/results/crops/shelf_low_light/book_002.jpg",
        "source_image": "shelf_low_light.jpg",
        "expected_readability_manual": "readable",
        "notes": "Low-light legible spine",
    },
    {
        "crop_id": "low_light_004",
        "rel_path": "test-images/results/crops/shelf_low_light/book_004.jpg",
        "source_image": "shelf_low_light.jpg",
        "expected_readability_manual": "partial",
        "notes": "Low-light shadowed vertical spine",
    },
    {
        "crop_id": "mixed_001",
        "rel_path": "test-images/results/crops/shelf_mixed_sizes/book_001.jpg",
        "source_image": "shelf_mixed_sizes.jpg",
        "expected_readability_manual": "readable",
        "notes": "Horizontal stacked spine",
    },
    {
        "crop_id": "mixed_004",
        "rel_path": "test-images/results/crops/shelf_mixed_sizes/book_004.jpg",
        "source_image": "shelf_mixed_sizes.jpg",
        "expected_readability_manual": "partial",
        "notes": "Small font spine crop",
    },
    {
        "crop_id": "mixed_006",
        "rel_path": "test-images/results/crops/shelf_mixed_sizes/book_006.jpg",
        "source_image": "shelf_mixed_sizes.jpg",
        "expected_readability_manual": "unreadable",
        "notes": "Difficult / blurry spine crop",
    },
]


def run_vlm_benchmark():
    repo_root = backend_dir.parent
    test_images_dir = repo_root / "test-images"

    print("=========================================================")
    print("SHELFIE HOSTED VISION-LANGUAGE (VLM) EXTRACTION BENCHMARK")
    print("=========================================================")

    service = VLMService()
    service._ensure_api_key()

    print(f"Provider:            OpenRouter (https://openrouter.ai)")
    print(f"Configured Model:    {service.model}")
    print(f"Configured Batch:    {service.batch_size}")
    print(f"Request Timeout:     {service.timeout}s")
    print(f"Max Retries:         {service.max_retries}")
    print("---------------------------------------------------------")

    # Load representative crop images
    loaded_crops = []
    metadata_by_crop_id = {}

    for item in REPRESENTATIVE_CROPS:
        crop_path = repo_root / item["rel_path"]
        if not crop_path.exists():
            print(f"WARNING: Crop file not found: {crop_path}")
            continue
        img = Image.open(crop_path)
        loaded_crops.append((item["crop_id"], img))
        metadata_by_crop_id[item["crop_id"]] = item

    print(f"Loaded {len(loaded_crops)} representative test crops.")
    print("Executing batched hosted VLM extractions...")

    t0_all = time.perf_counter()
    batch_latencies = []
    all_extractions = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    total_cost = 0.0

    batch_size = service.batch_size
    for i in range(0, len(loaded_crops), batch_size):
        batch = loaded_crops[i: i + batch_size]
        batch_idx = (i // batch_size) + 1
        print(f"  Sending Batch #{batch_idx} ({len(batch)} crops: {[cid for cid, _ in batch]})...", end="", flush=True)

        t_b_start = time.perf_counter()
        batch_res = service.extract_single_batch(batch)
        b_lat_ms = (time.perf_counter() - t_b_start) * 1000.0

        batch_latencies.append(batch_res.metrics.request_latency_ms)
        all_extractions.extend(batch_res.extractions)

        total_prompt_tokens += batch_res.metrics.prompt_tokens
        total_completion_tokens += batch_res.metrics.completion_tokens
        total_tokens += batch_res.metrics.total_tokens
        if batch_res.metrics.cost is not None:
            total_cost += batch_res.metrics.cost

        print(f" Done in {batch_res.metrics.request_latency_ms:.2f} ms (Status: {[e.status for e in batch_res.extractions]})")

    total_benchmark_time_ms = (time.perf_counter() - t0_all) * 1000.0

    # Build evaluation rows
    evaluation_rows = []
    for ext in all_extractions:
        meta = metadata_by_crop_id.get(ext.crop_id, {})
        evaluation_rows.append({
            "crop_id": ext.crop_id,
            "source_image": meta.get("source_image", "unknown"),
            "expected_readability_manual": meta.get("expected_readability_manual", "unknown"),
            "returned_title": ext.title or "",
            "returned_author": ext.author or "",
            "returned_readability": ext.readability,
            "status": ext.status,
            "error_reason": ext.error_reason or "",
            "notes": meta.get("notes", ""),
        })

    # Save to test-images/vlm_evaluation.csv
    vlm_csv_path = test_images_dir / "vlm_evaluation.csv"
    with open(vlm_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "crop_id", "source_image", "expected_readability_manual",
            "returned_title", "returned_author", "returned_readability",
            "status", "error_reason", "notes"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in evaluation_rows:
            writer.writerow(r)

    avg_req_lat = sum(batch_latencies) / len(batch_latencies) if batch_latencies else 0.0
    sorted_lat = sorted(batch_latencies)
    median_req_lat = sorted_lat[len(sorted_lat) // 2] if sorted_lat else 0.0

    cost_per_crop = total_cost / len(loaded_crops) if loaded_crops else 0.0
    est_25_crop_scan = cost_per_crop * 25

    print("\n=========================================================")
    print("VLM EXTRACTION RESULTS TABLE:")
    print(f"{'Crop ID':<15} | {'Source Image':<20} | {'Readability':<11} | {'Status':<7} | {'Extracted Title & Author'}")
    print("-" * 100)
    for r in evaluation_rows:
        t_str = r['returned_title'] if r['returned_title'] else "(null)"
        a_str = f" / {r['returned_author']}" if r['returned_author'] else ""
        print(f"{r['crop_id']:<15} | {r['source_image']:<20} | {r['returned_readability']:<11} | {r['status']:<7} | {t_str}{a_str}")
    print("-" * 100)

    print("\n=========================================================")
    print("USAGE, LATENCY & COST ACCOUNTING:")
    print(f"Total Representative Crops Tested:   {len(loaded_crops)}")
    print(f"Total Hosted API Requests:          {len(batch_latencies)}")
    print(f"Total Prompt Tokens:                {total_prompt_tokens}")
    print(f"Total Completion Tokens:            {total_completion_tokens}")
    print(f"Total Tokens:                       {total_tokens}")
    print(f"Total Provider-Reported Cost:       ${total_cost:.6f}")
    print(f"Measured Cost Per Tested Crop:      ${cost_per_crop:.6f} (${cost_per_crop*100:.4f} / 100 crops)")
    print(f"Estimated Typical 25-Crop Scan:     ${est_25_crop_scan:.6f}")
    print(f"Average Request Latency:            {avg_req_lat:.2f} ms")
    print(f"Median Request Latency:             {median_req_lat:.2f} ms")
    print(f"Total Benchmark Stage Time:         {total_benchmark_time_ms:.2f} ms")
    print("=========================================================\n")

    # Optional: Batch-Size Observation (Compare batch_size=1 vs batch_size=5 on 5-crop sample)
    print("Running Batch Size Observation (5 sample crops: batch_size=1 vs batch_size=5)...")
    sample_crops = loaded_crops[:5]

    # Batch Size 5
    t0_b5 = time.perf_counter()
    res_b5 = service.extract_single_batch(sample_crops)
    time_b5 = (time.perf_counter() - t0_b5) * 1000.0

    # Batch Size 1
    t0_b1 = time.perf_counter()
    res_b1 = service.extract_spines(sample_crops, batch_size=1)
    time_b1 = (time.perf_counter() - t0_b1) * 1000.0

    print(f"  Batch Size 5: 1 request, {res_b5.metrics.total_tokens} tokens, ${res_b5.metrics.cost or 0:.6f} cost, {res_b5.metrics.request_latency_ms:.2f} ms latency")
    print(f"  Batch Size 1: 5 requests, {res_b1.metrics.total_tokens} tokens, ${res_b1.metrics.cost or 0:.6f} cost, {time_b1:.2f} ms total latency")
    print(f"  Batching Speedup: {time_b1 / time_b5:.2f}x faster with batch_size=5")
    print(f"  Token Savings:    {(res_b1.metrics.total_tokens - res_b5.metrics.total_tokens) / res_b1.metrics.total_tokens * 100:.1f}% fewer tokens with batch_size=5")
    print("=========================================================\n")


if __name__ == "__main__":
    run_vlm_benchmark()
