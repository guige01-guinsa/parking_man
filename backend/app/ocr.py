from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Any

from .plates import PLATE_MIDDLE_CHARS, extract_plate_candidates


@dataclass(slots=True)
class OCRScanResult:
    provider: str
    raw_text: str
    candidates: list[str]
    error: str | None = None


def _normalize_tesseract_conf(value: Any) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0
    if number < 0:
        return 0.0
    return number


def _prepare_base_image(image):
    from PIL import ImageOps

    transposed = ImageOps.exif_transpose(image).convert("RGB")
    width, height = transposed.size
    longest = max(width, height)
    shortest = min(width, height)

    scale = 1.0
    if longest > 2200:
        scale = 2200 / longest
    elif shortest < 900:
        scale = 900 / shortest

    if abs(scale - 1.0) > 0.01:
        transposed = transposed.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            resample=getattr(__import__("PIL.Image", fromlist=["Image"]).Image, "Resampling").LANCZOS,
        )
    return transposed


def _to_pil_from_cv(array):
    from PIL import Image

    return Image.fromarray(array)


def _crop_center_band(image):
    width, height = image.size
    left = int(width * 0.06)
    right = int(width * 0.94)
    upper = int(height * 0.26)
    lower = int(height * 0.78)
    return image.crop((left, upper, right, lower))


def _detect_plate_regions(image):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return []

    rgb = np.array(image)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 70, 200)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    merged = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_area = rgb.shape[0] * rgb.shape[1]
    regions: list[tuple[float, Any]] = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h <= 0 or w <= 0:
            continue
        area = w * h
        area_ratio = area / image_area
        aspect_ratio = w / h
        if area_ratio < 0.01 or area_ratio > 0.55:
            continue
        if aspect_ratio < 1.8 or aspect_ratio > 7.2:
            continue
        score = (1.0 - abs(aspect_ratio - 4.2) / 4.2) + (area_ratio * 2.5)
        regions.append((score, (x, y, w, h)))

    regions.sort(key=lambda item: item[0], reverse=True)
    selected = []
    seen_boxes: list[tuple[int, int, int, int]] = []

    for _, (x, y, w, h) in regions:
        overlap = False
        for sx, sy, sw, sh in seen_boxes:
            inter_left = max(x, sx)
            inter_top = max(y, sy)
            inter_right = min(x + w, sx + sw)
            inter_bottom = min(y + h, sy + sh)
            if inter_left < inter_right and inter_top < inter_bottom:
                inter_area = (inter_right - inter_left) * (inter_bottom - inter_top)
                union_area = (w * h) + (sw * sh) - inter_area
                if union_area and (inter_area / union_area) > 0.45:
                    overlap = True
                    break
        if overlap:
            continue

        pad_x = int(w * 0.08)
        pad_y = int(h * 0.18)
        left = max(0, x - pad_x)
        top = max(0, y - pad_y)
        right = min(image.width, x + w + pad_x)
        bottom = min(image.height, y + h + pad_y)
        selected.append(image.crop((left, top, right, bottom)))
        seen_boxes.append((x, y, w, h))
        if len(selected) >= 3:
            break

    return selected


def _build_ocr_variants(image):
    from PIL import ImageEnhance, ImageFilter, ImageOps

    variants: list[tuple[str, Any, float, list[str]]] = []

    base = _prepare_base_image(image)
    grayscale = ImageOps.grayscale(base)
    contrast = ImageOps.autocontrast(grayscale)
    sharpened = contrast.filter(ImageFilter.SHARPEN)
    binary = sharpened.point(lambda pixel: 255 if pixel > 145 else 0)

    variants.append(("full-gray", contrast, 1.0, ["--oem 1 --psm 7", "--oem 1 --psm 6"]))
    variants.append(("full-sharp", sharpened, 1.15, ["--oem 1 --psm 7", "--oem 1 --psm 8"]))
    variants.append(("full-binary", binary, 1.2, ["--oem 1 --psm 7", "--oem 1 --psm 8"]))

    center_band = _crop_center_band(base)
    center_gray = ImageOps.autocontrast(ImageOps.grayscale(center_band))
    center_binary = center_gray.point(lambda pixel: 255 if pixel > 150 else 0)
    variants.append(("center-gray", center_gray, 1.3, ["--oem 1 --psm 7", "--oem 1 --psm 8"]))
    variants.append(("center-binary", center_binary, 1.4, ["--oem 1 --psm 7", "--oem 1 --psm 8"]))

    for index, region in enumerate(_detect_plate_regions(base), start=1):
        region_gray = ImageOps.autocontrast(ImageOps.grayscale(region))
        region_gray = ImageEnhance.Sharpness(region_gray).enhance(1.8)
        region_binary = region_gray.point(lambda pixel: 255 if pixel > 150 else 0)
        variants.append((f"region-{index}-gray", region_gray, 1.55, ["--oem 1 --psm 7", "--oem 1 --psm 8"]))
        variants.append((f"region-{index}-binary", region_binary, 1.7, ["--oem 1 --psm 7", "--oem 1 --psm 8"]))

    return variants


def _collect_ocr_pass(pytesseract, image, lang: str, config: str) -> tuple[str, float]:
    output_dict = pytesseract.image_to_data(
        image,
        lang=lang,
        config=config,
        output_type=pytesseract.Output.DICT,
    )
    texts = [str(text).strip() for text in output_dict.get("text", []) if str(text).strip()]
    confs = [
        _normalize_tesseract_conf(conf)
        for text, conf in zip(output_dict.get("text", []), output_dict.get("conf", []))
        if str(text).strip()
    ]
    raw_text = " ".join(texts).strip()
    confidence = (sum(confs) / len(confs)) if confs else 0.0
    if not raw_text:
        raw_text = pytesseract.image_to_string(image, lang=lang, config=config).strip()
    return raw_text, confidence


def _run_tesseract(image_bytes: bytes) -> OCRScanResult:
    try:
        from PIL import Image
        import pytesseract
    except ImportError as exc:
        return OCRScanResult(
            provider="tesseract",
            raw_text="",
            candidates=[],
            error=f"OCR 라이브러리를 불러오지 못했습니다: {exc}",
        )

    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        image = Image.open(io.BytesIO(image_bytes))
        lang = os.getenv("PARKING_OCR_LANG", "kor+eng")
        whitelist = f"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ{PLATE_MIDDLE_CHARS}"
        tessdata_dir = os.getenv("TESSDATA_PREFIX", "").strip()
        candidate_scores: dict[str, dict[str, float]] = {}
        raw_outputs: list[str] = []

        for variant_name, variant_image, variant_weight, configs in _build_ocr_variants(image):
            for config in configs:
                full_config = f"{config} -c preserve_interword_spaces=0 -c tessedit_char_whitelist={whitelist}"
                if tessdata_dir:
                    full_config += f' --tessdata-dir "{tessdata_dir}"'
                raw_text, confidence = _collect_ocr_pass(pytesseract, variant_image, lang, full_config)
                if not raw_text:
                    continue
                raw_outputs.append(f"[{variant_name}] {raw_text}")
                for rank, plate in enumerate(extract_plate_candidates(raw_text)):
                    entry = candidate_scores.setdefault(plate, {"score": 0.0, "hits": 0.0, "best_conf": 0.0})
                    score = 60.0 + (confidence * 0.65) + (variant_weight * 25.0) - (rank * 7.5)
                    entry["score"] += score
                    entry["hits"] += 1
                    entry["best_conf"] = max(entry["best_conf"], confidence)

        ranked_candidates = sorted(
            candidate_scores.items(),
            key=lambda item: (item[1]["score"], item[1]["hits"], item[1]["best_conf"]),
            reverse=True,
        )
        raw_text = "\n".join(dict.fromkeys(raw_outputs))[:4000].strip()
        return OCRScanResult(
            provider="tesseract",
            raw_text=raw_text,
            candidates=[plate for plate, _ in ranked_candidates[:8]],
        )
    except Exception as exc:
        return OCRScanResult(
            provider="tesseract",
            raw_text="",
            candidates=[],
            error=f"OCR 처리 실패: {exc}",
        )


def scan_plate_image(image_bytes: bytes) -> OCRScanResult:
    provider = os.getenv("PARKING_OCR_PROVIDER", "tesseract").strip().lower()
    if provider in {"", "none", "manual"}:
        return OCRScanResult(provider="manual", raw_text="", candidates=[], error="수동 입력 모드입니다.")
    if provider == "tesseract":
        return _run_tesseract(image_bytes)
    return OCRScanResult(provider=provider, raw_text="", candidates=[], error=f"지원하지 않는 OCR 공급자: {provider}")

