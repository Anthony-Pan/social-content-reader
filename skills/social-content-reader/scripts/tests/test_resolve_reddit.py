"""Reddit post URL → hosted media. Offline fixtures; no network."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import acquire_media as a
import resolve_reddit as r

TOKEN = "SUPERSECRETTOKENVALUE"
POST = "https://www.reddit.com/r/aww/comments/90bu6w/heat_index_was_110_degrees_so_we_offered_him_a/"
DASH = "https://v.redd.it/gyh95hiqc0b11/DASHPlaylist.mpd"


def listing(post, comments=None):
    return [
        {"kind": "Listing", "data": {"children": [{"kind": "t3", "data": post}]}},
        {"kind": "Listing", "data": {"children": comments or []}},
    ]


def player(post_id, media_path, extra=""):
    return (
        f'<shreddit-player post-id="t3_{post_id}" '
        f'src="https://v.redd.it/{media_path}/HLSPlaylist.m3u8?a={TOKEN}&amp;f=hd" '
        f'poster="https://preview.redd.it/not-the-file.jpg" '
        f'caption-url="https://v.redd.it/{media_path}/wh_ben_en.vtt" '
        f'preview="https://v.redd.it/{media_path}/DASH_600_K"{extra}></shreddit-player>'
    )


class ParseTests(unittest.TestCase):
    def test_post_url_variants(self):
        samples = [
            POST,
            "https://old.reddit.com/r/aww/comments/90bu6w/",
            "https://www.reddit.com/r/aww/comments/90bu6w.json",
            "https://www.redditmedia.com/r/aww/comments/90bu6w/slug/",
            "https://www.reddit.com/r/aww/comments/90bu6w/slug/commentid/",
        ]
        for url in samples:
            with self.subTest(url=url):
                target = r.parse_reddit_target(url)
                self.assertEqual(target.post_id, "90bu6w")
                self.assertEqual(target.path, "/r/aww/comments/90bu6w")
                self.assertIsNone(target.redirect_url)

    def test_user_and_bare_and_short_forms(self):
        user = r.parse_reddit_target("https://www.reddit.com/u/creepyt0es/comments/nip71r/title")
        self.assertEqual(user.path, "/user/creepyt0es/comments/nip71r")
        bare = r.parse_reddit_target("https://www.reddit.com/comments/90bu6w")
        self.assertEqual(bare.path, "/comments/90bu6w")
        short = r.parse_reddit_target("https://redd.it/90bu6w")
        self.assertEqual(short.redirect_kind, "short-link")
        share = r.parse_reddit_target("https://www.reddit.com/r/aww/s/AbCd12")
        self.assertEqual(share.redirect_kind, "share")

    def test_reject_non_posts(self):
        for url in [
            "https://www.reddit.com/r/aww",
            "https://www.reddit.com/user/someone",
            "https://user:pass@www.reddit.com/r/aww/comments/90bu6w",
            "https://oauth.reddit.com/r/aww/comments/90bu6w",
            "https://v.redd.it/gyh95hiqc0b11",
        ]:
            with self.subTest(url=url), self.assertRaises(r.RedditResolveError):
                r.parse_reddit_target(url)


class ListingTests(unittest.TestCase):
    def test_post_video_ignores_comment_duplicate_secure_media_and_caption(self):
        post = {
            "id": "90bu6w",
            "title": "Heat index caption",
            "selftext": "not the body",
            "url": "https://v.redd.it/gyh95hiqc0b11",
            "media": {"reddit_video": {
                "dash_url": "https://v.redd.it/gyh95hiqc0b11/DASHPlaylist.mpd?source=fallback",
                "fallback_url": "https://v.redd.it/gyh95hiqc0b11/DASH_720.mp4",
            }},
            "secure_media": {"reddit_video": {
                "dash_url": "https://v.redd.it/gyh95hiqc0b11/DASHPlaylist.mpd",
            }},
        }
        comment = {"kind": "t1", "data": {
            "id": "c1",
            "body": "comment text",
            "media": {"reddit_video": {"dash_url": "https://v.redd.it/commentvideo00/DASHPlaylist.mpd"}},
        }}
        video = r.hosted_videos_from_listing(listing(post, [comment]), "90bu6w")
        self.assertEqual(video["dash_url"], DASH)
        self.assertEqual(video["media_id"], "gyh95hiqc0b11")
        self.assertEqual(video["kind"], "post")
        self.assertNotIn("selftext", video)
        self.assertNotIn("title", video)
        self.assertNotIn(TOKEN, json.dumps(video))

    def test_crosspost_parent_used_only_when_the_post_has_no_video(self):
        own = listing({
            "id": "zzzzzz",
            "media": {"reddit_video": {"dash_url": "https://v.redd.it/ownmedia000000/DASHPlaylist.mpd"}},
            "crosspost_parent_list": [{
                "media": {"reddit_video": {"dash_url": "https://v.redd.it/parentmedia000/DASHPlaylist.mpd"}},
            }],
        })
        self.assertEqual(r.hosted_videos_from_listing(own, "zzzzzz")["media_id"], "ownmedia000000")
        crossed = listing({
            "id": "zjjw82",
            "title": "Cringe",
            "selftext": "",
            "url": "https://www.reddit.com/r/dumbfuckers_club/comments/zjjw82/cringe/",
            "media": None,
            "crosspost_parent_list": [{
                "id": "parent",
                "url": "https://v.redd.it/a1oneun6pa5a1",
                "media": {"reddit_video": {"hls_url": "https://v.redd.it/a1oneun6pa5a1/HLSPlaylist.m3u8?a=1"}},
            }],
        })
        video = r.hosted_videos_from_listing(crossed, "zjjw82")
        self.assertEqual(video["media_id"], "a1oneun6pa5a1")
        self.assertEqual(video["kind"], "crosspost")
        self.assertNotIn("a=1", video["dash_url"])

    def test_gallery_one_video_and_refuse_two(self):
        one = listing({
            "id": "gal111",
            "url": "https://www.reddit.com/gallery/gal111",
            "gallery_data": {"items": [
                {"media_id": "img0001"},
                {"media_id": "vid0001"},
            ]},
            "media_metadata": {
                "img0001": {"e": "Image", "s": {"u": "https://i.redd.it/img0001.jpg"}},
                "vid0001": {"e": "RedditVideo", "dashUrl": "https://v.redd.it/galleryvideo00/DASHPlaylist.mpd"},
            },
        })
        video = r.hosted_videos_from_listing(one, "gal111")
        self.assertEqual(video["kind"], "gallery")
        self.assertEqual(video["media_id"], "galleryvideo00")
        two = listing({
            "id": "gal222",
            "media_metadata": {
                "vid0001": {"e": "RedditVideo", "dashUrl": "https://v.redd.it/galleryvideo00/DASHPlaylist.mpd"},
                "vid0002": {"e": "RedditVideo", "hlsUrl": "https://v.redd.it/galleryvideo02/HLSPlaylist.m3u8"},
            },
        })
        with self.assertRaises(r.RedditResolveError) as caught:
            r.hosted_videos_from_listing(two, "gal222")
        self.assertIn("refusing to choose one", str(caught.exception))
        self.assertIn("2 hosted videos", str(caught.exception))

    def test_image_and_offplatform_are_not_media(self):
        for url in ("https://i.redd.it/abc.jpg", "https://www.youtube.com/watch?v=jNQXAC9IVRw"):
            payload = listing({"id": "90bu6w", "title": "caption", "selftext": "BODY", "url": url})
            self.assertIsNone(r.hosted_videos_from_listing(payload, "90bu6w"))

    def test_missing_post_does_not_use_another_child(self):
        payload = listing({"id": "someoneelse", "url": "https://v.redd.it/gyh95hiqc0b11"})
        with self.assertRaises(r.RedditResolveError) as caught:
            r.hosted_videos_from_listing(payload, "90bu6w")
        self.assertIn("did not include the requested post", str(caught.exception))


class EmbedTests(unittest.TestCase):
    def test_matching_player_ignores_other_post_poster_and_caption(self):
        html = (
            '<div id="t3_90bu6w-embed-wrapper"></div>'
            + player("deadbeef", "otherid000000")
            + player("90bu6w", "gyh95hiqc0b11")
            + '<a href="https://www.reddit.com/r/aww/comments/90bu6w/">Heat index caption</a>'
        )
        video, saw = r.hosted_videos_from_embed(html, "90bu6w")
        self.assertTrue(saw)
        self.assertEqual(video["dash_url"], DASH)
        self.assertNotIn(TOKEN, video["dash_url"])
        self.assertNotIn("preview.redd.it", video["dash_url"])
        self.assertNotIn(".vtt", video["dash_url"])

    def test_crosspost_screenview_ignores_other_post(self):
        html = """
        <div id="t3_zjjw82-embed-wrapper"></div>
        <shreddit-screenview-data data="{&quot;post&quot;:{&quot;id&quot;:&quot;t3_other99&quot;,&quot;url&quot;:&quot;https://v.redd.it/shouldnotuse00&quot;}}"></shreddit-screenview-data>
        <shreddit-screenview-data data="{&quot;post&quot;:{&quot;id&quot;:&quot;t3_zjjw82&quot;,&quot;url&quot;:&quot;https://v.redd.it/a1oneun6pa5a1&quot;,&quot;type&quot;:&quot;crosspost&quot;}}"></shreddit-screenview-data>
        """
        video, saw = r.hosted_videos_from_embed(html, "zjjw82")
        self.assertTrue(saw)
        self.assertEqual(video["media_id"], "a1oneun6pa5a1")
        self.assertEqual(video["kind"], "crosspost")

    def test_player_wins_over_a_different_screenview_url(self):
        html = (
            player("90bu6w", "gyh95hiqc0b11")
            + '<shreddit-screenview-data data='
            + "'{\"post\":{\"id\":\"t3_90bu6w\",\"url\":\"https://v.redd.it/notthis0000000\"}}'"
            + "></shreddit-screenview-data>"
        )
        video, _saw = r.hosted_videos_from_embed(html, "90bu6w")
        self.assertEqual(video["media_id"], "gyh95hiqc0b11")

    def test_two_inline_videos_refuse_without_leaking_the_player_token(self):
        html = (
            '<div id="t3_wzqkxp-embed-wrapper"></div>'
            '<shreddit-player post-id="t3_wzqkxp" '
            f'src="https://v.redd.it/link/wzqkxp/asset/ln81tq2lyhk91/HLSPlaylist.m3u8?a={TOKEN}"></shreddit-player>'
            '<shreddit-player post-id="t3_wzqkxp" '
            f'src="https://v.redd.it/link/wzqkxp/asset/cpvjun0zyhk91/HLSPlaylist.m3u8?a={TOKEN}"></shreddit-player>'
        )
        with self.assertRaises(r.RedditResolveError) as caught:
            r.hosted_videos_from_embed(html, "wzqkxp")
        message = str(caught.exception)
        self.assertIn("refusing to choose one", message)
        self.assertNotIn(TOKEN, message)
        self.assertNotIn("HLSPlaylist", message)

    def test_asset_must_belong_to_this_post(self):
        html = (
            '<shreddit-player post-id="t3_wzqkxp" '
            'src="https://v.redd.it/link/someoneelse/asset/ln81tq2lyhk91/HLSPlaylist.m3u8"></shreddit-player>'
        )
        video, saw = r.hosted_videos_from_embed(html, "wzqkxp")
        self.assertTrue(saw)
        self.assertIsNone(video)


class ResolveFetchTests(unittest.TestCase):
    def test_blocked_json_uses_embed_and_not_a_caption(self):
        calls = []

        def fetch(url):
            calls.append(url)
            if url.endswith(".json?raw_json=1&limit=1"):
                body = b"<html><title>Blocked</title></html>"
                return 403, url, "text/html", body
            html = ('<div id="t3_90bu6w-embed-wrapper"></div>' + player("90bu6w", "gyh95hiqc0b11")).encode()
            return 200, url, "text/html", html

        video = r.resolve_reddit_post(POST, fetch=fetch)
        self.assertEqual(video["via"], "embed")
        self.assertEqual(video["dash_url"], DASH)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].startswith("https://www.reddit.com/r/aww/comments/90bu6w/.json"))
        self.assertEqual(calls[1], "https://embed.reddit.com/r/aww/comments/90bu6w/")
        self.assertNotIn(TOKEN, json.dumps(video))

    def test_json_success_does_not_fetch_embed(self):
        calls = []

        def fetch(url):
            calls.append(url)
            post = {"id": "90bu6w", "selftext": "NO", "title": "caption",
                    "media": {"reddit_video": {"dash_url": DASH}}}
            return 200, url, "application/json", json.dumps(listing(post)).encode()

        video = r.resolve_reddit_post("https://old.reddit.com/r/aww/comments/90bu6w/", fetch=fetch)
        self.assertEqual(video["via"], "json")
        self.assertEqual(video["dash_url"], DASH)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("selftext", video)

    def test_json_without_video_does_not_shop_the_embed(self):
        calls = []

        def fetch(url):
            calls.append(url)
            post = {"id": "90bu6w", "title": "caption", "selftext": "BODYTEXT",
                    "url": "https://i.redd.it/abc.jpg"}
            return 200, url, "application/json", json.dumps(listing(post)).encode()

        with self.assertRaises(r.RedditResolveError) as caught:
            r.resolve_reddit_post(POST, fetch=fetch)
        self.assertIn("caption is metadata only", str(caught.exception))
        self.assertNotIn("BODYTEXT", str(caught.exception))
        self.assertEqual(len(calls), 1)

    def test_quarantine_does_not_fall_through_or_opt_in(self):
        calls = []

        def fetch(url):
            calls.append(url)
            body = json.dumps({"error": 403, "reason": "quarantined"}).encode()
            return 403, url, "application/json", body

        with self.assertRaises(r.RedditResolveError) as caught:
            r.resolve_reddit_post(POST, fetch=fetch)
        self.assertIn("quarantined", str(caught.exception))
        self.assertIn("not using cookies", str(caught.exception))
        self.assertEqual(len(calls), 1)

    def test_short_link_block_does_not_invent_an_id(self):
        def fetch(url):
            return 403, url, "text/html", b"<title>Blocked</title>"

        with self.assertRaises(r.RedditResolveError) as caught:
            r.resolve_reddit_post("https://redd.it/90bu6w", fetch=fetch)
        self.assertIn("short-link redirect blocked", str(caught.exception))
        self.assertIn("cannot invent a media id", str(caught.exception))

    def test_share_redirect_then_json(self):
        def fetch(url):
            if "/s/" in url:
                return 200, "https://www.reddit.com/r/aww/comments/90bu6w/heat/", "text/html", b""
            post = {"id": "90bu6w", "url": "https://v.redd.it/gyh95hiqc0b11"}
            return 200, url, "application/json", json.dumps(listing(post)).encode()

        video = r.resolve_reddit_post("https://www.reddit.com/r/aww/s/AbCd12", fetch=fetch)
        self.assertEqual(video["media_id"], "gyh95hiqc0b11")
        self.assertEqual(video["via"], "json")

    def test_embed_shell_without_the_post_is_a_hard_failure(self):
        def fetch(url):
            if "json" in url:
                return 403, url, "text/html", b"<title>Blocked</title>"
            return 200, url, "text/html", b"<title>Reddit</title><link href='https://v.redd.it/'>"

        with self.assertRaises(r.RedditResolveError) as caught:
            r.resolve_reddit_post("https://www.reddit.com/comments/90bu6w", fetch=fetch)
        message = str(caught.exception)
        self.assertIn("did not include post 90bu6w", message)
        self.assertIn("cannot invent a media id", message)


class AcquireWiringTests(unittest.TestCase):
    def probe(self):
        return {"duration_sec": 13.7, "has_video": True, "has_audio": False, "codecs": ["h264"]}

    def test_post_url_downloads_the_resolved_dash_manifest(self):
        def fake_ytdlp(platform, url, work, max_bytes):
            path = work / "media.mp4"
            path.write_bytes(b"video")
            return path, "yt_dlp", None

        with tempfile.TemporaryDirectory() as d, \
             patch.object(a.shutil, "which", return_value="/bin/tool"), \
             patch.object(r, "fetch_public") as fetch, \
             patch.object(a, "acquire_ytdlp", side_effect=fake_ytdlp) as ytdlp, \
             patch.object(a, "probe", return_value=self.probe()):
            fetch.side_effect = AssertionError("network")
            with patch.object(r, "resolve_reddit_post", return_value={
                "dash_url": DASH, "media_id": "gyh95hiqc0b11", "post_id": "90bu6w",
                "kind": "post", "via": "embed",
            }) as resolve:
                result = a.acquire(POST, Path(d))
            resolve.assert_called_once()
            fetch.assert_not_called()
            self.assertEqual(ytdlp.call_args.args[1], DASH)
            self.assertTrue(result["ok"])
            self.assertEqual(result["method"], "reddit_post_embed")
            self.assertEqual(result["source_url"], POST)
            self.assertEqual(result["reddit_post_id"], "90bu6w")
            self.assertEqual(result["reddit_media_id"], "gyh95hiqc0b11")
            self.assertNotIn("body_text", result)
            self.assertNotIn(TOKEN, json.dumps(result))

    def test_direct_cdn_url_skips_the_post_resolver(self):
        def fake_ytdlp(platform, url, work, max_bytes):
            path = work / "media.mp4"
            path.write_bytes(b"video")
            return path, "yt_dlp", None

        with tempfile.TemporaryDirectory() as d, \
             patch.object(a.shutil, "which", return_value="/bin/tool"), \
             patch("resolve_reddit.resolve_reddit_post") as resolve, \
             patch.object(a, "acquire_ytdlp", side_effect=fake_ytdlp) as ytdlp, \
             patch.object(a, "probe", return_value=self.probe()):
            result = a.acquire("https://v.redd.it/gyh95hiqc0b11", Path(d))
        resolve.assert_not_called()
        self.assertEqual(ytdlp.call_args.args[1], DASH)
        self.assertEqual(result["method"], "yt_dlp")
        self.assertNotIn("reddit_post_id", result)
        self.assertNotIn("body_text", result)

    def test_resolver_failure_has_no_file_or_body(self):
        with tempfile.TemporaryDirectory() as d, \
             patch.object(a.shutil, "which", return_value="/bin/tool"), \
             patch("resolve_reddit.resolve_reddit_post",
                   side_effect=r.RedditResolveError(
                       "reddit post 90bu6w has no hosted v.redd.it media; caption is metadata only")):
            result = a.acquire(POST, Path(d))
            self.assertFalse(result["ok"])
            self.assertIn("caption is metadata only", result["error"])
            self.assertEqual(result["body_kind"], "unavailable")
            self.assertNotIn("body_text", result)
            self.assertNotIn("path", result)
            self.assertEqual(list(Path(d).iterdir()), [])


class RouteTests(unittest.TestCase):
    def test_direct_dash_and_post_urls(self):
        self.assertEqual(a.route("https://v.redd.it/gyh95hiqc0b11")[1], DASH)
        platform, url, ident = a.route(POST)
        self.assertEqual((platform, ident), ("reddit", ""))
        self.assertEqual(url, POST)
        self.assertEqual(a.route("https://redd.it/90bu6w")[0], "reddit")
        self.assertEqual(a.route("https://www.redditmedia.com/r/aww/comments/90bu6w/")[0], "reddit")


if __name__ == "__main__":
    unittest.main()
