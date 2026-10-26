"""Acquisition correctness: provenance, false successes, isolation, and failures."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import acquire_media as a


class RouteTests(unittest.TestCase):
    def test_documented_players(self):
        self.assertEqual(a.route('https://www.tiktok.com/@scout2015/video/6718335390845095173')[1],
                         'https://www.tiktok.com/player/v1/6718335390845095173?autoplay=1')
        self.assertEqual(a.route('https://www.bilibili.com/video/BV17x411w7KC')[2], 'BV17x411w7KC')
        self.assertEqual(a.route('https://t.me/s/telegram/402')[1], 'https://t.me/telegram/402?embed=1')
        self.assertEqual(a.route('https://www.threads.net/@nasa/post/ABC')[2], 'ABC')

    def test_host_confusion_private_invites_and_profiles_rejected(self):
        for url in ['https://tiktok.com.evil.test/@a/video/123', 'file:///etc/passwd',
                    'https://user:pass@tiktok.com/@a/video/123', 'https://t.me/+secret',
                    'https://t.me/c/123/456', 'https://instagram.com/someone']:
            with self.subTest(url=url), self.assertRaises(a.AcquireError):
                a.route(url)

    def test_unlisted_vimeo_hash_preserved(self):
        self.assertIn('?h=owner_supplied', a.route('https://player.vimeo.com/video/123?h=owner_supplied')[1])


class ProvenanceTests(unittest.TestCase):
    def html(self, data):
        return '<script type="application/json">' + json.dumps(data) + '</script>'

    def test_ig_exact_post_not_recommendation(self):
        data = {'posts': [{'code': 'other', 'video_versions': [{'url': 'https://wrong'}]},
                          {'code': 'target', 'video_versions': [{'url': 'https://right'}]}]}
        self.assertEqual(a.page_media(self.html(data), 'instagram', 'target'), ['https://right'])
        self.assertEqual(a.page_media(self.html(data), 'instagram', 'missing'), [])

    def test_facebook_exact_numeric_id(self):
        data = [{'id': '123', 'browser_native_sd_url': 'https://right'},
                {'id': '456', 'browser_native_hd_url': 'https://wrong'}]
        self.assertEqual(a.page_media(self.html(data), 'facebook', '123'), ['https://right'])

    def test_caption_and_thumbnail_never_become_media(self):
        self.assertEqual(a.page_media(self.html({'code': 'x', 'caption': 'a story',
                         'thumbnail': 'https://image'}), 'threads', 'x'), [])
        self.assertEqual(a.page_media('<script>throw new Error()</script>', 'instagram', 'x'), [])


class ValidationTests(unittest.TestCase):
    def ffprobe(self, types, duration='10'):
        return Mock(returncode=0, stdout=json.dumps({'streams': [{'codec_type': t} for t in types],
                                                    'format': {'duration': duration}}))

    def test_reject_audio_only_invalid_and_truncated(self):
        for result in [self.ffprobe(['audio']), self.ffprobe(['video'], '0'),
                       self.ffprobe(['video'], 'NaN'), Mock(returncode=1)]:
            with self.subTest(result=result), patch.object(a.subprocess, 'run', return_value=result), self.assertRaises(a.AcquireError):
                a.probe(Path('clip.mp4'))
        with patch.object(a.subprocess, 'run', return_value=self.ffprobe(['video'], '2')), self.assertRaises(a.AcquireError):
            a.probe(Path('clip.mp4'), expected_duration=100)

    def test_reject_placeholder_before_network(self):
        context = Mock()
        with self.assertRaises(a.AcquireError):
            a.download(context, 'https://s1.hdslb.com/bfs/static/player/media/error.mp4', 'https://player', Path('x'), 100)
        context.request.get.assert_not_called()

    def test_reject_http_error_html_and_partial_response(self):
        for status, ct in [(403, 'video/mp4'), (200, 'text/html'), (206, 'video/mp4')]:
            response = Mock(status=status, headers={'content-type': ct})
            response.body.return_value = b'partial'
            context = Mock();context.request.get.return_value = response
            with self.subTest(status=status, ct=ct), self.assertRaises(a.AcquireError):
                a.download(context, 'https://media.example/video.mp4', 'https://page', Path('x'), 100)
            response.dispose.assert_called_once()

    def test_accept_only_complete_range(self):
        context = Mock()
        response = Mock(status=206, headers={'content-type': 'video/mp4', 'content-range': 'bytes 0-3/4'})
        response.body.return_value = b'data';context.request.get.return_value = response
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'track.mp4'
            a.download(context, 'https://media.example/track.m4s', 'https://player', path, 100)
            self.assertEqual(path.read_bytes(), b'data')
            response.headers['content-range'] = 'bytes 0-3/50'
            with self.assertRaises(a.AcquireError):
                a.download(context, 'https://media.example/track.m4s', 'https://player', path, 100)

    def test_failure_has_no_success_path_or_body(self):
        with patch.object(a.shutil, 'which', return_value='/bin/tool'), \
             patch.object(a, 'acquire_browser', side_effect=a.AcquireError('login wall')), tempfile.TemporaryDirectory() as d:
            result = a.acquire('https://clips.twitch.tv/TestClip', Path(d))
            self.assertFalse(result['ok']);self.assertEqual(result['body_kind'], 'unavailable')
            self.assertNotIn('path', result);self.assertNotIn('body_text', result)
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_downloader_ignores_user_config_and_never_reads_cookies(self):
        with tempfile.TemporaryDirectory() as d:
            work = Path(d);(work/'media.mp4').write_bytes(b'data')
            with patch.object(a.shutil, 'which', return_value='/bin/yt-dlp'), \
                 patch.object(a.subprocess, 'run', return_value=Mock(returncode=0)) as run:
                a.acquire_ytdlp('x', 'https://x.com/a/status/123', work, 100)
                args = run.call_args.args[0]
                self.assertIn('--ignore-config', args)
                self.assertIn('twitter:api=syndication', args)
                self.assertFalse(any('cookies' in v or 'password' in v for v in args))


if __name__ == '__main__':
    unittest.main()
