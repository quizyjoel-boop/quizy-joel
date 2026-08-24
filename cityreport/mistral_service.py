"""
Mistral AI agent used to replicate CivicSpot's "AI does the rest" flow:
given a citizen's raw description (and optionally a photo), it:
  1. classifies the report into one of the known categories
  2. drafts a clean, professional description
  3. scores a hazard/priority level (low / medium / high)

Falls back to a lightweight keyword classifier when no MISTRAL_API_KEY is
configured, so the app is fully runnable/demoable without a live key.
"""
import base64
import json
import os
import requests

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

CATEGORIES = ["pothole", "streetlight", "waste", "other"]

SYSTEM_PROMPT = f"""You are the triage AI for CityReport, a civic issue reporting
platform for Douala, Cameroon. Given a citizen's report text (and possibly a photo),
respond ONLY with a JSON object, no markdown, no preamble, with exactly these keys:

- "category": one of {CATEGORIES}
- "summary": a clean, professional 1-2 sentence description of the issue,
  written for a city works order (rewrite the citizen's raw text)
- "hazard_level": one of "low", "medium", "high" — based on danger to
  pedestrians/drivers/public health (e.g. a deep pothole on a busy road or
  waste blocking a drain is "high"; a cosmetic issue is "low")
- "confidence": a number between 0 and 1 for your classification confidence

Only output the JSON object."""


def _keyword_fallback(description: str):
    """Used when no API key is set, so the app still works end-to-end."""
    text = description.lower()
    scored = {
        "pothole": ["pothole", "hole", "road", "crack", "asphalt", "pavement"],
        "streetlight": ["streetlight", "light", "lamp", "dark", "bulb"],
        "waste": ["waste", "garbage", "trash", "rubbish", "dump", "bin"],
    }
    best_cat, best_hits = "other", 0
    for cat, kws in scored.items():
        hits = sum(1 for k in kws if k in text)
        if hits > best_hits:
            best_cat, best_hits = cat, hits

    danger_words = ["deep", "danger", "urgent", "accident", "child", "busy", "night", "block"]
    hazard = "high" if any(w in text for w in danger_words) else (
        "medium" if best_hits > 0 else "low"
    )

    summary = description.strip()
    if len(summary) > 180:
        summary = summary[:177] + "..."

    return {
        "category": best_cat,
        "summary": summary or "Citizen-reported civic issue.",
        "hazard_level": hazard,
        "confidence": 0.4 if best_hits else 0.2,
    }


def classify_report(description: str, photo_path: str = None):
    """
    Calls the Mistral AI chat completions API to classify a report.
    If photo_path is provided and the model supports vision (pixtral),
    the image is sent alongside the text for richer classification.
    Returns a dict: category, summary, hazard_level, confidence.
    """
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        return _keyword_fallback(description)

    model = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
    user_content = []

    if photo_path and os.path.exists(photo_path):
        # Use a vision-capable model when a photo is attached
        model = os.environ.get("MISTRAL_VISION_MODEL", "pixtral-12b-2409")
        with open(photo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(photo_path)[1].lstrip(".") or "jpeg"
        user_content.append({
            "type": "image_url",
            "image_url": f"data:image/{ext};base64,{b64}",
        })

    user_content.append({
        "type": "text",
        "text": f"Citizen report text: {description}",
    })

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)

        category = data.get("category", "other")
        if category not in CATEGORIES:
            category = "other"

        hazard = data.get("hazard_level", "low")
        if hazard not in ("low", "medium", "high"):
            hazard = "low"

        return {
            "category": category,
            "summary": data.get("summary", description)[:500],
            "hazard_level": hazard,
            "confidence": float(data.get("confidence", 0.5)),
        }
    except Exception as e:
        # Network/API failure -> graceful fallback, never blocks a citizen's report
        fallback = _keyword_fallback(description)
        fallback["error"] = str(e)
        return fallback
