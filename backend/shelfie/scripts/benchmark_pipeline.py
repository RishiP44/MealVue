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

from shelfie.services.pipeline import ShelfiePipeline, PipelineResult


BENCHMARK_IMAGES = [
    "shelf_easy.jpg",
    "shelf_low_light.jpg",
    "shelf_mixed_sizes.jpg",
    "shelf_angle.jpg",
]


def run_pipeline_benchmark():
    repo_root = backend_dir.parent
    test_images_dir = repo_root / "test-images"

    print("=========================================================")
    print("SHELFIE FULL END-TO-END PIPELINE BENCHMARK (PHASE 5)")
    print("=========================================================")

    pipeline = ShelfiePipeline()
    pipeline.vlm_service._ensure_api_key()

    print(f"Local Detector:      {pipeline.detector.model_name} (CPU, conf={pipeline.detector.conf_threshold})")
    print(f"Hosted VLM Model:    {pipeline.vlm_service.model} (Batch Size={pipeline.vlm_service.batch_size})")
    print(f"Catalog Matcher:     {len(pipeline.matcher.catalog)} catalog entries loaded")
    print("---------------------------------------------------------")

    results_table = []
    total_detections = 0
    total_matched = 0
    total_needs_review = 0
    total_unmatched = 0
    total_unreadable = 0
    total_extraction_failed = 0
    total_cost = 0.0
    total_latencies = []

    for img_name in BENCHMARK_IMAGES:
        img_path = test_images_dir / img_name
        if not img_path.exists():
            print(f"WARNING: Image not found: {img_path}")
            continue

        raw_img = Image.open(img_path)
        w, h = raw_img.size
        print(f"\nProcessing '{img_name}' ({w}x{h})...")

        t0 = time.perf_counter()
        pipeline_res: PipelineResult = pipeline.analyze_image(raw_img)
        total_time_ms = (time.perf_counter() - t0) * 1000.0

        summ = pipeline_res.summary
        metr = pipeline_res.metrics
        cost = metr.api_cost_usd or 0.0

        total_detections += summ.detections
        total_matched += summ.matched
        total_needs_review += summ.needs_review
        total_unmatched += summ.unmatched
        total_unreadable += summ.unreadable
        total_extraction_failed += summ.extraction_failed
        total_cost += cost
        total_latencies.append(total_time_ms)

        print(f"  Status:            {pipeline_res.status}")
        print(f"  Detections:        {summ.detections} boxes")
        print(f"  State Breakdown:   matched={summ.matched}, needs_review={summ.needs_review}, unmatched={summ.unmatched}, unreadable={summ.unreadable}, failed={summ.extraction_failed}")
        print(f"  Timing (ms):       det={metr.detection_ms:.1f}ms, vlm={metr.vlm_ms:.1f}ms, match={metr.matching_ms:.1f}ms -> total={total_time_ms:.1f}ms")
        print(f"  VLM Requests/Cost: {metr.api_requests} requests | ${cost:.6f}")

        # Print top extracted items for sanity verification
        if pipeline_res.items:
            print("  Item Samples:")
            for itm in pipeline_res.items[:4]:
                ext = itm.extraction
                t_str = ext.get("title") or "(null)"
                a_str = f" / {ext.get('author')}" if ext.get("author") else ""
                match_str = ""
                if itm.match and itm.match.get("best_candidate"):
                    cand = itm.match["best_candidate"]
                    match_str = f" -> [{cand.get('catalog_id')}] '{cand.get('title')}' (conf={itm.match.get('confidence'):.2f})"
                print(f"    [{itm.item_id}] ({itm.state}): '{t_str}{a_str}'{match_str}")
            if len(pipeline_res.items) > 4:
                print(f"    ... ({len(pipeline_res.items) - 4} more items)")

        results_table.append({
            "filename": img_name,
            "dimensions": f"{w}x{h}",
            "status": pipeline_res.status,
            "detections": summ.detections,
            "vlm_requests": metr.api_requests,
            "matched": summ.matched,
            "needs_review": summ.needs_review,
            "unmatched": summ.unmatched,
            "unreadable": summ.unreadable,
            "extraction_failed": summ.extraction_failed,
            "detection_ms": round(metr.detection_ms, 2),
            "crop_prep_ms": round(metr.crop_prep_ms, 2),
            "vlm_ms": round(metr.vlm_ms, 2),
            "matching_ms": round(metr.matching_ms, 2),
            "total_ms": round(total_time_ms, 2),
            "api_cost_usd": round(cost, 6),
        })

    # Save to test-images/pipeline_evaluation.csv
    csv_path = test_images_dir / "pipeline_evaluation.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "filename", "dimensions", "status", "detections", "vlm_requests",
            "matched", "needs_review", "unmatched", "unreadable", "extraction_failed",
            "detection_ms", "crop_prep_ms", "vlm_ms", "matching_ms", "total_ms", "api_cost_usd"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results_table:
            writer.writerow(r)

    avg_lat = sum(total_latencies) / len(total_latencies) if total_latencies else 0.0
    sorted_lat = sorted(total_latencies)
    median_lat = sorted_lat[len(sorted_lat) // 2] if sorted_lat else 0.0
    avg_cost = total_cost / len(results_table) if results_table else 0.0

    print("\n=========================================================")
    print("PIPELINE EVALUATION SUMMARY TABLE:")
    print(f"{'Filename':<22} | {'Det':<4} | {'Req':<3} | {'Mat':<3} | {'Rev':<3} | {'Unm':<3} | {'Unr':<3} | {'Fail':<4} | {'Det(ms)':<8} | {'VLM(ms)':<8} | {'Total(ms)':<9} | {'Cost ($)'}")
    print("-" * 125)
    for r in results_table:
        print(f"{r['filename']:<22} | {r['detections']:<4} | {r['vlm_requests']:<3} | {r['matched']:<3} | {r['needs_review']:<3} | {r['unmatched']:<3} | {r['unreadable']:<3} | {r['extraction_failed']:<4} | {r['detection_ms']:<8.1f} | {r['vlm_ms']:<8.1f} | {r['total_ms']:<9.1f} | ${r['api_cost_usd']:.6f}")
    print("-" * 125)
    print(f"Total Detections Across Runs:      {total_detections}")
    print(f"Total Matched Candidates:         {total_matched}")
    print(f"Total Needs Review Candidates:    {total_needs_review}")
    print(f"Total Unmatched Candidates:       {total_unmatched}")
    print(f"Total Unreadable Crops:           {total_unreadable}")
    print(f"Total Extraction Failures:        {total_extraction_failed}")
    print(f"Total Measured API Cost:          ${total_cost:.6f}")
    print(f"Average API Cost Per Image:       ${avg_cost:.6f}")
    print(f"Average Full-Pipeline Latency:    {avg_lat:.2f} ms")
    print(f"Median Full-Pipeline Latency:     {median_lat:.2f} ms")
    print("=========================================================\n")


if __name__ == "__main__":
    run_pipeline_benchmark()
