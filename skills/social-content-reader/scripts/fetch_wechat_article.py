#!/usr/bin/env python3
"""Fetch a public WeChat 公众号 article body over HTTPS (stdlib only).

Uses a fixed Chrome desktop User-Agent. No cookies, browser profiles, captcha
defeat, IP rotation, or private APIs. A share caption / og title is metadata.

Success requires a substantive article body in #js_content (or documented
fallbacks). WeChat SSR often ships #js_content with visibility:hidden;opacity:0
— that is still a real body. display:none and 环境异常 / captcha shells fail.

Embedded mpvideo iframes are extracted as metadata. Optionally, when
acquire_media helpers (Playwright + ffmpeg) are importable, the first embed's
public player is attempted; article success does not depend on media.

Stdout is one JSON receipt. See platforms/wechat-article.md.
"""
from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse


CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 120
MAX_HTML_BYTES = 8 * 1024 * 1024
MIN_BODY_CHARS = 40
BODY_SELECTORS = (
    "js_content",
    "js_article_content",
)
BODY_CLASSES = ("rich_media_content",)
CAPTCHA_MARKERS = (
    "环境异常",
    "完成验证后即可继续访问",
    "访问过于频繁",
    "请输入验证码",
    "系统繁忙，此时请开发者关注",
)
MPVIDEO_IFRAME_RE = re.compile(
    r"<iframe\b([^>]*)>",
    re.IGNORECASE | re.DOTALL,
)
ATTR_RE = re.compile(
    r"""([^\s=]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""",
    re.IGNORECASE,
)
VID_RE = re.compile(r"wxv_\d+")
LETTER_RE = re.compile(r"[0-9A-Za-z\u4e00-\u9fff]")


class FetchError(Exception):
    def __init__(self, status: str, message: str, **extra: Any):
        super().__init__(message)
        self.status = status
        self.message = message
        self.extra = extra


def _attrs(tag_attrs: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in ATTR_RE.finditer(tag_attrs):
        key = m.group(1).lower()
        val = m.group(2) if m.group(2) is not None else (
            m.group(3) if m.group(3) is not None else m.group(4) or ""
        )
        out[key] = html_lib.unescape(val)
    return out


def _style_dict(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in (style or "").split(";"):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        result[k.strip().lower()] = v.strip().lower()
    return result


def _is_display_none(style: str) -> bool:
    styles = _style_dict(style)
    return styles.get("display") == "none"


def _ssr_hidden_ok(style: str) -> bool:
    """WeChat SSR hides #js_content with visibility/opacity until JS runs."""
    styles = _style_dict(style)
    if styles.get("display") == "none":
        return False
    # visibility:hidden and/or opacity:0 alone are acceptable for SSR.
    return True


def _strip_tags(fragment: str) -> str:
    # Drop script/style blocks first.
    fragment = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>",
        " ",
        fragment,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = html_lib.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _substantive_count(text: str) -> int:
    return len(LETTER_RE.findall(text))


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.author = ""
        self.og_url = ""
        self._in_title = False
        self._title_bits: list[str] = []

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if tag == "meta":
            prop = (ad.get("property") or ad.get("name") or "").lower()
            content = ad.get("content") or ""
            if prop in ("og:title", "twitter:title") and content and not self.title:
                self.title = content.strip()
            elif prop in ("og:article:author", "author") and content and not self.author:
                self.author = content.strip()
            elif prop == "og:url" and content and not self.og_url:
                self.og_url = content.strip()
        if tag == "title":
            self._in_title = True
            self._title_bits = []
        if tag in ("a", "span", "strong") and ad.get("id") == "js_name" and not self.author:
            self.author = (ad.get("data-name") or "").strip()

    def handle_data(self, data):
        if self._in_title:
            self._title_bits.append(data)

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            if not self.title:
                self.title = "".join(self._title_bits).strip()


def _find_body_region(html: str) -> tuple[str, str, str] | None:
    """Return (selector, open_tag_attrs_style_hint, inner_html) or None."""
    # Prefer #js_content, then #js_article_content, then .rich_media_content,
    # then [itemprop=articleBody].
    patterns = [
        (r'id=["\']js_content["\']', "js_content"),
        (r'id=["\']js_article_content["\']', "js_article_content"),
        (r'class=["\'][^"\']*\brich_media_content\b[^"\']*["\']', "rich_media_content"),
        (r'itemprop=["\']articleBody["\']', "itemprop=articleBody"),
    ]
    for pat, name in patterns:
        for m in re.finditer(r"<([a-zA-Z0-9]+)([^>]*)\s" + pat[0:].replace("\\b", r"\b") if False else "", html):
            pass
        # Simpler: find opening tag containing the marker.
        open_re = re.compile(
            rf"<([a-zA-Z0-9]+)([^>]*{pat}[^>]*)>",
            re.IGNORECASE | re.DOTALL,
        )
        om = open_re.search(html)
        if not om:
            continue
        tag = om.group(1)
        attrs = om.group(2)
        start = om.end()
        # Walk to matching close tag (depth-aware for same tag name).
        close_re = re.compile(rf"</{tag}\s*>", re.IGNORECASE)
        open_same = re.compile(rf"<{tag}\b[^>]*>", re.IGNORECASE)
        depth = 1
        pos = start
        end = None
        while depth and pos < len(html):
            n_open = open_same.search(html, pos)
            n_close = close_re.search(html, pos)
            if not n_close:
                break
            if n_open and n_open.start() < n_close.start():
                depth += 1
                pos = n_open.end()
            else:
                depth -= 1
                if depth == 0:
                    end = n_close.start()
                    break
                pos = n_close.end()
        if end is None:
            # Fallback: cut at next major script after content for SSR pages.
            sm = re.search(r"</div>\s*<script", html[start:], re.IGNORECASE)
            if not sm:
                continue
            end = start + sm.start()
        style = _attrs(attrs).get("style", "")
        return name, style, html[start:end]
    return None


def extract_mpvideo_embeds(html: str, base_url: str = "") -> list[dict[str, str]]:
    embeds: list[dict[str, str]] = []
    seen: set[str] = set()
    for m in MPVIDEO_IFRAME_RE.finditer(html):
        attrs = _attrs(m.group(1))
        raw = attrs.get("data-src") or attrs.get("src") or ""
        if not raw:
            continue
        raw = html_lib.unescape(raw)
        if "action=mpvideo" not in raw and "video_player_tmpl" not in raw:
            # Still accept explicit data-mpvid frames.
            vid = attrs.get("data-mpvid") or ""
            if not VID_RE.fullmatch(vid):
                continue
            player = (
                "https://mp.weixin.qq.com/mp/readtemplate?"
                f"t=pages/video_player_tmpl&action=mpvideo&auto=0&vid={vid}"
            )
        else:
            player = urljoin(base_url or "https://mp.weixin.qq.com/", raw)
            qs = parse_qs(urlparse(player).query)
            action = (qs.get("action") or [""])[0]
            if action and action != "mpvideo":
                continue
            vid = attrs.get("data-mpvid") or (qs.get("vid") or [""])[0]
            if not VID_RE.fullmatch(vid):
                # Try vid from URL path/query after unescape
                found = VID_RE.search(player)
                vid = found.group(0) if found else ""
            if not VID_RE.fullmatch(vid):
                continue
            # Normalize player URL
            player = (
                "https://mp.weixin.qq.com/mp/readtemplate?"
                f"t=pages/video_player_tmpl&action=mpvideo&auto=0&vid={vid}"
            )
        if vid in seen:
            continue
        seen.add(vid)
        embeds.append({
            "vid": vid,
            "player_url": player,
            "cover": unquote(attrs.get("data-cover") or "") or None,
        })
        if embeds[-1]["cover"] is None:
            embeds[-1].pop("cover")
    return embeds


def parse_article_html(html: str, source_url: str = "") -> dict[str, Any]:
    if not html or not html.strip():
        raise FetchError("fetch_failed", "empty HTML")

    lower = html
    # Captcha / environment shells: title or prominent verification copy
    # without a substantive body.
    meta = _MetaParser()
    try:
        meta.feed(html)
    except Exception:
        pass

    region = _find_body_region(html)
    captcha_hit = any(marker in html for marker in CAPTCHA_MARKERS)
    title_looks_verify = any(
        token in (meta.title or "") for token in ("环境异常", "验证", "未知错误")
    )

    if region is None:
        if captcha_hit or title_looks_verify:
            raise FetchError(
                "captcha_required",
                "verification / 环境异常 shell; no substantive #js_content",
                title=meta.title or None,
            )
        raise FetchError("unavailable", "no article body container found")

    selector, style, inner = region
    if _is_display_none(style):
        if captcha_hit or title_looks_verify:
            raise FetchError(
                "captcha_required",
                "verification / 环境异常 shell; #js_content is display:none",
                title=meta.title or None,
            )
        raise FetchError(
            "unavailable",
            f"{selector} has display:none; refusing hidden shell",
            title=meta.title or None,
        )
    if not _ssr_hidden_ok(style):
        raise FetchError(
            "unavailable",
            f"{selector} style not accepted",
            title=meta.title or None,
        )

    body_text = _strip_tags(inner)
    count = _substantive_count(body_text)
    if count < MIN_BODY_CHARS:
        if captcha_hit:
            raise FetchError(
                "captcha_required",
                "verification shell with empty/short body",
                title=meta.title or None,
                body_chars=count,
            )
        raise FetchError(
            "unavailable",
            f"body too short ({count} < {MIN_BODY_CHARS} letters/digits/CJK)",
            title=meta.title or None,
            body_chars=count,
        )

    # Captcha markers may appear in article prose; only reject when the
    # page title/shell is the verification page.
    if captcha_hit and count < 200 and (
        "环境异常" in (meta.title or "") or "验证" in (meta.title or "")
    ):
        raise FetchError(
            "captcha_required",
            "verification page, not an article",
            title=meta.title or None,
        )

    embeds = extract_mpvideo_embeds(html, source_url)
    return {
        "ok": True,
        "status": "ok",
        "platform": "wechat-article",
        "source_url": source_url,
        "canonical_url": meta.og_url or source_url,
        "title": meta.title or None,
        "author": meta.author or None,
        "body_text": body_text,
        "body_chars": count,
        "body_kind": "article",
        "body_selector": selector,
        "ssr_visibility_hidden": "visibility" in _style_dict(style)
        and "hidden" in _style_dict(style).get("visibility", ""),
        "fetch_method": "public_https_chrome_ua",
        "embeds": embeds,
        "embed_count": len(embeds),
    }


def fetch_html(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_HTML_BYTES,
) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise FetchError("fetch_failed", "expected an https:// mp.weixin.qq.com URL")
    host = parsed.hostname.lower()
    if host != "mp.weixin.qq.com" and not host.endswith(".mp.weixin.qq.com"):
        raise FetchError("fetch_failed", "only mp.weixin.qq.com article URLs are supported")
    if parsed.username or parsed.password:
        raise FetchError("fetch_failed", "URL must not include credentials")

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": CHROME_UA,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
        method="GET",
    )
    ctx = ssl.create_default_context()
    deadline = time.monotonic() + timeout
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            final_url = resp.geturl()
            status = getattr(resp, "status", None) or resp.getcode()
            if status == 429:
                raise FetchError(
                    "rate_limited",
                    "HTTP 429",
                    retry_after=resp.headers.get("Retry-After"),
                )
            if status >= 400:
                raise FetchError("fetch_failed", f"HTTP {status}")
            chunks: list[bytes] = []
            total = 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise FetchError("fetch_failed", f"deadline exceeded ({timeout}s)")
                block = resp.read(64 * 1024)
                if not block:
                    break
                total += len(block)
                if total > max_bytes:
                    raise FetchError(
                        "fetch_failed",
                        f"HTML exceeds max_bytes ({max_bytes})",
                    )
                chunks.append(block)
            raw = b"".join(chunks)
    except FetchError:
        raise
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise FetchError(
                "rate_limited",
                "HTTP 429",
                retry_after=exc.headers.get("Retry-After") if exc.headers else None,
            ) from exc
        raise FetchError("fetch_failed", f"HTTP {exc.code}") from exc
    except Exception as exc:
        raise FetchError("fetch_failed", f"{type(exc).__name__}: {exc}") from exc

    # Decode
    charset = "utf-8"
    for m in re.finditer(rb"charset\s*=\s*([\"']?)([a-zA-Z0-9_\-]+)", raw[:4096], re.I):
        charset = m.group(2).decode("ascii", "ignore") or "utf-8"
        break
    try:
        text = raw.decode(charset, errors="replace")
    except LookupError:
        text = raw.decode("utf-8", errors="replace")
    return text, final_url


def try_acquire_first_embed(
    embeds: list[dict[str, str]],
    out_dir: Path | None,
    referer: str,
) -> dict[str, Any] | None:
    """Best-effort public player media for the first embed. Never required."""
    if not embeds or out_dir is None:
        return None
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return {
            "ok": False,
            "error": "playwright not installed; embed media acquire skipped",
            "vid": embeds[0]["vid"],
        }
    try:
        import acquire_media as am
    except ImportError:
        am = None

    embed = embeds[0]
    player = embed["player_url"]
    vid = embed["vid"]
    out_dir = Path(out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--autoplay-policy=no-user-gesture-required"],
            )
            try:
                context = browser.new_context(
                    user_agent=CHROME_UA,
                    locale="zh-CN",
                    extra_http_headers={"Referer": referer},
                )
                page = context.new_page()
                observed: list[str] = []

                def on_response(response):
                    ct = response.headers.get("content-type", "")
                    if response.status in (200, 206) and (
                        "video" in ct
                        or "mpegurl" in ct
                        or ".mp4" in response.url
                        or ".m3u8" in response.url
                    ):
                        observed.append(response.url)

                page.on("response", on_response)
                page.goto(player, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(6000)
                body_snip = ""
                try:
                    body_snip = page.inner_text("body")[:240]
                except Exception:
                    pass
                videos = page.locator("video").evaluate_all(
                    """vs => vs.map(v => ({
                        src: v.currentSrc || v.src,
                        sources: [...v.querySelectorAll('source')].map(s => s.src),
                        duration: Number.isFinite(v.duration) ? v.duration : null
                    }))"""
                )
                urls: list[str] = []
                for v in videos or []:
                    if v.get("src"):
                        urls.append(v["src"])
                    urls.extend(v.get("sources") or [])
                urls.extend(observed)
                urls = list(dict.fromkeys(u for u in urls if isinstance(u, str) and u.startswith("https://")))
                if not urls:
                    return {
                        "ok": False,
                        "vid": vid,
                        "player_url": player,
                        "error": "public mpvideo player exposed no media URL",
                        "body_snip": body_snip,
                    }
                if am is None:
                    return {
                        "ok": False,
                        "vid": vid,
                        "error": "acquire_media helpers unavailable for download/probe",
                        "candidate_urls": len(urls),
                    }
                errors = []
                for media_url in urls[:3]:
                    target = out_dir / f"wechat-mpvideo_{vid}.mp4"
                    try:
                        am.download(context, media_url, player, target, 128 * 1024**2)
                        info = am.probe(target)
                        digest = __import__("hashlib").sha256(target.read_bytes()).hexdigest()
                        final = out_dir / f"wechat-mpvideo_{digest[:16]}.mp4"
                        target.replace(final)
                        return {
                            "ok": True,
                            "vid": vid,
                            "player_url": player,
                            "path": str(final),
                            "bytes": final.stat().st_size,
                            "sha256": digest,
                            "method": "public_mpvideo_player",
                            **info,
                        }
                    except Exception as exc:
                        errors.append(str(exc))
                        target.unlink(missing_ok=True)
                return {
                    "ok": False,
                    "vid": vid,
                    "player_url": player,
                    "error": "; ".join(errors) or "media download failed",
                    "body_snip": body_snip,
                }
            finally:
                browser.close()
    except Exception as exc:
        return {
            "ok": False,
            "vid": vid,
            "player_url": player,
            "error": f"{type(exc).__name__}: embed acquire failed",
        }


def fetch_article(
    url: str,
    out_dir: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_HTML_BYTES,
    try_embed_media: bool = True,
    html: str | None = None,
) -> dict[str, Any]:
    """Fetch+parse a 公众号 article. Pass html= to parse offline (tests)."""
    try:
        if html is None:
            html, final_url = fetch_html(url, timeout=timeout, max_bytes=max_bytes)
            source = final_url or url
        else:
            source = url
        result = parse_article_html(html, source_url=source)
        if try_embed_media and result.get("embeds") and out_dir is not None:
            media = try_acquire_first_embed(result["embeds"], out_dir, referer=source)
            if media is not None:
                result["embed_media"] = media
        if out_dir is not None:
            out_dir = Path(out_dir).expanduser().resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            receipt = out_dir / "wechat-article.json"
            # Do not dump full body into a second huge copy when HTML saved separately;
            # receipt is the JSON result.
            receipt.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result["receipt_path"] = str(receipt)
        return result
    except FetchError as exc:
        payload = {
            "ok": False,
            "status": exc.status,
            "platform": "wechat-article",
            "source_url": url,
            "error": exc.message,
            "body_kind": "unavailable",
            "fetch_method": "public_https_chrome_ua",
            **exc.extra,
        }
        return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="https://mp.weixin.qq.com/s/... article URL")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-bytes", type=int, default=MAX_HTML_BYTES)
    parser.add_argument(
        "--no-embed-media",
        action="store_true",
        help="skip optional first-embed media acquire",
    )
    parser.add_argument(
        "--html-file",
        type=Path,
        default=None,
        help="parse local HTML instead of fetching (offline / tests)",
    )
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.max_bytes <= 0:
        parser.error("--timeout and --max-bytes must be positive")
    html = None
    if args.html_file is not None:
        html = args.html_file.read_text(encoding="utf-8", errors="replace")
    result = fetch_article(
        args.url,
        out_dir=args.out_dir,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
        try_embed_media=not args.no_embed_media,
        html=html,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
