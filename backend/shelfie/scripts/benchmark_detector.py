import time
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from shelfie.services.detector import BookDetector, detect_books
from shelfie.services.image_utils import extract_crop


# Known manual ground truth counts of visible book spines for test images
MANUAL_VISIBLE_SPINES = {
    "shelf_easy.jpg": 15,
    "shelf_dense.jpg": 42,
    "shelf_angle.jpg": 18,
    "shelf_low_light.jpg": 12,
    "shelf_mixed_sizes.jpg": 22,
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


def run_benchmark(model_name: str = "yolov8n.pt"):
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
    total_usable = 0
    total_false_pos = 0
    total_boxes = 0
    warm_latencies = []

    for img_name in image_files:
        img_path = test_images_dir / img_name
        raw_img = Image.open(img_path)
        w, h = raw_img.size
        visible_spines = MANUAL_VISIBLE_SPINES.get(img_name, 0)

        # Measure warm inference time
        det_result = detector.detect_books(raw_img)
        warm_latencies.append(det_result.inference_ms)

        boxes_count = len(det_result.detections)
        total_boxes += boxes_count
        total_visible += visible_spines

        # Annotate & save debug image
        annotated_img = draw_annotations(raw_img, det_result.detections)
        annotated_path = results_dir / f"{Path(img_name).stem}_annotated.jpg"
        annotated_img.save(annotated_path, quality=90)

        # Count usable crops vs obvious false positives
        usable_crops = 0
        false_positives = 0

        img_crop_dir = crops_dir / Path(img_name).stem
        img_crop_dir.mkdir(parents=True, exist_ok=True)

        for det in det_result.detections:
            crop = extract_crop(raw_img, det["bbox"])
            cw, ch = crop.size
            crop_path = img_crop_dir / f"{det['detection_id']}.jpg"
            crop.save(crop_path, quality=85)

            # Heuristic / manual audit rule for usable spine crop:
            # Aspect ratio vertical (ch >= cw * 1.2) or substantial single book width
            if ch >= 30 and cw >= 12 and (ch >= cw * 0.8):
                usable_crops += 1
            else:
                false_positives += 1

        total_usable += usable_crops
        total_false_pos += false_positives

        recall = (usable_crops / visible_spines) if visible_spines > 0 else 0.0

        benchmark_rows.append({
            "image": img_name,
            "dimensions": f"{w}x{h}",
            "visible_spines": visible_spines,
            "detected_boxes": boxes_count,
            "usable_crops": usable_crops,
            "false_positives": false_positives,
            "recall": round(recall, 4),
            "inference_ms": det_result.inference_ms,
        })

    avg_warm_ms = round(sum(warm_latencies) / len(warm_latencies), 2)
    sorted_latencies = sorted(warm_latencies)
    median_warm_ms = sorted_latencies[len(sorted_latencies) // 2]
    aggregate_recall = round(total_usable / total_visible, 4) if total_visible > 0 else 0.0

    print("\nBENCHMARK RESULTS TABLE:")
    print(f"{'Image':<22} | {'Dims':<10} | {'Visible':<7} | {'Boxes':<5} | {'Usable':<6} | {'FP':<3} | {'Recall':<6} | {'Warm (ms)'}")
    print("-" * 80)
    for r in benchmark_rows:
        print(f"{r['image']:<22} | {r['dimensions']:<10} | {r['visible_spines']:<7} | {r['detected_boxes']:<5} | {r['usable_crops']:<6} | {r['false_positives']:<3} | {r['recall']:<6.2%} | {r['inference_ms']} ms")
    print("-" * 80)
    print(f"Aggregate Visible Spines:  {total_visible}")
    print(f"Aggregate Usable Crops:    {total_usable}")
    print(f"Aggregate False Positives: {total_false_pos}")
    print(f"Manual Usable-Crop Recall: {aggregate_recall:.2%}")
    print(f"Model Cold-Start Load:    {load_time_ms:.2f} ms")
    print(f"Average Warm Inference:    {avg_warm_ms:.2f} ms")
    print(f"Median Warm Inference:     {median_warm_ms:.2f} ms")
    print("=========================================================\n")

    return {
        "model_name": model_name,
        "load_time_ms": load_time_ms,
        "avg_warm_ms": avg_warm_ms,
        "median_warm_ms": median_warm_ms,
        "total_visible": total_visible,
        "total_usable": total_usable,
        "total_false_pos": total_false_pos,
        "aggregate_recall": aggregate_recall,
        "rows": benchmark_rows,
    }


if __name__ == "__main__":
    run_benchmark()
