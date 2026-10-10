"""
AI-generated image detector.

Uses real signals — not a deep learning classifier (those are unreliable).

Detection layers:
  1. EXIF metadata — many AI tools write identifying tags
  2. PNG text chunks — Midjourney/Stable Diffusion embed prompt data
  3. Filename patterns — common download names
  4. Image dimensions — unusual aspect ratios typical of AI generators
  5. Missing camera EXIF — real photos have Make/Model/LensModel; AI images don't

Returns a verdict with human-readable reasons.
"""

import re
from pathlib import Path

from PIL import Image, ExifTags


# Known AI tool signals
AI_FILENAME_PATTERNS = [
    r"midjourney",
    r"mj_",
    r"dall[\-_]?e",
    r"stable[\-_]?diffusion",
    r"sd[\-_]?xl",
    r"stablediffusion",
    r"flux[\-_]",
    r"firefly",
    r"leonardo[\-_]",
    r"adobe[\-_]?firefly",
    r"generated[\-_]?image",
    r"ai[\-_]?gen",
]

# EXIF Software field values that indicate AI tools
AI_SOFTWARE_TAGS = [
    "midjourney",
    "dall-e",
    "dall·e",
    "stable diffusion",
    "stablediffusion",
    "firefly",
    "leonardo.ai",
    "flux",
]

# PNG "Software" / "Comment" text chunk patterns (text inside PNG)
AI_PNG_TEXT_MARKERS = [
    "midjourney",
    "stable diffusion",
    "sd-xl",
    "prompt:",
    "negative prompt:",
    "steps:",
    "sampler:",
    "cfg scale:",
    "seed:",
]

# Common AI-image dimensions (DALL-E 3, Midjourney defaults)
SUSPICIOUS_DIMENSIONS = {
    (1024, 1024),   # DALL-E 3 square
    (1792, 1024),   # DALL-E 3 wide
    (1024, 1792),   # DALL-E 3 tall
    (512, 512),     # Stable Diffusion 1.5 default
    (768, 768),     # SD 2.0 default
    (2048, 2048),   # MJ HD
    (1456, 816),    # MJ v6 wide
    (816, 1456),    # MJ v6 tall
}

# Camera EXIF tags that real photos almost always have
CAMERA_EXIF_TAGS = [
    "Make",
    "Model",
    "LensModel",
    "FNumber",
    "ExposureTime",
    "ISOSpeedRatings",
    "FocalLength",
]


def _get_exif_dict(img: Image.Image) -> dict:
    """Extract EXIF tags from a PIL image, keyed by tag name."""
    try:
        raw_exif = img.getexif()
    except Exception:
        return {}
    if not raw_exif:
        return {}
    out = {}
    for tag_id, value in raw_exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
        out[tag_name] = value
    return out


def _check_filename(path: Path) -> tuple[float, str | None]:
    """Filename patterns matching known AI tools."""
    name = path.name.lower()
    for pattern in AI_FILENAME_PATTERNS:
        if re.search(pattern, name):
            return 0.4, f"Filename matches AI tool pattern: {pattern}"
    return 0.0, None


def _check_exif_software(exif: dict) -> tuple[float, str | None]:
    """Software tag in EXIF indicating AI tool."""
    software = str(exif.get("Software", "")).lower()
    for marker in AI_SOFTWARE_TAGS:
        if marker in software:
            return 0.8, f"EXIF Software field names AI tool: {software}"
    return 0.0, None


def _check_png_text(img: Image.Image) -> tuple[float, str | None]:
    """PNG text chunks often carry AI-generation metadata."""
    try:
        text_chunks = getattr(img, "text", None) or {}
    except Exception:
        text_chunks = {}
    if not text_chunks:
        # Also check info dict (PIL exposes some text there)
        text_chunks = getattr(img, "info", {}) or {}

    combined = " ".join(str(v).lower() for v in text_chunks.values())
    for marker in AI_PNG_TEXT_MARKERS:
        if marker in combined:
            return 0.9, f"PNG metadata contains AI marker: {marker}"
    return 0.0, None


def _check_dimensions(img: Image.Image) -> tuple[float, str | None]:
    """Common AI-generated dimensions."""
    dims = img.size
    if dims in SUSPICIOUS_DIMENSIONS:
        return 0.3, f"Dimensions {dims[0]}x{dims[1]} match common AI output sizes"
    return 0.0, None


def _check_missing_camera_exif(exif: dict) -> tuple[float, str | None]:
    """
    Real camera photos almost always carry Make/Model/LensModel.
    If NONE of those are present, it's a weak signal (could be a screenshot,
    a downloaded wallpaper, or an AI image).
    """
    present = [tag for tag in CAMERA_EXIF_TAGS if tag in exif]
    if len(present) == 0:
        return 0.1, "No camera EXIF (Make/Model/LensModel) found"
    return 0.0, None


def classify_image(file_path: str | Path) -> dict:
    """
    Analyze an image for signs of AI generation.

    Returns:
        {
            "is_ai": bool,                    # True if score ≥ threshold
            "score": float,                   # 0.0 – 1.0
            "reasons": list[str],             # human-readable explanations
            "signals": dict,                  # individual signal details
            "error": str | None,
        }
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "is_ai": False,
            "score": 0.0,
            "reasons": [],
            "signals": {},
            "error": f"File not found: {file_path}",
        }

    score = 0.0
    reasons: list[str] = []
    signals: dict = {}

    try:
        # Filename check
        s, r = _check_filename(path)
        if s > 0:
            score += s
            reasons.append(r)
            signals["filename"] = r

        # Open image
        with Image.open(path) as img:
            exif = _get_exif_dict(img)

            # EXIF Software field
            s, r = _check_exif_software(exif)
            if s > 0:
                score += s
                reasons.append(r)
                signals["exif_software"] = r

            # PNG text chunks
            s, r = _check_png_text(img)
            if s > 0:
                score += s
                reasons.append(r)
                signals["png_text"] = r

            # Suspicious dimensions
            s, r = _check_dimensions(img)
            if s > 0:
                score += s
                reasons.append(r)
                signals["dimensions"] = r

            # Missing camera EXIF (weak signal)
            s, r = _check_missing_camera_exif(exif)
            if s > 0:
                score += s
                reasons.append(r)
                signals["no_camera_exif"] = r

    except Exception as e:
        return {
            "is_ai": False,
            "score": 0.0,
            "reasons": [],
            "signals": {},
            "error": f"Analysis failed: {e}",
        }

    # Cap score at 1.0
    score = min(score, 1.0)

    # Threshold: strong signal OR combination of weak signals
    is_ai = score >= 0.7

    return {
        "is_ai": is_ai,
        "score": round(score, 3),
        "reasons": reasons,
        "signals": signals,
        "error": None,
    }


def describe_verdict(verdict: dict) -> str:
    """Turn a verdict into a short human-readable string."""
    if not verdict["is_ai"]:
        return ""
    return " | ".join(verdict["reasons"])[:500]
