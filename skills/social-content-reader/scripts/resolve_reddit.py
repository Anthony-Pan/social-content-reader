#!/usr/bin/env python3
"""Resolve a public Reddit post URL to that post's hosted v.redd.it media.

Public paths only: the post's `.json` listing, then the public embed page
when the listing is blocked. No cookies, profiles, captcha solving, private
APIs, or IP rotation. A caption, oEmbed title, poster, or subtitle track is
never the media. Multiple hosted videos are refused rather than guessed.
The returned URL is an unsigned DASHPlaylist.mpd; signed player queries are
discarded.
"""
from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlsplit

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)
TIMEOUT = 25
MAX_BYTES = 4 * 1024 * 1024
POST_ID_RE = re.compile(r"^[a-z0-9]{3,12}$")
MEDIA_ID_RE = re.compile(r"^[a-z0-9]{5,32}$")
_BLOCKED_HOSTS = {"oauth", "accounts", "gateway", "ads", "api", "ads-api"}


class RedditResolveError(Exception):
    pass


class _Target:
    def __init__(self, post_id, path, redirect_url=None, redirect_kind=None):
        self.post_id = post_id
        self.path = path
        self.redirect_url = redirect_url
        self.redirect_kind = redirect_kind


def _host_ok(host):
    host = (host or "").lower().rstrip(".")
    if host in {"v.redd.it", "redd.it", "www.redd.it", "embed.reddit.com",
                "redditmedia.com", "www.redditmedia.com"}:
        return True
    if host == "reddit.com" or host.endswith(".reddit.com"):
        label = host.split(".")[0]
        return label not in _BLOCKED_HOSTS
    return False


def _split(url):
    try:
        parts = urlsplit(url.strip())
    except ValueError as exc:
        raise RedditResolveError("expected a public Reddit post URL") from exc
    if parts.scheme not in {"http", "https"} or parts.username or parts.password:
        raise RedditResolveError("expected a public http(s) Reddit post URL")
    if not _host_ok(parts.hostname):
        raise RedditResolveError("expected a public Reddit post URL")
    path = parts.path or "/"
    if path.endswith(".json"):
        path = path[:-5]
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return (parts.hostname or "").lower(), path


def parse_reddit_target(url):
    """Classify a post URL. Does not fetch. v.redd.it media URLs are not posts."""
    host, path = _split(url)
    if host == "v.redd.it":
        raise RedditResolveError("v.redd.it media URL is already a direct DASH path")

    if host in {"redd.it", "www.redd.it"}:
        m = re.fullmatch(r"/([A-Za-z0-9]{3,12})", path)
        if not m or not POST_ID_RE.fullmatch(m[1].lower()):
            raise RedditResolveError(
                "expected a Reddit post URL (/comments/{id}) or a v.redd.it media URL")
        return _Target(m[1].lower(), None, f"https://redd.it/{m[1].lower()}", "short-link")

    m = re.fullmatch(r"/r/([A-Za-z0-9_]{2,30})/s/([A-Za-z0-9]+)", path)
    if m:
        return _Target(None, None, f"https://www.reddit.com/r/{m[1]}/s/{m[2]}", "share")

    m = re.fullmatch(r"/gallery/([A-Za-z0-9]{3,12})", path)
    if m and POST_ID_RE.fullmatch(m[1].lower()):
        return _Target(m[1].lower(), None, f"https://www.reddit.com/gallery/{m[1].lower()}", "gallery")

    m = re.match(r"^/(?:r/([A-Za-z0-9_]{2,30})|(?:user|u)/([A-Za-z0-9_-]{2,30}))/comments/([A-Za-z0-9]{3,12})(?:/|$)", path)
    user = None
    sub = None
    if m:
        sub, user, post_id = m[1], m[2], m[3].lower()
    else:
        bare = re.match(r"^/comments/([A-Za-z0-9]{3,12})(?:/|$)", path)
        if not bare:
            raise RedditResolveError(
                "expected a Reddit post URL (/comments/{id}) or a v.redd.it media URL")
        post_id = bare[1].lower()
    if not POST_ID_RE.fullmatch(post_id):
        raise RedditResolveError(
            "expected a Reddit post URL (/comments/{id}) or a v.redd.it media URL")
    if user:
        prefix = f"/user/{user}"
    elif sub:
        prefix = f"/r/{sub}"
    else:
        prefix = ""
    return _Target(post_id, f"{prefix}/comments/{post_id}")


def canonical_dash(url, post_id):
    """Map a public v.redd.it URL to an unsigned DASH playlist, or return None.

    Signed HLS/MP4 queries are dropped. Preview images, captions, and other
    hosts are ignored. Inline /link/{post}/asset/{id} paths must name this post.
    """
    if not isinstance(url, str) or not url:
        return None
    raw = html.unescape(url).strip()
    try:
        parts = urlsplit(raw)
    except ValueError:
        return None
    if parts.scheme != "https" or (parts.hostname or "").lower() != "v.redd.it":
        return None
    segs = [seg for seg in parts.path.split("/") if seg]
    if len(segs) >= 4 and segs[0].lower() == "link" and segs[2].lower() == "asset":
        link_post, asset = segs[1].lower(), segs[3].lower()
        if link_post != post_id.lower() or not MEDIA_ID_RE.fullmatch(asset):
            return None
        return {
            "media_id": asset,
            "dash_url": f"https://v.redd.it/link/{link_post}/asset/{asset}/DASHPlaylist.mpd",
            "kind": "asset",
        }
    if not segs:
        return None
    media_id = segs[0].lower()
    if media_id == "link" or not MEDIA_ID_RE.fullmatch(media_id):
        return None
    return {
        "media_id": media_id,
        "dash_url": f"https://v.redd.it/{media_id}/DASHPlaylist.mpd",
        "kind": "post",
    }


def _select_one(videos, post_id):
    chosen = []
    seen = set()
    for video in videos:
        if video["dash_url"] in seen:
            continue
        seen.add(video["dash_url"])
        chosen.append(video)
    if len(chosen) > 1:
        ids = ", ".join(sorted(video["media_id"] for video in chosen))
        raise RedditResolveError(
            f"reddit post {post_id} exposes {len(chosen)} hosted videos ({ids}); refusing to choose one")
    return chosen[0] if chosen else None


def _add(videos, url, post_id, kind):
    item = canonical_dash(url, post_id)
    if not item:
        return
    if kind:
        item["kind"] = kind
    item["post_id"] = post_id.lower()
    videos.append(item)


def _reddit_video_urls(node):
    if not isinstance(node, dict):
        return []
    video = node.get("reddit_video")
    if not isinstance(video, dict):
        video = node.get("reddit_video_preview") if isinstance(node.get("reddit_video_preview"), dict) else None
    if not isinstance(video, dict):
        return []
    return [video.get("dash_url"), video.get("hls_url"), video.get("fallback_url")]


def hosted_videos_from_listing(payload, post_id):
    """Return the requested t3's hosted video from a public listing.

    Only listing[0] is read. Comment media is ignored. Raises when the post
    is present but has several hosted videos, or when the post is absent.
    Returns None when the post is present and has no hosted video.
    """
    post_id = post_id.lower()
    listing = payload[0] if isinstance(payload, list) and payload else payload
    if not isinstance(listing, dict):
        raise RedditResolveError("public listing did not include the requested post")
    children = (listing.get("data") or {}).get("children") if isinstance(listing.get("data"), dict) else None
    post = None
    for child in children or []:
        if not isinstance(child, dict) or child.get("kind") != "t3":
            continue
        data = child.get("data")
        if isinstance(data, dict) and str(data.get("id", "")).lower() == post_id:
            post = data
            break
    if post is None:
        raise RedditResolveError("public listing did not include the requested post")

    videos = []
    for key in ("media", "secure_media"):
        for url in _reddit_video_urls(post.get(key)):
            _add(videos, url, post_id, "post")
    if not videos and isinstance(post.get("url"), str):
        kind = "crosspost" if post.get("crosspost_parent_list") else "post"
        _add(videos, post.get("url"), post_id, kind)
    if not videos:
        for parent in post.get("crosspost_parent_list") or []:
            if not isinstance(parent, dict):
                continue
            for key in ("media", "secure_media"):
                for url in _reddit_video_urls(parent.get(key)):
                    _add(videos, url, post_id, "crosspost")
            _add(videos, parent.get("url"), post_id, "crosspost")
    if not videos:
        meta = post.get("media_metadata") if isinstance(post.get("media_metadata"), dict) else {}
        items = (post.get("gallery_data") or {}).get("items") if isinstance(post.get("gallery_data"), dict) else None
        order = []
        if isinstance(items, list) and items:
            for item in items:
                if isinstance(item, dict) and item.get("media_id"):
                    order.append(str(item["media_id"]))
        else:
            order = list(meta.keys())
        for media_key in order:
            item = meta.get(media_key)
            if not isinstance(item, dict) or item.get("e") == "Image":
                continue
            for url in _reddit_video_urls(item):
                _add(videos, url, post_id, "gallery")
            _add(videos, item.get("dashUrl") or item.get("hlsUrl"), post_id, "gallery")
    if not videos:
        preview = post.get("preview") if isinstance(post.get("preview"), dict) else {}
        for url in _reddit_video_urls(preview):
            _add(videos, url, post_id, "preview")
        nested = preview.get("reddit_video_preview")
        if isinstance(nested, dict):
            for url in (nested.get("dash_url"), nested.get("hls_url"), nested.get("fallback_url")):
                _add(videos, url, post_id, "preview")
    return _select_one(videos, post_id)


class _EmbedHTML(HTMLParser):
    def __init__(self, post_id):
        super().__init__(convert_charrefs=True)
        self.post_id = post_id.lower()
        self.players = []
        self.screenviews = []
        self.saw_post = False

    def handle_starttag(self, tag, attrs):
        ad = {key.lower(): value for key, value in attrs}
        ident = ad.get("id") or ""
        if ident.lower().startswith(f"t3_{self.post_id}"):
            self.saw_post = True
        if tag == "shreddit-player":
            self.players.append(ad)
            if _same_post(ad.get("post-id"), self.post_id):
                self.saw_post = True
        elif tag == "shreddit-screenview-data" and ad.get("data"):
            self.screenviews.append(ad["data"])


def _same_post(value, post_id):
    value = (value or "").strip().lower()
    if value.startswith("t3_"):
        value = value[3:]
    return value == post_id.lower()


def hosted_videos_from_embed(html_text, post_id):
    """Read hosted media for this post from a public embed page.

    Uses shreddit-player src for this t3 id, else that post's screenview URL
    (crossposts often have no player). Other posts on the page are ignored.
    Returns (video or None, saw_post).
    """
    post_id = post_id.lower()
    parser = _EmbedHTML(post_id)
    try:
        parser.feed(html_text)
        parser.close()
    except RedditResolveError:
        raise
    except Exception as exc:
        raise RedditResolveError("public embed could not be read") from exc

    videos = []
    matched_player = False
    for player in parser.players:
        if not _same_post(player.get("post-id"), post_id):
            continue
        matched_player = True
        # src only: poster, preview, and caption-url are not the file.
        _add(videos, player.get("src"), post_id, "asset" if "/asset/" in (player.get("src") or "") else "post")
    if matched_player:
        return _select_one(videos, post_id), True

    for blob in parser.screenviews:
        try:
            data = json.loads(blob)
        except (ValueError, TypeError):
            continue
        post = data.get("post") if isinstance(data, dict) else None
        if not isinstance(post, dict) or not _same_post(post.get("id"), post_id):
            continue
        parser.saw_post = True
        kind = "crosspost" if post.get("type") == "crosspost" else "post"
        _add(videos, post.get("url"), post_id, kind)
    return _select_one(videos, post_id), parser.saw_post


def _reason_block(body):
    if not body:
        return None
    stripped = body.lstrip()
    if not stripped.startswith((b"{", b"[")):
        return None
    try:
        payload = json.loads(stripped.decode("utf-8", "replace"))
    except (ValueError, UnicodeError):
        return None
    if isinstance(payload, dict):
        reason = str(payload.get("reason") or "")
        if reason in {"quarantined", "private", "gated"}:
            return reason
    return None


def _parse_json(body):
    stripped = body.lstrip()
    if not stripped.startswith((b"{", b"[")):
        return None
    try:
        return json.loads(stripped.decode("utf-8", "replace"))
    except (ValueError, UnicodeError):
        return None


class _GuardRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        host = (urlsplit(newurl).hostname or "").lower()
        if not _host_ok(host):
            raise RedditResolveError("reddit redirect left public reddit hosts")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header("Cookie")
        return redirected


def fetch_public(url):
    """GET one public URL. No cookie jar and no credential headers."""
    if not _host_ok(urlsplit(url).hostname):
        raise RedditResolveError("refusing non-reddit URL")
    opener = urllib.request.build_opener(_GuardRedirect)
    request = urllib.request.Request(url, headers={
        "User-Agent": CHROME_UA,
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            status = getattr(response, "status", 200)
            final = response.geturl()
            ctype = response.headers.get("content-type", "")
            body = response.read(MAX_BYTES + 1)
    except RedditResolveError:
        raise
    except urllib.error.HTTPError as exc:
        status = exc.code
        final = exc.geturl() if hasattr(exc, "geturl") else url
        ctype = exc.headers.get("content-type", "") if exc.headers else ""
        body = exc.read(MAX_BYTES + 1)
    except urllib.error.URLError as exc:
        raise RedditResolveError("reddit public fetch failed; no media id invented") from exc
    if not _host_ok(urlsplit(final).hostname):
        raise RedditResolveError("reddit redirect left public reddit hosts")
    if len(body) > MAX_BYTES:
        body = body[:MAX_BYTES]
    return status, final, ctype, body


def _blocked_status(status):
    return status >= 400


def resolve_reddit_post(url, fetch=None):
    """Resolve a post URL to one unsigned DASH playlist for that post's media.

    `fetch` is optional `(url) -> (status, final_url, content_type, body)` for tests.
    """
    fetch = fetch or fetch_public
    target = parse_reddit_target(url)
    if target.redirect_url:
        status, final, _ctype, body = fetch(target.redirect_url)
        reason = _reason_block(body)
        if reason:
            raise RedditResolveError(f"reddit post is {reason}; not using cookies to opt in")
        if _blocked_status(status):
            raise RedditResolveError(
                f"reddit {target.redirect_kind} redirect blocked (HTTP {status}); cannot invent a media id")
        try:
            landed = parse_reddit_target(final)
        except RedditResolveError as exc:
            raise RedditResolveError(
                f"reddit {target.redirect_kind} redirect did not reach a post URL") from exc
        if landed.redirect_url or not landed.post_id or not landed.path:
            raise RedditResolveError(
                f"reddit {target.redirect_kind} redirect did not reach a post URL")
        target = landed

    json_url = f"https://www.reddit.com{target.path}/.json?raw_json=1&limit=1"
    status, _final, _ctype, body = fetch(json_url)
    reason = _reason_block(body)
    if reason:
        raise RedditResolveError(f"reddit post is {reason}; not using cookies to opt in")
    if not _blocked_status(status):
        payload = _parse_json(body)
        if payload is not None:
            if isinstance(payload, dict) and payload.get("error") and "data" not in payload:
                raise RedditResolveError(
                    "reddit listing refused the post; not using cookies to opt in")
            video = hosted_videos_from_listing(payload, target.post_id)
            if video is None:
                raise RedditResolveError(
                    f"reddit post {target.post_id} has no hosted v.redd.it media; caption is metadata only")
            video["via"] = "json"
            video["post_id"] = target.post_id
            return video

    embed_url = f"https://embed.reddit.com{target.path}/"
    status, _final, _ctype, body = fetch(embed_url)
    if _blocked_status(status):
        raise RedditResolveError(
            "reddit post page and public embed blocked (HTTP "
            f"{status}); cannot invent a media id")
    try:
        html_text = body.decode("utf-8", "replace")
    except Exception as exc:
        raise RedditResolveError("public embed could not be read") from exc
    video, saw_post = hosted_videos_from_embed(html_text, target.post_id)
    if video is None:
        if saw_post:
            raise RedditResolveError(
                f"reddit post {target.post_id} has no hosted v.redd.it media; caption is metadata only")
        raise RedditResolveError(
            f"public embed did not include post {target.post_id}; listing JSON was blocked; cannot invent a media id")
    video["via"] = "embed"
    video["post_id"] = target.post_id
    return video


__all__ = [
    "RedditResolveError",
    "canonical_dash",
    "hosted_videos_from_embed",
    "hosted_videos_from_listing",
    "parse_reddit_target",
    "resolve_reddit_post",
]
