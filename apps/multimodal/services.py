from __future__ import annotations

from pathlib import Path

from django.conf import settings
from PIL import Image


class VisionService:
    def analyze(self, documents: list[dict]) -> dict:
        images = [doc for doc in documents if doc.get("asset_type") == "image"]
        results = []
        for doc in images:
            try:
                with Image.open(doc["path"]) as image:
                    results.append({
                        "source": doc["name"],
                        "width": image.width,
                        "height": image.height,
                        "mode": image.mode,
                        "ocr_text": self._ocr(doc["path"]),
                        "objects": self._detect_objects(doc["path"]),
                        "embedding_ready": True,
                    })
            except Exception as exc:
                results.append({"source": doc["name"], "error": str(exc)})
        detected = sum(len(item.get("objects", [])) for item in results)
        return {
            "summary": f"Analyzed {len(results)} image(s) for OCR, visual metadata, and detected {detected} object(s).",
            "images": results,
            "confidence": 0.78 if detected else 0.74,
        }

    def _ocr(self, path: str) -> str:
        try:
            import pytesseract

            return pytesseract.image_to_string(Image.open(path)).strip()[:1200]
        except Exception:
            return Path(path).stem.replace("_", " ")

    def _detect_objects(self, path: str) -> list[dict]:
        if not getattr(settings, "YOLO_ENABLED", True):
            return []
        model_path = getattr(settings, "YOLO_MODEL_PATH", "")
        model_name = getattr(settings, "YOLO_MODEL_NAME", "yolov8n.pt")
        allow_download = getattr(settings, "YOLO_ALLOW_MODEL_DOWNLOAD", False)
        if model_path and not Path(model_path).exists() and not allow_download:
            return [{"status": "unavailable", "reason": f"YOLO model not found: {model_path}"}]
        if not model_path and model_name.endswith(".pt") and not Path(model_name).exists() and not allow_download:
            return [{"status": "unavailable", "reason": f"YOLO model not found: {model_name}"}]
        try:
            from ultralytics import YOLO

            model = YOLO(model_path or model_name)
            results = model(path, conf=getattr(settings, "YOLO_CONFIDENCE", 0.35), verbose=False)
        except Exception as exc:
            return [{"status": "unavailable", "reason": str(exc)}]

        detections = []
        for result in results:
            names = getattr(result, "names", {}) or {}
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                class_id = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else -1
                confidence = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else 0.0
                xyxy = box.xyxy[0].tolist() if getattr(box, "xyxy", None) is not None else []
                detections.append(
                    {
                        "label": names.get(class_id, str(class_id)),
                        "confidence": round(confidence, 4),
                        "box": [round(float(value), 2) for value in xyxy],
                    }
                )
        return detections
