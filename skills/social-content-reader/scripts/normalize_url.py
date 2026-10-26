#!/usr/bin/env python3
"""URL normalizers for social-content-reader.

Legal, keyless helpers: extract canonical ids / URLs only.
No network I/O, no credentials.
"""

from __future__ import annotations

import argparse
import json
import re
from urllib.parse import parse_qs, urlparse


YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
X_STATUS_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:mobile\.)?(?:x|twitter)\.com/([^/]+)/status/(\d+)",
    re.I,
)
IG_RE = re.compile(
    r"(?:https?://)?(?:www\.)?instagram\.com/(p|reel|reels|tv)/([^/?#]+)",
    re.I,
)
WX_ARTICLE_RE = re.compile(r"(?:https?://)?mp\.weixin\.qq\.com/s/([A-Za-z0-9_-]+)", re.I)
TIKTOK_RE = re.compile(
    r"(?:https?://)?(?:www\.)?tiktok\.com/@([^/]+)/video/(\d+)",
    re.I,
)
TIKTOK_SHORT_RE = re.compile(
    r"(?:https?://)?(?:vm\.tiktok\.com|www\.tiktok\.com/t)/([A-Za-z0-9_]+)",
    re.I,
)
THREADS_RE = re.compile(
    r"(?:https?://)?(?:www\.)?threads\.(?:net|com)/@([^/]+)/post/([A-Za-z0-9_-]+)",
    re.I,
)
REDDIT_RE = re.compile(
    r"(?:https?://)?(?:www\.|old\.|new\.)?reddit\.com/r/([^/]+)/comments/([A-Za-z0-9]+)",
    re.I,
)
REDDIT_SHORT_RE = re.compile(r"(?:https?://)?redd\.it/([A-Za-z0-9]+)", re.I)
LINKEDIN_POST_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(posts|pulse)/([^/?#]+)",
    re.I,
)
LINKEDIN_ACTIVITY_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/feed/update/(urn:li:activity:\d+)",
    re.I,
)
FACEBOOK_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:facebook\.com|fb\.watch)/",
    re.I,
)
TELEGRAM_RE = re.compile(
    r"(?:https?://)?(?:www\.)?t\.me/(?:s/)?([A-Za-z0-9_]+)/(\d+)",
    re.I,
)
VIMEO_RE = re.compile(
    r"(?:https?://)?(?:www\.|player\.)?vimeo\.com/(?:video/)?(\d+)",
    re.I,
)
TWITCH_VOD_RE = re.compile(
    r"(?:https?://)?(?:www\.)?twitch\.tv/videos/(\d+)",
    re.I,
)
TWITCH_CLIP_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitch\.tv/[^/]+/clip/|clips\.twitch\.tv/)([A-Za-z0-9_-]+)",
    re.I,
)
DOUYIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?douyin\.com/video/(\d+)",
    re.I,
)
DOUYIN_SHORT_RE = re.compile(
    r"(?:https?://)?(?:v\.douyin\.com)/([A-Za-z0-9_]+)",
    re.I,
)
BILIBILI_BV_RE = re.compile(
    r"(?:https?://)?(?:www\.)?bilibili\.com/video/(BV[A-Za-z0-9]+)",
    re.I,
)
BILIBILI_AV_RE = re.compile(
    r"(?:https?://)?(?:www\.)?bilibili\.com/video/av(\d+)",
    re.I,
)
BILIBILI_SHORT_RE = re.compile(r"(?:https?://)?b23\.tv/([A-Za-z0-9]+)", re.I)
XHS_RE = re.compile(
    r"(?:https?://)?(?:www\.)?xiaohongshu\.com/(?:explore|discovery/item)/([A-Za-z0-9]+)",
    re.I,
)
XHS_SHORT_RE = re.compile(r"(?:https?://)?xhslink\.com/([A-Za-z0-9]+)", re.I)


def detect(url: str) -> dict:
    raw = (url or "").strip()
    if not raw:
        return {"platform": "unknown", "error": "empty_url"}

    if YOUTUBE_ID_RE.match(raw):
        return {
            "platform": "youtube",
            "canonical_id": raw,
            "canonical_url": f"https://www.youtube.com/watch?v={raw}",
        }

    yt = _youtube(raw)
    if yt:
        return yt

    m = X_STATUS_RE.search(raw)
    if m:
        user, sid = m.group(1), m.group(2)
        return {
            "platform": "x",
            "canonical_id": sid,
            "canonical_url": f"https://x.com/{user}/status/{sid}",
            "author_hint": user,
        }

    m = IG_RE.search(raw)
    if m:
        kind, code = m.group(1).lower(), m.group(2)
        if kind == "reels":
            kind = "reel"
        return {
            "platform": "instagram",
            "canonical_id": code,
            "kind": kind,
            "canonical_url": f"https://www.instagram.com/{kind}/{code}/",
        }

    m = TIKTOK_RE.search(raw)
    if m:
        user, vid = m.group(1), m.group(2)
        return {
            "platform": "tiktok",
            "canonical_id": vid,
            "author_hint": user,
            "canonical_url": f"https://www.tiktok.com/@{user}/video/{vid}",
        }
    m = TIKTOK_SHORT_RE.search(raw)
    if m:
        return {
            "platform": "tiktok",
            "canonical_id": m.group(1),
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "link_form": "short",
            "limits": ["resolve redirect to @user/video/{id}"],
        }

    m = THREADS_RE.search(raw)
    if m:
        user, pid = m.group(1), m.group(2)
        return {
            "platform": "threads",
            "canonical_id": pid,
            "author_hint": user,
            "canonical_url": f"https://www.threads.net/@{user}/post/{pid}",
        }

    m = REDDIT_RE.search(raw)
    if m:
        sub, pid = m.group(1), m.group(2)
        return {
            "platform": "reddit",
            "canonical_id": pid,
            "subreddit": sub,
            "canonical_url": f"https://www.reddit.com/r/{sub}/comments/{pid}/",
        }
    m = REDDIT_SHORT_RE.search(raw)
    if m:
        return {
            "platform": "reddit",
            "canonical_id": m.group(1),
            "canonical_url": f"https://redd.it/{m.group(1)}",
            "link_form": "short",
        }

    m = LINKEDIN_ACTIVITY_RE.search(raw)
    if m:
        urn = m.group(1)
        return {
            "platform": "linkedin",
            "canonical_id": urn,
            "canonical_url": f"https://www.linkedin.com/feed/update/{urn}",
            "kind": "activity",
        }
    m = LINKEDIN_POST_RE.search(raw)
    if m:
        kind, slug = m.group(1).lower(), m.group(2)
        return {
            "platform": "linkedin",
            "canonical_id": slug,
            "kind": kind,
            "canonical_url": f"https://www.linkedin.com/{kind}/{slug}",
        }

    m = TELEGRAM_RE.search(raw)
    if m:
        channel, mid = m.group(1), m.group(2)
        return {
            "platform": "telegram",
            "canonical_id": f"{channel}/{mid}",
            "channel": channel,
            "canonical_url": f"https://t.me/s/{channel}/{mid}",
            "limits": ["public channels only via t.me/s/ preview"],
        }

    m = VIMEO_RE.search(raw)
    if m:
        vid = m.group(1)
        return {
            "platform": "vimeo",
            "canonical_id": vid,
            "canonical_url": f"https://vimeo.com/{vid}",
        }

    m = TWITCH_VOD_RE.search(raw)
    if m:
        return {
            "platform": "twitch",
            "canonical_id": m.group(1),
            "kind": "vod",
            "canonical_url": f"https://www.twitch.tv/videos/{m.group(1)}",
        }
    m = TWITCH_CLIP_RE.search(raw)
    if m:
        return {
            "platform": "twitch",
            "canonical_id": m.group(1),
            "kind": "clip",
            "canonical_url": f"https://clips.twitch.tv/{m.group(1)}",
        }

    m = DOUYIN_RE.search(raw)
    if m:
        return {
            "platform": "douyin",
            "canonical_id": m.group(1),
            "canonical_url": f"https://www.douyin.com/video/{m.group(1)}",
        }
    m = DOUYIN_SHORT_RE.search(raw)
    if m:
        return {
            "platform": "douyin",
            "canonical_id": m.group(1),
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "link_form": "short",
            "limits": ["resolve redirect to douyin.com/video/{id}"],
        }

    m = BILIBILI_BV_RE.search(raw)
    if m:
        bvid = m.group(1)
        if not bvid.startswith("BV"):
            bvid = "BV" + bvid[2:] if bvid.lower().startswith("bv") else bvid
        # preserve original casing of BV id after match
        bvid = m.group(1)
        return {
            "platform": "bilibili",
            "canonical_id": bvid,
            "canonical_url": f"https://www.bilibili.com/video/{bvid}",
        }
    m = BILIBILI_AV_RE.search(raw)
    if m:
        return {
            "platform": "bilibili",
            "canonical_id": f"av{m.group(1)}",
            "canonical_url": f"https://www.bilibili.com/video/av{m.group(1)}",
        }
    m = BILIBILI_SHORT_RE.search(raw)
    if m:
        return {
            "platform": "bilibili",
            "canonical_id": m.group(1),
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "link_form": "short",
            "limits": ["resolve b23.tv redirect to BV id"],
        }

    m = XHS_RE.search(raw)
    if m:
        return {
            "platform": "xiaohongshu",
            "canonical_id": m.group(1),
            "canonical_url": f"https://www.xiaohongshu.com/explore/{m.group(1)}",
        }
    m = XHS_SHORT_RE.search(raw)
    if m:
        return {
            "platform": "xiaohongshu",
            "canonical_id": m.group(1),
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "link_form": "short",
            "limits": ["resolve xhslink.com redirect"],
        }

    m = WX_ARTICLE_RE.search(raw)
    if m:
        return {
            "platform": "wechat-article",
            "canonical_id": m.group(1),
            "canonical_url": f"https://mp.weixin.qq.com/s/{m.group(1)}",
            "link_form": "short",
        }

    parsed = urlparse(raw if "://" in raw else "https://" + raw)
    host = (parsed.hostname or "").lower()

    if FACEBOOK_RE.search(raw) or "facebook.com" in host or host == "fb.watch":
        return {
            "platform": "facebook",
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "limits": ["prefer Graph API or user paste; oEmbed varies"],
        }

    if "mp.weixin.qq.com" in host and parsed.path.startswith("/s"):
        qs = parse_qs(parsed.query)
        return {
            "platform": "wechat-article",
            "canonical_id": qs.get("sn", [None])[0],
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "link_form": "long",
            "limits": ["long __biz links often hit verification pages"],
        }
    if "channels.weixin.qq.com" in host or "视频号" in raw:
        return {
            "platform": "wechat-channels",
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "limits": ["no general public consumer fetch; use user media + ASR"],
        }
    if "tiktok.com" in host:
        return {
            "platform": "tiktok",
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "limits": ["could not extract video id; resolve short links"],
        }
    if "threads.net" in host or "threads.com" in host:
        return {
            "platform": "threads",
            "canonical_url": raw if "://" in raw else "https://" + raw,
        }
    if "linkedin.com" in host:
        return {
            "platform": "linkedin",
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "limits": ["often login-walled; prefer user paste"],
        }
    if "douyin.com" in host or "iesdouyin.com" in host:
        return {
            "platform": "douyin",
            "canonical_url": raw if "://" in raw else "https://" + raw,
        }
    if "xiaohongshu.com" in host or "xhslink.com" in host:
        return {
            "platform": "xiaohongshu",
            "canonical_url": raw if "://" in raw else "https://" + raw,
        }
    if "bilibili.com" in host or "b23.tv" in host:
        return {
            "platform": "bilibili",
            "canonical_url": raw if "://" in raw else "https://" + raw,
        }
    if "vimeo.com" in host:
        return {
            "platform": "vimeo",
            "canonical_url": raw if "://" in raw else "https://" + raw,
        }
    if "twitch.tv" in host or "clips.twitch.tv" in host:
        return {
            "platform": "twitch",
            "canonical_url": raw if "://" in raw else "https://" + raw,
        }
    if host in {"t.me", "telegram.me"}:
        return {
            "platform": "telegram",
            "canonical_url": raw if "://" in raw else "https://" + raw,
            "limits": ["invite links are not public"],
        }

    return {"platform": "unknown", "canonical_url": raw}


def _youtube(url: str) -> dict | None:
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower()
    if host in {"youtu.be"}:
        vid = parsed.path.strip("/").split("/")[0]
        if YOUTUBE_ID_RE.match(vid):
            return {
                "platform": "youtube",
                "canonical_id": vid,
                "canonical_url": f"https://www.youtube.com/watch?v={vid}",
            }
    if "youtube.com" in host:
        qs = parse_qs(parsed.query)
        if "v" in qs and YOUTUBE_ID_RE.match(qs["v"][0]):
            vid = qs["v"][0]
            return {
                "platform": "youtube",
                "canonical_id": vid,
                "canonical_url": f"https://www.youtube.com/watch?v={vid}",
            }
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            vid = parts[1]
            if YOUTUBE_ID_RE.match(vid):
                return {
                    "platform": "youtube",
                    "canonical_id": vid,
                    "canonical_url": f"https://www.youtube.com/watch?v={vid}",
                }
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalize social content URLs")
    ap.add_argument("url", help="URL or bare YouTube id")
    args = ap.parse_args()
    print(json.dumps(detect(args.url), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
