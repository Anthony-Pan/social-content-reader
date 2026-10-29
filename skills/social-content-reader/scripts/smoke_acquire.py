#!/usr/bin/env python3
"""Explicit opt-in live sample acquisition; never runs in the unit suite.

Use --platform NAME or --all. Writes PASS.json or FAIL.txt under --proof-dir.
These samples test public paths, not general access or media Understanding.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

SAMPLES = {
    'youtube': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
    'x': 'https://x.com/oshtru/status/1577855540407197696',
    'instagram': 'https://www.instagram.com/reel/Chunk8-jurw/',
    'tiktok': 'https://www.tiktok.com/@scout2015/video/6718335390845095173',
    'threads': 'https://www.threads.com/@nasa/post/DeMqtuYgkaL',
    # Post URL, not a pre-known CDN id. Direct v.redd.it URLs still work.
    'reddit': 'https://www.reddit.com/r/aww/comments/90bu6w/heat_index_was_110_degrees_so_we_offered_him_a/',
    'linkedin': 'https://www.linkedin.com/posts/the-mathworks_2_what-is-mathworks-cloud-center-activity-7151241570371948544-4Gu7',
    'facebook': 'https://www.facebook.com/reel/1195289147628387',
    'telegram': 'https://t.me/telegram/402',
    'vimeo': 'https://vimeo.com/22439234',
    'twitch': 'https://clips.twitch.tv/FaintLightGullWholeWheat',
    'douyin': 'https://www.douyin.com/video/7696098282904259850',
    'bilibili': 'https://www.bilibili.com/video/BV17x411w7KC',
    'xiaohongshu': 'https://www.xiaohongshu.com/explore/6411cf99000000001300b6d9',
    'wechat-channels': 'https://weixin.qq.com/sph/AAZ3p39sQm',
    # Video probe only; article-body fetching follows platforms/wechat-article.md.
    'wechat-article': 'https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--platform', choices=SAMPLES)
    group.add_argument('--all', action='store_true')
    ap.add_argument('--proof-dir', type=Path, required=True)
    args = ap.parse_args()
    records = []
    for name in SAMPLES if args.all else [args.platform]:
        folder = args.proof_dir.expanduser().resolve() / name
        folder.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, '-B', str(Path(__file__).with_name('acquire_media.py')),
                   SAMPLES[name], '--out-dir', str(folder)]
        try:
            run = subprocess.run(command, capture_output=True, text=True, timeout=360)
            result = json.loads(run.stdout)
        except (subprocess.TimeoutExpired, ValueError) as exc:
            result = {'ok': False, 'platform': name, 'source_url': SAMPLES[name],
                      'error': f'{type(exc).__name__}: no validated result'}
        if name == 'reddit':
            result['limits'] = [
                'Post URL; www/old listing JSON may be blocked and the public embed used instead',
                'A saved file is not Understanding. redd.it short links stay blocked when that redirect is HTTP 403',
            ]
        if name == 'wechat-article':
            result['limits'] = ['Embedded video probe only; no article-body success claimed']
        (folder/'attempt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        if result.get('ok'):
            (folder/'PASS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
            (folder/'FAIL.txt').unlink(missing_ok=True)
        else:
            (folder/'FAIL.txt').write_text(SAMPLES[name]+'\n'+result.get('error', 'unknown failure')+'\nVideo not watched; caption is metadata.\n')
            (folder/'PASS.json').unlink(missing_ok=True)
        records.append(result)
        print(name + ': ' + ('PASS' if result.get('ok') else 'FAIL'), flush=True)
    (args.proof_dir.expanduser().resolve()/'latest-run.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n')
    return 0 if all(r.get('ok') for r in records) else 1


if __name__ == '__main__':
    sys.exit(main())
