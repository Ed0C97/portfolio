# Portfolio excerpt, adapted. Distilled from a shipped Gemini-driven feature that auto-generates Instagram marketing carousels from an article: AI copy -> HTML render -> screenshot -> Cloudinary upload, plus SHA-256 content-hash translation caching.

import os
import json
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import google.generativeai as genai

# separate keys per use case so usage and cost track independently
GEMINI_INSTAGRAM_API_KEY = os.getenv("GEMINI_INSTAGRAM_API_KEY")
GEMINI_TRANSLATION_API_KEY = os.getenv("GEMINI_TRANSLATION_API_KEY")

# tighter than the template can actually fit, so over-long copy gets trimmed instead of re-prompted
MAX_H2_CHARS = 45          # ~6-7 words, max 2 lines
MAX_P_CHARS_WITH_IMAGE = 240
MAX_P_CHARS_NO_IMAGE = 280
MAX_RETRIES = 3
INITIAL_TEMPERATURE = 0.25  # already near-deterministic; drops further per retry


# ============================================================================
# 1. AI COPY  (Gemini, with retry + validate + auto-fix)
# ============================================================================

def _build_model(temperature: float) -> "genai.GenerativeModel":
    genai.configure(api_key=GEMINI_INSTAGRAM_API_KEY)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={
            "temperature": temperature,
            "top_p": 0.95,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",  # force raw JSON, not prose
        },
        system_instruction=(
            "You are a social media manager. Produce EXACTLY 3 carousel slides as a "
            "JSON array of {h2, p}. Output English only. h2 <= 35 chars, p <= 220 "
            "chars, complete sentences ending in a period. No emoji, no lists."
        ),
    )


def safe_json_parse(text: str) -> Optional[object]:
    """Parse JSON from text, digging out the payload when the model wraps it in code fences."""
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        import re
        for pattern in (r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", r"(\{.*\}|\[.*\])"):
            m = re.search(pattern, text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except json.JSONDecodeError:
                    continue
    return None


def _fix_slide(slide: Dict, has_image: bool) -> Dict:
    """Trim h2/p to the card limits, cutting on a word boundary."""
    fixed = dict(slide)
    h2 = (slide.get("h2") or "").strip()
    if len(h2) > MAX_H2_CHARS:
        h2 = h2[:MAX_H2_CHARS].rsplit(" ", 1)[0]
    fixed["h2"] = h2

    p = (slide.get("p") or "").strip()
    max_p = MAX_P_CHARS_WITH_IMAGE if has_image else MAX_P_CHARS_NO_IMAGE
    if len(p) > max_p:
        p = p[:max_p].rsplit(" ", 1)[0].rstrip(",")
        if p and p[-1] not in ".!?":
            p += "."
    fixed["p"] = p
    return fixed


def generate_slides_with_ai(
    article_title: str,
    article_content: str,
    images_available: Optional[List[str]] = None,
    max_retries: int = MAX_RETRIES,
) -> Optional[List[Dict]]:
    """Return 3 validated carousel slides, dropping temperature on each retry."""
    if not article_content or len(article_content) < 100:
        return None
    clean_text = article_content[:30000]  # cap prompt size for latency and cost

    for attempt in range(max_retries):
        try:
            temperature = max(0.1, INITIAL_TEMPERATURE - attempt * 0.05)
            model = _build_model(temperature)
            response = model.generate_content(
                f"TITLE: {article_title}\n\nCONTENT:\n{clean_text}\n\n"
                "Return exactly 3 slides as a JSON array. English only."
            )
            if not response or not response.text:
                continue

            slides = safe_json_parse(response.text)
            if isinstance(slides, dict):  # unwrap {"slides": [...]}-style replies
                slides = next((v for v in slides.values() if isinstance(v, list)), None)
            if not slides or len(slides) < 3:
                continue
            slides = slides[:3]

            # slide 0 is text-only; later slides pair with article images when present
            corrections = 0
            fixed: List[Dict] = []
            for i, slide in enumerate(slides):
                has_image = i > 0 and bool(images_available)
                corrected = _fix_slide(slide, has_image)
                if corrected != slide:
                    corrections += 1
                fixed.append(corrected)

            # take clean output right away; on the final attempt take whatever we have
            if corrections <= 1 or attempt == max_retries - 1:
                return fixed
        except Exception as e:  # noqa: BLE001 - log and retry rather than 500
            print(f"AI attempt {attempt + 1} failed: {e}")
    return None


# ============================================================================
# 2. RENDER  (inject data into an HTML template, screenshot each card)
# ============================================================================

def render_carousel_images(article_data: Dict, template_path: str, output_dir: str) -> List[str]:
    """Render slides to 1080x1350 PNGs in a headless browser."""
    from playwright.sync_api import sync_playwright

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    html = Path(template_path).read_text(encoding="utf-8")

    # design stays in HTML/CSS so designers can iterate without touching Python
    injection = (
        f"<script>window.ARTICLE_DATA = {json.dumps(article_data, ensure_ascii=False)};"
        "document.body.classList.add('data-injected');</script>"
    )
    html = html.replace("</body>", injection + "</body>")
    html_file = Path(output_dir) / "carousel_template.html"
    html_file.write_text(html, encoding="utf-8")

    image_paths: List[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.goto(f"file://{html_file}")
        # wait on signals rather than a fixed sleep: data injected, then cards built
        page.wait_for_selector("body.data-injected")
        page.wait_for_function(
            "document.getElementById('dynamic-slides-container').children.length > 0"
        )
        page.wait_for_timeout(2000)  # let web fonts and images settle

        cards = page.query_selector_all(".instagram-card")
        if not cards:
            raise RuntimeError("No cards found after JS rendering")
        for idx, card in enumerate(cards, start=1):
            path = str(Path(output_dir) / f"slide_{idx}.png")
            card.screenshot(path=path)  # per-element shot, so no manual cropping
            image_paths.append(path)
        browser.close()
    return image_paths


# ============================================================================
# 3. UPLOAD  (Cloudinary, into the article's existing folder)
# ============================================================================

def upload_to_cloudinary(image_paths: List[str], article_image_url: str, slug: str) -> Tuple[List[str], float]:
    """Upload rendered slides into the same Cloudinary folder as the article cover."""
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    )

    # derive the folder from the cover URL so generated assets sit next to the article
    parts = article_image_url.split("/")
    base_folder = "/".join(parts[parts.index("upload") + 2:-1])
    folder = f"{base_folder}/ig/{time.strftime('%Y-%m-%d_%H-%M-%S')}"

    start, urls = time.time(), []
    for path in image_paths:
        try:
            result = cloudinary.uploader.upload(
                path, folder=folder, tags=["carousel-auto-gen", f"slug-{slug}"],
                overwrite=True, invalidate=True,
            )
            urls.append(result["secure_url"])
        except Exception as e:  # one bad upload shouldn't sink the batch
            print(f"Upload failed for {path}: {e}")
            urls.append(None)
    return urls, time.time() - start


# ============================================================================
# 4. ORCHESTRATION  (the shipped end-to-end call)
# ============================================================================

def generate_carousel(article: Dict, template_path: str) -> Dict:
    """Run the pipeline end to end: AI copy -> render -> upload."""
    slides = generate_slides_with_ai(
        article["title"], article["content"], article.get("images", [])
    )
    method = "ai"
    if not slides:  # never block publishing on the model: fall back to article excerpts
        method = "fallback"
        slides = article.get("fallback_slides", [])[:3]

    with tempfile.TemporaryDirectory() as tmp:
        article_data = {"id": article["id"], "slides_content": slides, "method": method}
        images = render_carousel_images(article_data, template_path, tmp)
        urls, upload_time = upload_to_cloudinary(images, article["image_url"], article["slug"])

    return {"method": method, "slide_count": len(slides),
            "urls": [u for u in urls if u], "upload_seconds": round(upload_time, 2)}


# ============================================================================
# Sibling AI feature: SHA-256 content-hash translation cache
# ============================================================================
#
# Translation runs on demand through Gemini, which is slow and billed per call.
# Key the cache on a SHA-256 of the source fields: matching hash serves the stored
# translation, a miss re-translates and re-caches. Any edit to the article changes
# the hash, so the cache invalidates itself.

def content_hash(title: str, subtitle: str, content: str) -> str:
    combined = f"{title}|{subtitle or ''}|{content}"
    return hashlib.sha256(combined.encode()).hexdigest()


def get_or_translate(article, cached, source_lang: str, target_lang: str, force: bool = False):
    """Return the cached translation while the source hash matches, else translate and cache."""
    current = content_hash(article.title, article.subtitle, article.content)
    if cached and cached.content_hash == current and not force:
        return cached, True  # hit, no API call

    genai.configure(api_key=GEMINI_TRANSLATION_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    def _translate(text: str) -> Optional[str]:
        if not text:
            return None
        prompt = (
            f"Translate from {source_lang} to {target_lang}. Keep HTML intact and "
            f"leave proper nouns/brand names untouched. Return only the translation.\n\n{text}"
        )
        return model.generate_content(prompt).text.strip()

    fields = {
        "title_translated": _translate(article.title),
        "subtitle_translated": _translate(article.subtitle),
        "content_translated": _translate(article.content),
        "content_hash": current,  # store the hash this translation was made against
    }
    return fields, False  # caller persists and returns this
