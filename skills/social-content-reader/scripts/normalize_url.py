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


def detect(url: str) -> dict:
    raw = (url or "").strip()
    if not raw:
        return {"platform": "unknown", "error": "empty_url"}

    # bare YouTube id
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
            "limits": ["no general public consumer fetch"],
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
