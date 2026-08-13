import time
import sys
import os
import csv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from shelfie.services.detector import BookDetector, detect_books
from shelfie.services.image_utils import extract_crop


# Audited approximate ground truth counts of visible physical book spines
AUDITED_VISIBLE_SPINES = {
    "shelf_easy.jpg": 85,
    "shelf_dense.jpg": 75,
    "shelf_angle.jpg": 24,
    "shelf_low_light.jpg": 32,
    "shelf_mixed_sizes.jpg": 26,
}

# Manual visual audit classifications for YOLO26n predictions
AUDITED_YOLO26N_CLASSIFICATIONS = {
    "shelf_easy.jpg": {"unique_usable": 14, "duplicates": 2, "grouped": 6, "false_positives": 0},
    "shelf_dense.jpg": {"unique_usable": 0, "duplicates": 0, "grouped": 0, "false_positives": 0},
    "shelf_angle.jpg": {"unique_usable": 0, "duplicates": 0, "grouped": 0, "false_positives": 0},
    "shelf_low_light.jpg": {"unique_usable": 6, "duplicates": 0, "grouped": 0, "false_positives": 0},
    "shelf_mixed_sizes.jpg": {"unique_usable": 7, "duplicates": 1, "grouped": 0, "false_positives": 0},
}


def draw_annotations(image: Image.Image, detections: list) -> Image.Image:
    """Draw bounding boxes, detection IDs, and confidence labels on image."""
    annotated = image.copy().convert("RGB")
    draw = ImageDraw.Draw(annotated)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    colors = ["#00FF00", "#00E5FF", "#FF9100", "#FF007F", "#7C4DFF"]

    for idx, det in enumerate(detections):
        bbox = det["bbox"]
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        conf = det["detector_confidence"]
        det_id = det["detection_id"]

        color = colors[idx % len(colors)]

        # Draw 3px bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        # Label background pill
        label_text = f"{det_id}: {conf:.2f}"
        text_bbox = draw.textbbox((x1, max(0, y1 - 22)), label_text, font=font)
        draw.rectangle([text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2], fill=color)
        draw.text((x1, max(0, y1 - 22)), label_text, fill="black", font=font)

    return annotated


def run_benchmark(model_name: str = "yolo26n.pt"):
    repo_root = backend_dir.parent
    test_images_dir = repo_root / "test-images"
    results_dir = test_images_dir / "results"
    crops_dir = results_dir / "crops"

    results_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    print("=========================================================")
    print(f"SHELFIE LOCAL BOOK DETECTOR BENCHMARK ({model_name})")
    print("=========================================================")

    detector = BookDetector(model_name=model_name, conf_threshold=0.25, padding_percent=0.04)

    # 1. Measure Model Cold Start Load Time
    print("Initializing detector and measuring model load time...")
    start_load = time.perf_counter()
    detector._ensure_model_loaded()
    load_time_ms = detector.load_time_ms
    print(f"Model Cold-Start Load Time: {load_time_ms:.2f} ms")
    print("---------------------------------------------------------")

    image_files = sorted([f for f in os.listdir(test_images_dir) if f.endswith(".jpg")])

    benchmark_rows = []
    total_visible = 0
    total_boxes = 0
    total_unique_usable = 0
    total_duplicates = 0
    total_grouped = 0
    total_false_pos = 0
    total_missed = 0
    zero_detection_images = 0
    warm_latencies = []

    for img_name in image_files:
        img_path = test_images_dir / img_name
        raw_img = Image.open(img_path)
        w, h = raw_img.size
        visible_spines = AUDITED_VISIBLE_SPINES.get(img_name, 0)
        total_visible += visible_spines

        # Measure warm inference time (average of 3 runs for stability)
        times = []
        for _ in range(3):
            t0 = time.perf_counter()
            det_result = detector.detect_books(raw_img)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000.0)
        infer_ms = round(sum(times) / len(times), 2)
        warm_latencies.append(infer_ms)

        boxes_count = len(det_result.detections)
        total_boxes += boxes_count

        if boxes_count == 0:
            zero_detection_images += 1

        # Classifications from visual audit
        clf = AUDITED_YOLO26N_CLASSIFICATIONS.get(img_name, {
            "unique_usable": 0, "duplicates": 0, "grouped": 0, "false_positives": 0
        })
        unique_usable = clf["unique_usable"]
        duplicates = clf["duplicates"]
        grouped = clf["grouped"]
        false_positives = clf["false_positives"]
        missed = visible_spines - unique_usable

        total_unique_usable += unique_usable
        total_duplicates += duplicates
        total_grouped += grouped
        total_false_pos += false_positives
        total_missed += missed

        manual_recall = round(unique_usable / visible_spines, 4) if visible_spines > 0 else 0.0
        denom = unique_usable + duplicates + grouped + false_positives
        precision_proxy = round(unique_usable / denom, 4) if denom > 0 else 0.0

        # Annotate & save debug image
        annotated_img = draw_annotations(raw_img, det_result.detections)
        annotated_path = results_dir / f"{Path(img_name).stem}_annotated.jpg"
        annotated_img.save(annotated_path, quality=90)

        # Save crops
        img_crop_dir = crops_dir / Path(img_name).stem
        img_crop_dir.mkdir(parents=True, exist_ok=True)

        for det in det_result.detections:
            crop = extract_crop(raw_img, det["bbox"])
            crop_path = img_crop_dir / f"{det['detection_id']}.jpg"
            crop.save(crop_path, quality=85)

        benchmark_rows.append({
            "filename": img_name,
            "dimensions": f"{w}x{h}",
            "visible_spines": visible_spines,
            "detected_boxes": boxes_count,
            "unique_usable_spines": unique_usable,
            "duplicates": duplicates,
            "grouped_boxes": grouped,
            "false_positives": false_positives,
            "missed_spines": missed,
            "manual_recall": manual_recall,
            "manual_precision_proxy": precision_proxy,
            "inference_ms": infer_ms,
        })

    avg_warm_ms = round(sum(warm_latencies) / len(warm_latencies), 2)
    sorted_latencies = sorted(warm_latencies)
    median_warm_ms = sorted_latencies[len(sorted_latencies) // 2]
    micro_recall = round(total_unique_usable / total_visible, 4) if total_visible > 0 else 0.0
    macro_recall = round(sum(r["manual_recall"] for r in benchmark_rows) / len(benchmark_rows), 4)

    # Save test-images/evaluation.csv
    eval_csv_path = test_images_dir / "evaluation.csv"
    with open(eval_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "filename", "visible_spines", "detected_boxes", "unique_usable_spines",
            "duplicates", "grouped_boxes", "false_positives", "missed_spines",
            "manual_recall", "manual_precision_proxy", "inference_ms"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in benchmark_rows:
            writer.writerow({k: r[k] for k in fieldnames})

    print("\nBENCHMARK RESULTS TABLE (AUDITED METHODOLOGY):")
    print(f"{'Filename':<22} | {'Vis':<4} | {'Box':<4} | {'Uniq':<4} | {'Dup':<3} | {'Grp':<3} | {'FP':<3} | {'Miss':<4} | {'Recall':<7} | {'PrecProxy':<9} | {'Warm (ms)'}")
    print("-" * 105)
    for r in benchmark_rows:
        print(f"{r['filename']:<22} | {r['visible_spines']:<4} | {r['detected_boxes']:<4} | {r['unique_usable_spines']:<4} | {r['duplicates']:<3} | {r['grouped_boxes']:<3} | {r['false_positives']:<3} | {r['missed_spines']:<4} | {r['manual_recall']:<7.2%} | {r['manual_precision_proxy']:<9.2%} | {r['inference_ms']} ms")
    print("-" * 105)
    print(f"Aggregate Visible Spines:         {total_visible}")
    print(f"Aggregate Detected Boxes:         {total_boxes}")
    print(f"Aggregate Unique Usable Spines:   {total_unique_usable}")
    print(f"Aggregate Duplicates:             {total_duplicates}")
    print(f"Aggregate Grouped Boxes:          {total_grouped}")
    print(f"Aggregate False Positives:        {total_false_pos}")
    print(f"Aggregate Missed Spines:          {total_missed}")
    print(f"Micro Usable-Crop Recall:         {micro_recall:.2%}")
    print(f"Macro Usable-Crop Recall:         {macro_recall:.2%}")
    print(f"Images with Zero Usable Detections: {zero_detection_images} of {len(benchmark_rows)}")
    print(f"Model Cold-Start Load Time:       {load_time_ms:.2f} ms")
    print(f"Average Warm CPU Latency:         {avg_warm_ms:.2f} ms")
    print(f"Median Warm CPU Latency:          {median_warm_ms:.2f} ms")
    print("=========================================================\n")

    return {
        "model_name": model_name,
        "load_time_ms": load_time_ms,
        "avg_warm_ms": avg_warm_ms,
        "median_warm_ms": median_warm_ms,
        "total_visible": total_visible,
        "total_unique_usable": total_unique_usable,
        "micro_recall": micro_recall,
        "macro_recall": macro_recall,
        "zero_detection_images": zero_detection_images,
        "rows": benchmark_rows,
    }


if __name__ == "__main__":
    run_benchmark()
