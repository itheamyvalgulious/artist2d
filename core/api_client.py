"""Gemini image API client for the locally hosted NewAPI gateway.

The PLAN pins the generative roles to ``gpt-image-2.5-flare`` (fast) and
``gpt-image-2.5-sunburst`` (high quality).  Per project requirement GPT Image is
replaced by Gemini image models served by the local NewAPI instance:

    role "flare"    -> gemini-3.1-flash-lite-image   (fast masked repaints)
    role "sunburst" -> gemini-nano-banana-2.1        (master references / sheets)

The module provides plain text-to-image generation as well as an edit API that
accepts reference images and a mask.  Masked edits are *locally* composited so
that every pixel outside the mask stays bit-identical to the input, which is what
the border-locked steps of the pipeline rely on.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import random
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

from config.pipeline_config import (
    API_CACHE,
    API_CONCURRENCY,
    API_RETRIES,
    API_TIMEOUT,
    CACHE_DIR,
    LOG_DIR,
    NEWAPI_BASE,
    NEWAPI_KEY,
    ROLE_MODELS,
)

_LOG_LOCK = threading.Lock()


class APIError(RuntimeError):
    pass


def _b64_png(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _hash_bytes(*chunks: bytes) -> str:
    h = hashlib.sha256()
    for c in chunks:
        h.update(c)
    return h.hexdigest()[:24]


class GeminiImageClient:
    """Thin, cached, retrying wrapper around NewAPI's Gemini image endpoint."""

    def __init__(
        self,
        base_url: str = NEWAPI_BASE,
        api_key: str = NEWAPI_KEY,
        cache_dir: Path = CACHE_DIR,
        cache: bool = API_CACHE,
        concurrency: int = API_CONCURRENCY,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        if not self.api_key:
            raise APIError(
                "NEWAPI_KEY is not set: export NEWAPI_KEY=... before calling the image API"
            )
        self.cache_dir = Path(cache_dir) / "api"
        self.log_path = Path(LOG_DIR) / "api_calls.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = cache
        self.concurrency = max(1, concurrency)


    # ------------------------------------------------------------------
    # Low-level call
    # ------------------------------------------------------------------
    def _request(self, model: str, prompt: str, images: list[Image.Image],
                 aspect: str, size: str) -> tuple[list[Image.Image], dict]:
        parts: list[dict] = []
        for idx, img in enumerate(images):
            parts.append({
                "inlineData": {
                    "mimeType": "image/png",
                    "data": _b64_png(img.convert("RGB")),
                }
            })
        parts.append({"text": prompt})
        body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {"aspectRatio": aspect, "imageSize": size},
            },
        }
        url = f"{self.base_url}/v1beta/models/{model}:generateContent"
        data = json.dumps(body).encode()
        last_err: Exception | None = None
        attempt = 0
        overload_retries = 10
        while attempt < API_RETRIES + overload_retries:
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            started = time.time()
            try:
                with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
                    payload = json.loads(resp.read())
                imgs: list[Image.Image] = []
                for cand in payload.get("candidates", []):
                    for part in cand.get("content", {}).get("parts", []):
                        inline = part.get("inlineData") or part.get("inline_data")
                        if inline and inline.get("data"):
                            raw = base64.b64decode(inline["data"])
                            imgs.append(Image.open(io.BytesIO(raw)).convert("RGB"))
                if not imgs:
                    raise APIError(f"no image in response: {json.dumps(payload)[:400]}")
                usage = payload.get("usageMetadata", {})
                self._log(model, prompt, aspect, size, len(images), round(time.time() - started, 2), usage, True)
                return imgs, usage
            except urllib.error.HTTPError as exc:
                detail = exc.read()[:400].decode("utf-8", "replace")
                last_err = APIError(f"HTTP {exc.code}: {detail}")
                if exc.code == 503 and ("overloaded" in detail or "overload" in detail):
                    # NewAPI's own load guard; wait for the host to calm down.
                    time.sleep(20)
                    attempt += 1
                    continue
                if exc.code in (400, 401, 403, 404):
                    break
            except Exception as exc:  # noqa: BLE001 - network/timeouts/parse
                last_err = exc
            sleep = min(30.0, (2 ** min(attempt, 4)) + random.random() * 1.5)
            time.sleep(sleep)
            attempt += 1
        self._log(model, prompt, aspect, size, len(images), 0.0, {}, False)
        raise APIError(str(last_err))

    def _log(self, model, prompt, aspect, size, n_in, seconds, usage, ok):
        rec = {
            "t": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "model": model,
            "aspect": aspect,
            "size": size,
            "images_in": n_in,
            "seconds": seconds,
            "usage": usage,
            "ok": ok,
            "prompt": prompt[:400],
        }
        with _LOG_LOCK:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Public generation API
    # ------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        images: list[Image.Image] | None = None,
        role: str = "sunburst",
        aspect: str = "1:1",
        size: str = "2K",
        tag: str = "",
        fallback: bool = True,
    ) -> list[Image.Image]:
        model = ROLE_MODELS.get(role, ROLE_MODELS["sunburst"])
        images = images or []
        key = _hash_bytes(
            model.encode(),
            prompt.encode(),
            aspect.encode(),
            size.encode(),
            *[img.convert("RGB").resize((64, 64)).tobytes() for img in images],
        )
        if tag:
            key = f"{tag}-{key}" if tag.isalnum() or "-" in tag else key
        cache_path = self.cache_dir / f"{role}-{key}.png"
        if self.cache and cache_path.exists():
            return [Image.open(cache_path).convert("RGB")]
        try:
            imgs, _ = self._request(model, prompt, images, aspect, size)
        except APIError as exc:
            msg = str(exc).lower()
            if fallback and role == "sunburst" and ("429" in msg or "quota" in msg or "exhaust" in msg):
                # The high-quality tier is temporarily quota-limited; keep the
                # pipeline productive with the fast tier and record the swap.
                model = ROLE_MODELS["flare"]
                self._log(model, "[fallback from sunburst] " + prompt, aspect, size, len(images), 0.0, {}, None)
                imgs, _ = self._request(model, prompt, images, aspect, size)
            else:
                raise
        if self.cache:
            imgs[0].save(cache_path)
        return imgs

    def generate_one(self, prompt: str, **kw) -> Image.Image:
        return self.generate(prompt, **kw)[0]

    def edit(
        self,
        prompt: str,
        images: list[Image.Image],
        role: str = "sunburst",
        aspect: str = "1:1",
        size: str = "2K",
        tag: str = "",
        fallback: bool = True,
    ) -> Image.Image:
        return self.generate(prompt, images=images, role=role, aspect=aspect, size=size,
                             tag=tag, fallback=fallback)[0]

    def inpaint(
        self,
        image: Image.Image,
        mask: Image.Image,
        prompt: str,
        role: str = "flare",
        aspect: str = "1:1",
        size: str = "1K",
        tag: str = "",
        refs: list[Image.Image] | None = None,
    ) -> Image.Image:
        """Masked repaint with a hard local guarantee.

        The model receives the source plus a white-on-black mask visualisation
        and is asked to repaint only the white area.  The result is then
        composited back with the *original* pixels wherever the mask is black,
        so protected borders can never drift by a single byte.
        """
        refs = refs or []
        base = image.convert("RGB")
        m = mask.convert("L").resize(base.size, Image.NEAREST)
        overlay = base.copy()
        arr = np.array(overlay)
        mm = np.array(m) > 127
        arr[mm] = (arr[mm] * 0.35 + np.array([255, 0, 0]) * 0.65).astype(np.uint8)
        overlay = Image.fromarray(arr)
        full_prompt = (
            f"{prompt}\n\nThe second image is a mask: pure white means 'repaint this area', "
            "pure black means 'keep exactly as is'. Image 1 shows the masked area tinted red. "
            "Return the complete image with only the masked area regenerated; keep every other "
            "pixel, its edges and the overall composition identical."
        )
        key = _hash_bytes(
            f"inpaint-{role}-{tag}-{prompt}-{base.size}-{aspect}-{size}".encode(),
            base.resize((64, 64)).tobytes(),
            np.array(m.resize((64, 64))).tobytes(),
            *[r.convert("RGB").resize((64, 64)).tobytes() for r in refs],
        )
        cache_path = self.cache_dir / f"inpaint-{key}.png"
        if self.cache and cache_path.exists():
            return Image.open(cache_path).convert("RGB")
        model = ROLE_MODELS.get(role, ROLE_MODELS["flare"])
        try:
            imgs, _ = self._request(model, full_prompt, [base, m.convert("RGB")] + refs, aspect, size)
        except APIError as exc:
            msg = str(exc).lower()
            if role != "flare" and ("429" in msg or "quota" in msg or "exhaust" in msg):
                imgs, _ = self._request(ROLE_MODELS["flare"], full_prompt,
                                        [base, m.convert("RGB")] + refs, aspect, size)
            else:
                raise
        out = imgs[0].resize(base.size, Image.LANCZOS)
        out_arr = np.array(out)
        base_arr = np.array(base)
        out_arr[~mm] = base_arr[~mm]
        result = Image.fromarray(out_arr)
        if self.cache:
            result.save(cache_path)
        return result

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------
    def generate_many(self, jobs: list[dict]) -> list[Image.Image]:
        """Run independent generation jobs concurrently (order preserved)."""
        def run(job: dict) -> Image.Image:
            return self.generate_one(**job)

        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            return list(pool.map(run, jobs))

    def health(self) -> dict:
        out = {}
        for role, model in ROLE_MODELS.items():
            url = f"{self.base_url}/v1beta/models/{model}:generateContent"
            body = json.dumps({
                "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
                "generationConfig": {"responseModalities": ["TEXT"], "maxOutputTokens": 4},
            }).encode()
            req = urllib.request.Request(url, data=body, headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    out[role] = {"model": model, "status": resp.status}
            except urllib.error.HTTPError as exc:
                out[role] = {"model": model, "status": exc.code}
            except Exception as exc:  # noqa: BLE001
                out[role] = {"model": model, "status": str(exc)}
        return out
