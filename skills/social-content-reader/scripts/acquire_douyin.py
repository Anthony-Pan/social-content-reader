#!/usr/bin/env python3
"""Acquire a Douyin video file automatically (no user export).

Verified 2026-10-26 on macOS: homepage cookies → m.douyin.com/share/video/{id}
→ <video> playwm URL → CDN mp4. Re-downloaded aweme 7696098282904259850
from https://v.douyin.com/2qulGbSTiRI/ (~8MB).

On failure, body_snip is a short page excerpt for diagnosis. It is not
Understanding. Do not treat a share caption as the video.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_aweme_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if re.fullmatch(r"\d{15,}", s):
        return s
    m = re.search(r"/video/(\d+)", s)
    if m:
        return m.group(1)
    # short link resolved by Playwright navigation
    return ""


def acquire(url_or_id: str, out_dir: Path) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"ok": False, "error": "playwright not installed; pip install playwright && playwright install chromium"}

    out_dir.mkdir(parents=True, exist_ok=True)
    aweme_id = parse_aweme_id(url_or_id)
    start = url_or_id if url_or_id.startswith("http") else f"https://www.douyin.com/video/{aweme_id}"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        context = browser.new_context(
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 "
                "Mobile/15E148 Safari/604.1"
            ),
        )
        page = context.new_page()
        page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        if "v.douyin.com" in start or not aweme_id:
            page.goto(start, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(3000)
            m = re.search(r"/video/(\d+)", page.url)
            if m:
                aweme_id = m.group(1)

        if not aweme_id:
            browser.close()
            return {"ok": False, "error": "could not resolve aweme_id", "final_url": page.url}

        share = f"https://m.douyin.com/share/video/{aweme_id}"
        page.goto(share, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(5000)
        title = page.title()
        info = page.evaluate(
            """() => [...document.querySelectorAll('video')].map(v => ({
              src: v.src, currentSrc: v.currentSrc, poster: v.poster
            }))"""
        )
        play = None
        for v in info or []:
            play = v.get("currentSrc") or v.get("src")
            if play:
                break
        if not play:
            body = page.inner_text("body")[:300]
            browser.close()
            return {
                "ok": False,
                "error": "no video element / playwm on share page",
                "aweme_id": aweme_id,
                "title": title,
                "body_snip": body,
            }

        resp = page.request.get(
            play,
            max_redirects=10,
            headers={"Referer": share},
            timeout=60000,
        )
        data = resp.body()
        ct = resp.headers.get("content-type", "")
        browser.close()

        if resp.status != 200 or len(data) < 20000:
            return {
                "ok": False,
                "error": "media HTTP error or download too small",
                "aweme_id": aweme_id,
                "play_url": play,
                "bytes": len(data),
                "content_type": ct,
            }

        path = out_dir / f"douyin_{aweme_id}.mp4"
        pending = out_dir / f".douyin_{aweme_id}.part.mp4"
        pending.write_bytes(data)
        try:
            from acquire_media import probe
            media_info = probe(pending)
            pending.replace(path)
        except Exception:
            pending.unlink(missing_ok=True)
            return {"ok": False, "error": "download failed ffprobe video validation", "aweme_id": aweme_id}
        return {
            "ok": True,
            "path": str(path),
            "bytes": len(data),
            "content_type": ct,
            "aweme_id": aweme_id,
            "play_url": play,
            "title": title,
            "cdn_url": resp.url,
            **media_info,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url_or_id", help="Douyin share/video URL or aweme id")
    ap.add_argument("--out-dir", default=".", type=Path)
    args = ap.parse_args()
    try:
        result = acquire(args.url_or_id, args.out_dir)
    except Exception as exc:
        result = {"ok": False, "error": f"{type(exc).__name__}: Douyin acquire failed"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
