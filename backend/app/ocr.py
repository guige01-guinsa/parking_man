from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Any

from .plates import extract_plate_candidates


@dataclass(slots=True)
class OCRScanResult:
    provider: str
    raw_text: str
    candidates: list[str]
    error: str | None = None


def _run_tesseract(image_bytes: bytes) -> OCRScanResult:
    try:
        from PIL import Image, ImageOps
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
        grayscale = ImageOps.grayscale(image)
        enhanced = ImageOps.autocontrast(grayscale)
        big = enhanced.resize((enhanced.width * 2, enhanced.height * 2))
        lang = os.getenv("PARKING_OCR_LANG", "kor+eng")
        configs = ["--psm 7", "--psm 6"]
        outputs: list[str] = []
        for config in configs:
            outputs.append(pytesseract.image_to_string(big, lang=lang, config=config))
        raw_text = "\n".join(part for part in outputs if part).strip()
        return OCRScanResult(
            provider="tesseract",
            raw_text=raw_text,
            candidates=extract_plate_candidates(raw_text),
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

