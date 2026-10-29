#!/usr/bin/env python3
"""Acquire public social media or WeChat 公众号 article bodies.

Video platforms: success requires a local, ffprobe-validated file. Fresh
Playwright contexts only. No browser profiles, saved cookies, private API
clients, challenge solving, or decryption. Captions never become a media result.
WeChat 公众号 (mp.weixin.qq.com): delegates to fetch_wechat_article.py; article
body success does not require ffmpeg. Reddit post URLs resolve through the
public `.json` listing, then `embed.reddit.com` when that listing is blocked,
and download the post's own unsigned v.redd.it DASH manifest. See
platforms/_video-body.md, platforms/wechat-article.md, and platforms/reddit.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from acquire_twitch import TwitchError, acquire_public, classify_twitch


class AcquireError(Exception):
    pass


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class PageJSON(HTMLParser):
    """Read JSON already shipped in public HTML, never execute page scripts."""
    def __init__(self):
        super().__init__()
        self.active = False
        self.chunks = []
        self.values = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.active = dict(attrs).get("type") == "application/json"
            self.chunks = []

    def handle_data(self, data):
        if self.active:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.active:
            try:
                self.values.append(json.loads("".join(self.chunks)))
            except (ValueError, RecursionError):
                pass
            self.active = False


def page_media(html, platform, ident):
    """Match the requested post, excluding recommendations and quoted posts."""
    parser = PageJSON()
    parser.feed(html)
    urls = []
    for value in parser.values:
        for node in walk(value):
            if platform in ("instagram", "threads") and node.get("code") == ident:
                urls.extend(v["url"] for v in node.get("video_versions") or []
                            if isinstance(v, dict) and isinstance(v.get("url"), str))
            elif platform == "facebook" and str(node.get("id")) == ident:
                urls.extend(node[k] for k in ("browser_native_hd_url", "browser_native_sd_url")
                            if isinstance(node.get(k), str))
    return list(dict.fromkeys(urls))


def route(url):
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if p.scheme not in ("http", "https") or p.username or p.password:
        raise AcquireError("expected a public http(s) social URL")
    def domain(d):
        return host == d or host.endswith("." + d)
    path = p.path
    if domain("youtube.com") or domain("youtu.be"):
        return "youtube", url, ""
    if domain("tiktok.com"):
        m = re.search(r"/(?:video|player/v1)/(\d+)", path)
        if m:
            return "tiktok", f"https://www.tiktok.com/player/v1/{m[1]}?autoplay=1", m[1]
        raise AcquireError("resolve the TikTok short link to its public video URL first")
    if domain("bilibili.com"):
        m = re.search(r"BV[0-9A-Za-z]+", url)
        if not m:
            raise AcquireError("use the resolved Bilibili BV URL")
        part = parse_qs(p.query).get("p", ["1"])[0]
        if part != "1":
            raise AcquireError("Bilibili multipart acquisition is unverified; refusing to substitute part 1")
        return "bilibili", f"https://player.bilibili.com/player.html?bvid={m[0]}&autoplay=1", m[0]
    if domain("t.me"):
        m = re.fullmatch(r"/(?:s/)?([A-Za-z][A-Za-z0-9_]+)/(\d+)/?", path)
        if not m:
            raise AcquireError("only a public Telegram channel/message URL is supported")
        return "telegram", f"https://t.me/{m[1]}/{m[2]}?embed=1", f"{m[1]}/{m[2]}"
    if domain("instagram.com"):
        m = re.search(r"/(?:p|reel|reels|tv)/([\w-]+)", path)
        if not m:
            raise AcquireError("expected an Instagram post/Reel URL")
        return "instagram", f"https://www.instagram.com/reel/{m[1]}/", m[1]
    if domain("threads.com") or domain("threads.net"):
        m = re.search(r"/(?:post|t)/([\w-]+)", path)
        if not m:
            raise AcquireError("expected a Threads post URL")
        return "threads", f"https://www.threads.com/t/{m[1]}", m[1]
    if domain("facebook.com"):
        m = re.search(r"/(?:reel|videos)/(\d+)", path)
        ident = m[1] if m else parse_qs(p.query).get("v", [""])[0]
        if not ident.isdigit():
            raise AcquireError("use a resolved Facebook reel/videos/watch URL with video id")
        return "facebook", url, ident
    if domain("twitter.com") or domain("x.com"):
        if not re.search(r"/status/\d+", path):
            raise AcquireError("expected an X/Twitter status URL")
        return "x", url, ""
    if domain("vimeo.com"):
        m = re.fullmatch(r"/(?:video/)?(\d+)/?", path)
        if not m:
            raise AcquireError("use the public Vimeo video or player URL")
        # Preserve the owner's supplied unlisted access hash, never invent one.
        return "vimeo", f"https://player.vimeo.com/video/{m[1]}" + ("?" + p.query if p.query else ""), m[1]
    if host == "v.redd.it":
        m = re.fullmatch(r"/([a-z0-9]+)(?:/DASHPlaylist\.mpd)?/?", path)
        if not m:
            raise AcquireError("expected a public v.redd.it media id or DASHPlaylist.mpd URL")
        return "reddit", f"https://v.redd.it/{m[1]}/DASHPlaylist.mpd", m[1]
    if host in {"redd.it", "www.redd.it"}:
        return "reddit", url, ""
    if domain("twitch.tv"):
        try:
            info = classify_twitch(url)
        except TwitchError as exc:
            raise AcquireError(str(exc)) from exc
        return "twitch", info["canonical_url"], info["ident"]
    for d, platform in [("linkedin.com", "linkedin"),
                        ("xiaohongshu.com", "xiaohongshu"), ("xhslink.com", "xiaohongshu"),
                        ("reddit.com", "reddit"), ("redditmedia.com", "reddit"),
                        ("v.redd.it", "reddit"), ("douyin.com", "douyin")]:
        if domain(d):
            return platform, url, ""
    if domain("mp.weixin.qq.com"):
        return "wechat-article", url, ""
    if domain("weixin.qq.com"):
        return "wechat-channels", url, ""
    raise AcquireError("unsupported social URL host")


def probe(path, require_video=True, expected_duration=None):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                             "-of", "json", str(path)], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise AcquireError("download is not decodable media (ffprobe failed)")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    types = {s.get("codec_type") for s in streams}
    duration = float(data.get("format", {}).get("duration", 0))
    if not math.isfinite(duration) or duration <= 0 or (require_video and "video" not in types):
        raise AcquireError("file has no video stream or positive duration")
    if expected_duration and abs(duration - expected_duration) > max(2, expected_duration * .05):
        raise AcquireError("file duration differs from the requested player (possible partial/other video)")
    return {"duration_sec": duration, "has_video": "video" in types, "has_audio": "audio" in types,
            "codecs": [s.get("codec_name") for s in streams]}


def download(context, url, referer, path, max_bytes, headers=None):
    if not url.startswith("https://") or re.search(r"/(?:error|placeholder)\.mp4(?:\?|$)", url):
        raise AcquireError("missing public HTTPS media URL or known error placeholder")
    response = context.request.get(url, headers=headers or {"Referer": referer}, timeout=60000)
    try:
        if response.status not in (200, 206):
            raise AcquireError(f"media GET HTTP {response.status}; no complete file")
        if int(response.headers.get("content-length", 0)) > max_bytes:
            raise AcquireError("media exceeds --max-mb")
        if any(t in response.headers.get("content-type", "") for t in ("text/html", "application/json")):
            raise AcquireError("media GET returned a page, not a media file")
        data = response.body()
        if not data or len(data) > max_bytes:
            raise AcquireError("empty media or media exceeds --max-mb")
        if response.status == 206:
            bounds = re.fullmatch(r"bytes 0-(\d+)/(\d+)", response.headers.get("content-range", ""))
            if not bounds or int(bounds[1]) + 1 != int(bounds[2]) or len(data) != int(bounds[2]):
                raise AcquireError("incomplete HTTP range: not a complete media file")
        path.write_bytes(data)
    finally:
        response.dispose()


def acquire_browser(platform, url, ident, work, max_bytes, wait_seconds):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise AcquireError("install Playwright in a venv, then: playwright install chromium") from exc
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        try:
            context = browser.new_context()
            page = context.new_page()
            observed = []
            # External Bilibili player has one requested video. Observe its actual
            # media requests; no calls to a reverse-engineered player API.
            if platform == "bilibili":
                page.on("response", lambda r: observed.append(r)
                        if r.status in (200, 206) and ".m4s?" in r.url else None)
            response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            if response and response.status >= 400:
                raise AcquireError(f"public player HTTP {response.status}")
            page.wait_for_timeout(wait_seconds * 1000)
            if platform == "telegram":
                scope = page.locator(f'[data-post="{ident}"]')
                if scope.count() != 1:
                    raise AcquireError("requested Telegram message missing from public widget")
            else:
                scope = page
            videos = scope.locator("video").evaluate_all("""vs => vs.map(v => ({
                src: v.currentSrc || v.src, duration: Number.isFinite(v.duration) ? v.duration : null,
                sources: [...v.querySelectorAll('source')].map(s=>s.src),
                dataSources: v.getAttribute('data-sources')}))""")
            if any(v.get("src") and "/error.mp4" in v["src"] for v in videos):
                raise AcquireError("player returned error.mp4 placeholder, not requested video")
            if platform == "bilibili" and observed:
                parts = []
                seen = set()
                for i, response in enumerate(observed[:]):
                    if response.url in seen:
                        continue
                    seen.add(response.url)
                    # Match headers from this ordinary, successful playback.
                    # Request the entire unencrypted track, not just its index.
                    headers = {k: v for k, v in response.request.all_headers().items()
                               if k in ("origin", "referer", "user-agent", "accept", "accept-encoding")}
                    headers["range"] = "bytes=0-"
                    part = work / f"track-{i}.mp4"
                    download(context, response.url, page.url, part, max_bytes, headers=headers)
                    info = probe(part, require_video=False)
                    parts.append((part, info))
                    if any(x[1]["has_video"] for x in parts) and any(x[1]["has_audio"] for x in parts):
                        break
                video = next((x[0] for x in parts if x[1]["has_video"]), None)
                audio = next((x[0] for x in parts if x[1]["has_audio"]), None)
                if not video or not audio:
                    raise AcquireError("Bilibili player did not yield both video and audio tracks")
                target = work / "media.mp4"
                mux = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(video),
                                      "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
                                      str(target)], capture_output=True, timeout=120)
                if mux.returncode:
                    raise AcquireError("Bilibili video/audio mux failed")
                return target, "browser_media_tracks", videos[0].get("duration") if videos else None
            urls = []
            if platform in ("instagram", "facebook", "threads"):
                urls = page_media(page.content(), platform, ident)
            else:
                if platform != "telegram" and len(videos) > 1:
                    raise AcquireError("multiple videos: cannot establish requested media identity")
                for v in videos:
                    urls += [v["src"]] + v["sources"]
                    if v.get("dataSources"):
                        urls += [s["src"] for s in json.loads(v["dataSources"]) if s.get("src")]
            urls = list(dict.fromkeys(u for u in urls if u.startswith("https://")))
            if not urls:
                text = page.inner_text("body")
                if any(word in text for word in ("IP存在风险", "安全限制", "captcha", "Access Denied")):
                    raise AcquireError("public page presents an access/risk challenge; stopped")
                raise AcquireError("public page exposes no media for requested post; caption is metadata only")
            errors = []
            for media_url in urls[:4]:
                try:
                    target = work / "media.mp4"
                    download(context, media_url, page.url, target, max_bytes)
                    expected = videos[0].get("duration") if len(videos) == 1 else None
                    probe(target, expected_duration=expected)
                    return target, "public_page_media", expected
                except AcquireError as exc:
                    errors.append(str(exc))
            raise AcquireError("; ".join(errors))
        finally:
            browser.close()


def acquire_ytdlp(platform, url, work, max_bytes):
    if not shutil.which("yt-dlp"):
        raise AcquireError("yt-dlp is not installed")
    args = ["yt-dlp", "--ignore-config", "--no-playlist", "--no-progress", "--no-overwrites",
            "--retries", "0", "--fragment-retries", "0", "--socket-timeout", "20",
            "--max-filesize", str(max_bytes), "-f", "bv[height<=480]+ba/b/bv[height<=480]", "--merge-output-format", "mp4",
            "-o", str(work / "media.%(ext)s")]
    if platform == "x":
        args += ["--extractor-args", "twitter:api=syndication"]
    result = subprocess.run(args + [url], capture_output=True, text=True, timeout=240)
    if result.returncode:
        # Never emit signed URLs, cookies, or credentials from downloader output.
        text = result.stderr.lower()
        wall = next((w for w in ("drm", "login", "logged-in", "authentication", "403", "412", "unavailable")
                     if w in text), "downloader failure")
        raise AcquireError(f"yt-dlp: {wall}; no verified file (no cookie/profile fallback)")
    files = [p for p in work.glob("media.*") if p.suffix in (".mp4", ".mkv", ".webm")]
    if len(files) != 1:
        raise AcquireError("yt-dlp did not save exactly one media file (size limit or unavailable)")
    return files[0], "yt_dlp_syndication" if platform == "x" else "yt_dlp", None


def acquire(url, out_dir, max_mb=128, wait_seconds=8, section=None):
    platform = None
    try:
        platform, player, ident = route(url)
        out_dir = Path(out_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        # 公众号 articles: body can succeed without ffmpeg. Embedded media is optional.
        if platform == "wechat-article":
            from fetch_wechat_article import fetch_article
            result = fetch_article(player, out_dir=out_dir, try_embed_media=True)
            if not result.get("ok"):
                return {
                    "ok": False,
                    "platform": platform,
                    "source_url": url,
                    "error": result.get("error") or result.get("status") or "wechat article fetch failed",
                    "status": result.get("status"),
                    "body_kind": "unavailable",
                    "fetch_method": result.get("fetch_method") or "acquire_failed",
                }
            # Article body is the primary success. Attach optional embed media if present.
            payload = {
                "ok": True,
                "platform": platform,
                "source_url": url,
                "method": "wechat_article_https",
                "body_kind": "article",
                "fetch_method": result.get("fetch_method"),
                "title": result.get("title"),
                "author": result.get("author"),
                "body_text": result.get("body_text"),
                "body_chars": result.get("body_chars"),
                "embeds": result.get("embeds") or [],
                "embed_count": result.get("embed_count", 0),
                "receipt_path": result.get("receipt_path"),
            }
            media = result.get("embed_media")
            if isinstance(media, dict):
                payload["embed_media"] = media
                if media.get("ok") and media.get("path"):
                    payload["path"] = media["path"]
                    payload["bytes"] = media.get("bytes")
                    payload["sha256"] = media.get("sha256")
                    for k in ("duration_sec", "has_video", "has_audio", "codecs"):
                        if k in media:
                            payload[k] = media[k]
            return payload
        if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
            raise AcquireError("ffprobe and ffmpeg are required to verify acquired media")
        if section and platform != "twitch":
            raise AcquireError("--section is only supported for a Twitch clip or VOD URL")
        with tempfile.TemporaryDirectory(prefix=".acquire-", dir=out_dir) as temp:
            work = Path(temp)
            reddit_meta = None
            twitch_meta = None
            if platform == "reddit" and not ident:
                from resolve_reddit import RedditResolveError, resolve_reddit_post
                try:
                    reddit_meta = resolve_reddit_post(player)
                except RedditResolveError as exc:
                    raise AcquireError(str(exc)) from exc
                player = reddit_meta["dash_url"]
                ident = reddit_meta["media_id"]
            if platform in ("youtube", "vimeo", "x") or (platform == "reddit" and ident):
                path, method, expected = acquire_ytdlp(platform, player, work, max_mb * 1024**2)
                if reddit_meta:
                    method = "reddit_post_" + reddit_meta["via"]
            elif platform == "douyin":
                from acquire_douyin import acquire as douyin_acquire
                result = douyin_acquire(player, work)
                if not result.get("ok"):
                    raise AcquireError(result.get("error", "Douyin acquire failed"))
                path, method, expected = Path(result["path"]), "douyin_mobile_player", None
            elif platform == "twitch":
                try:
                    path, method, expected, twitch_meta = acquire_public(
                        url, work, max_mb * 1024**2, section)
                except TwitchError as exc:
                    raise AcquireError(str(exc)) from exc
            else:
                path, method, expected = acquire_browser(platform, player, ident, work, max_mb * 1024**2, wait_seconds)
            info = probe(path, expected_duration=expected)
            if path.stat().st_size > max_mb * 1024**2:
                raise AcquireError("media exceeds --max-mb")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            target = out_dir / f"{platform}_{digest[:16]}{path.suffix}"
            shutil.move(str(path), target)
            result = {"ok": True, "platform": platform, "source_url": url, "method": method,
                      "path": str(target), "bytes": target.stat().st_size, "sha256": digest, **info}
            if reddit_meta:
                result["reddit_post_id"] = reddit_meta["post_id"]
                result["reddit_media_id"] = reddit_meta["media_id"]
                result["reddit_kind"] = reddit_meta.get("kind") or "post"
            if twitch_meta:
                result.update(twitch_meta)
            (out_dir / (target.name + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            return result
    except Exception as exc:
        # Browser exception messages may include ephemeral signed media URLs.
        message = str(exc) if isinstance(exc, AcquireError) else f"{type(exc).__name__}: acquire failed; no validated file"
        if platform is None:
            host = (urlparse(url).hostname or "").lower()
            if host == "twitch.tv" or host.endswith(".twitch.tv"):
                platform = "twitch"
        return {"ok": False, "platform": platform, "source_url": url, "error": message,
                "body_kind": "unavailable", "fetch_method": "acquire_failed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--max-mb", type=int, default=128)
    parser.add_argument("--wait-seconds", type=int, default=8)
    parser.add_argument(
        "--section", default=None,
        help="Twitch only. START-END (seconds, MM:SS, H:MM:SS, or 1h2m3s). At most 600s. Not a silent prefix.",
    )
    args = parser.parse_args()
    if args.max_mb <= 0 or not 1 <= args.wait_seconds <= 60:
        parser.error("--max-mb must be positive; --wait-seconds must be 1..60")
    result = acquire(args.url, args.out_dir, args.max_mb, args.wait_seconds, args.section)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
