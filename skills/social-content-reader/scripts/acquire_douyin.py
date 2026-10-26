#!/usr/bin/env python3
"""Acquire a Douyin video from the mobile share player. One JSON object on stdout.

Measured on Mac, 2026-10-26, for https://v.douyin.com/2qulGbSTiRI/
(aweme 7696098282904259850):

  1. Playwright Chromium, mobile UA.
  2. Open https://www.douyin.com/ so this browser receives cookies.
  3. Open https://m.douyin.com/share/video/{aweme_id}.
  4. Read <video>.currentSrc / src. The playing URL looks like
     https://m.douyin.com/aweme/v1/playwm/?...&video_id=v0...
  5. GET that playwm URL with the same browser context and
     Referer set to the mobile share page. It follows to a CDN video/mp4.

That run saved an 8MB 1280x720 H.264+AAC file of about 49 seconds.
iesdouyin.com share pages often show 「请尝试在抖音内观看」 and are not this path.

The helper saves a media file only. It does not return a share caption and
must not be treated as Understanding of the video. Frames, OCR, host vision,
and asr_local.py still have to read the file.

No captcha solving, no login, no cookie file, no CDN decryption.
"""

from __future__ import annotations

import argparse
import importlib
import ipaddress
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


WALL_TEXT = "请尝试在抖音内观看"
HOME_URL = "https://www.douyin.com/"
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)
AWEME_RE = re.compile(r"(?:/video/|/share/video/|aweme_id=|modal_id=)(\d{6,})")
RESOLVE_HOSTS = {
    "v.douyin.com",
    "www.douyin.com",
    "douyin.com",
    "m.douyin.com",
    "www.iesdouyin.com",
    "iesdouyin.com",
}
MIN_MEDIA_BYTES = 4096
MAX_MEDIA_BYTES = 200 * 1024 * 1024
INSTALL_HINT = (
    "Install Playwright and Chromium, then rerun this helper. "
    "macOS/Linux: python3 -m pip install playwright && python3 -m playwright install chromium. "
    "Windows: py -3.12 -m pip install playwright && py -3.12 -m playwright install chromium. "
    "Do not substitute the share caption for the video."
)


class AcquireError(Exception):
    """An actionable error safe to include in the JSON response."""


def aweme_id_from_text(text: str) -> str | None:
    match = AWEME_RE.search(text or "")
    return match.group(1) if match else None


def share_page_url(aweme_id: str) -> str:
    if not aweme_id.isdigit():
        raise AcquireError("aweme id must be digits")
    return f"https://m.douyin.com/share/video/{aweme_id}"


def _host_is_public(hostname: str) -> bool:
    host = (hostname or "").strip(".").lower()
    if not host or host == "localhost" or host.endswith(".local") or host.endswith(".internal"):
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)


def is_public_https(url: str) -> bool:
    parsed = urllib.parse.urlparse(url or "")
    return parsed.scheme == "https" and _host_is_public(parsed.hostname or "")


def pick_video_src(elements: list[dict]) -> str | None:
    """Prefer the playwm URL the mobile player puts on <video>. Ignore blob/data URLs."""
    http_urls: list[str] = []
    for element in elements or []:
        for key in ("currentSrc", "src"):
            raw = str((element or {}).get(key) or "").strip()
            if is_public_https(raw):
                http_urls.append(raw)
    for url in http_urls:
        if "/aweme/v1/playwm" in url:
            return url
    return http_urls[0] if http_urls else None


def redact_play_url(url: str) -> str:
    """Keep host, path, and video_id. Drop signed query parameters."""
    parsed = urllib.parse.urlparse(url or "")
    query = urllib.parse.parse_qs(parsed.query)
    video_ids = query.get("video_id") or []
    kept = f"video_id={video_ids[0]}" if video_ids else ""
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", kept, ""))


def validate_media(body: bytes, content_type: str) -> str | None:
    """Return an error when the response is not a video file. None means accept."""
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype.startswith("text/") or ctype in {"application/json", "application/javascript"}:
        return f"response is {ctype}, not a media file"
    if len(body) < MIN_MEDIA_BYTES:
        return f"response is only {len(body)} bytes"
    if len(body) > MAX_MEDIA_BYTES:
        return f"response is {len(body)} bytes, over the {MAX_MEDIA_BYTES} byte cap"
    stripped = body.lstrip()
    if stripped.startswith((b"<", b"{", b"<!")):
        return "response body is a document, not a media file"
    if "video/" in ctype or ctype == "application/octet-stream" or b"ftyp" in body[:64]:
        return None
    return f"unrecognized media type {ctype or 'unknown'}"


def failure_reason(aweme_id: str, wall: bool, captcha: bool) -> str:
    share = share_page_url(aweme_id)
    if captcha:
        return (
            f"{share} showed a verification challenge and no playing <video> src. "
            "This helper does not solve captchas. No media file was saved. "
            "Do not use the share caption as Understanding."
        )
    if wall:
        return (
            f"{share} includes {WALL_TEXT} and no <video> src. "
            "iesdouyin share pages often show that wall; this attempt already used the "
            "mobile share page after visiting www.douyin.com. No media file was saved. "
            "Do not use the share caption as Understanding."
        )
    return (
        f"{share} did not expose a playing <video> src (no playwm URL). "
        "No media file was saved. Do not use the share caption as Understanding."
    )


def resolve_aweme_id(url: str, fetch=None) -> str:
    """Pull a numeric aweme id from a video URL, or from public redirects of a short link."""
    current = (url or "").strip()
    if not current:
        raise AcquireError("Missing Douyin URL. Pass --url or --aweme-id.")
    if not current.startswith(("http://", "https://")):
        current = "https://" + current
    found = aweme_id_from_text(current)
    if found:
        return found
    fetch = fetch or default_fetch
    seen: set[str] = set()
    for _ in range(8):
        if current in seen:
            break
        seen.add(current)
        host = (urllib.parse.urlparse(current).hostname or "").lower()
        if host not in RESOLVE_HOSTS:
            break
        _status, location, snippet = fetch(current)
        if location:
            current = urllib.parse.urljoin(current, location)
            found = aweme_id_from_text(current)
            if found:
                return found
            continue
        found = aweme_id_from_text(snippet or "")
        if found:
            return found
        break
    raise AcquireError(
        "Could not resolve a Douyin aweme id from the URL. "
        "Pass --aweme-id. Do not use the share caption as the video."
    )


def default_fetch(url: str) -> tuple[int, str | None, str]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": MOBILE_UA, "Accept": "text/html"},
    )

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=20) as response:
            location = response.headers.get("Location")
            snippet = response.read(8192).decode("utf-8", "replace")
            return response.status, location, snippet
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location") if exc.headers else None
        return exc.code, location, ""


def load_playwright():
    try:
        return importlib.import_module("playwright.sync_api")
    except ImportError as exc:
        raise AcquireError("playwright is not installed. " + INSTALL_HINT) from exc


def read_player_state(page) -> dict:
    """Video URLs plus wall/captcha flags. Page text itself is not returned."""
    page.wait_for_timeout(1000)
    try:
        page.wait_for_function(
            """() => {
                const videos = Array.from(document.querySelectorAll('video'));
                return videos.some(v => {
                    const source = v.querySelector('source');
                    const src = v.currentSrc || v.src || (source && source.src) || '';
                    return src.startsWith('https://');
                });
            }""",
            timeout=25000,
        )
    except Exception:
        # Timeout or missing video is a normal failed acquire, handled below.
        pass
    return page.evaluate(
        """() => {
            const text = document.body ? document.body.innerText : "";
            const videos = Array.from(document.querySelectorAll('video')).map(v => {
                const source = v.querySelector('source');
                return {
                    src: v.src || (source && source.src) || "",
                    currentSrc: v.currentSrc || ""
                };
            });
            const lowered = text.toLowerCase();
            return {
                videos: videos,
                wall: text.includes("请尝试在抖音内观看"),
                captcha: text.includes("验证码") || lowered.includes("captcha")
            };
        }"""
    )


def download_play_url(context, play_url: str, referer: str, dest: Path) -> dict:
    if not is_public_https(play_url):
        raise AcquireError("Refusing a video src that is not a public https URL.")
    response = context.request.get(
        play_url,
        headers={"Referer": referer},
        timeout=120_000,
        max_redirects=10,
    )
    status = response.status
    if status < 200 or status >= 300:
        raise AcquireError(
            f"playwm GET returned HTTP {status}. No media file was saved. "
            "Do not use the share caption as Understanding."
        )
    body = response.body()
    content_type = (response.headers or {}).get("content-type", "")
    problem = validate_media(body, content_type)
    if problem:
        raise AcquireError(
            problem + ". No media file was saved. Do not use the share caption as Understanding."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    return {
        "bytes": len(body),
        "content_type": content_type.split(";")[0].strip() or "video/mp4",
    }


def acquire_with_browser(aweme_id: str, dest: Path, playwright_module) -> dict:
    share = share_page_url(aweme_id)
    browser = None
    try:
        with playwright_module.sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=MOBILE_UA,
                viewport={"width": 390, "height": 844},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True,
                locale="zh-CN",
            )
            page = context.new_page()
            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=30_000)
            page.goto(share, wait_until="domcontentloaded", timeout=45_000)
            state = read_player_state(page)
            play_url = pick_video_src(state.get("videos") or [])
            if not play_url:
                raise AcquireError(failure_reason(
                    aweme_id, bool(state.get("wall")), bool(state.get("captcha")),
                ))
            saved = download_play_url(context, play_url, share, dest)
            browser.close()
            browser = None
    except AcquireError:
        raise
    except Exception as exc:
        name = type(exc).__name__
        message = str(exc)
        if "Executable doesn't exist" in message or "chromium" in message.lower():
            raise AcquireError("Playwright Chromium is not installed. " + INSTALL_HINT) from exc
        raise AcquireError(
            f"Douyin acquire failed ({name}). No media file was saved. "
            "Do not use the share caption as Understanding. " + INSTALL_HINT
        ) from exc
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
    return success_record(aweme_id, share, dest, saved["bytes"], saved["content_type"], play_url)


def media_dest(out_dir: str) -> Path:
    """Local mp4 path. One acquire writes video.mp4 inside --out-dir."""
    dest_dir = Path(out_dir).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    return dest_dir / "video.mp4"


def success_record(aweme_id: str, share: str, dest: Path, nbytes: int,
                   content_type: str, play_url: str) -> dict:
    path = str(dest)
    return {
        "ok": True,
        "path": path,
        "bytes": nbytes,
        "content_type": content_type,
        "aweme_id": aweme_id,
        "play_url": play_url,
        "acquired": True,
        "platform": "douyin",
        "share_url": share,
        "media_path": path,
        "fetch_method": "playwright_playwm",
        "caption_used_as_body": False,
        "error": None,
    }


def empty_record(url: str) -> dict:
    return {
        "ok": False,
        "path": None,
        "bytes": 0,
        "content_type": None,
        "aweme_id": None,
        "play_url": None,
        "acquired": False,
        "platform": "douyin",
        "share_url": None,
        "media_path": None,
        "fetch_method": "playwright_playwm",
        "caption_used_as_body": False,
        "source_url": url,
        "error": None,
    }


def acquire(url: str | None, aweme_id: str | None, out_dir: str, fetch=None,
            playwright_module=None) -> dict:
    aweme = aweme_id or resolve_aweme_id(url or "", fetch=fetch)
    dest = media_dest(out_dir)
    module = playwright_module if playwright_module is not None else load_playwright()
    record = acquire_with_browser(aweme, dest, module)
    record["source_url"] = url
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Save a Douyin video from the mobile share <video> play URL. "
                    "Does not read the share caption as the body.",
        epilog=INSTALL_HINT,
    )
    parser.add_argument("--url", default=None, help="Douyin share or video URL")
    parser.add_argument("--aweme-id", default=None, help="Numeric aweme id, if already known")
    parser.add_argument("--out-dir", default=".",
                        help="Directory for video.mp4 (default: current directory)")
    args = parser.parse_args(argv)
    record = empty_record(args.url or "")
    try:
        if not args.url and not args.aweme_id:
            raise AcquireError("Pass --url or --aweme-id.")
        record = acquire(args.url, args.aweme_id, args.out_dir)
    except AcquireError as exc:
        record["error"] = str(exc)
        if args.aweme_id and args.aweme_id.isdigit():
            record["aweme_id"] = args.aweme_id
            record["share_url"] = share_page_url(args.aweme_id)
    except Exception as exc:
        record["error"] = f"Douyin acquire failed ({type(exc).__name__}). " + INSTALL_HINT
    print(json.dumps(record, ensure_ascii=True))
    return 0 if record.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
