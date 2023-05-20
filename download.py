from __future__ import unicode_literals
import sys
import os
# import youtube_dl
import yt_dlp as youtube_dl

import utils
from utils import cfg

from datetime import datetime

url = 'https://youtu.be/ncjYz6RhYwk'
storage = cfg('storage')

def get_yt(url, target):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': target,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            # 'preferredquality': '192',
        }],
        # 'postprocessor_args': ['-threads', '4'], # - don't have any effect
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:

        r = ydl.extract_info(url)

        title = r.get('title', 'no title')
        desctiption = r.get('description', 'no desc')
        print(f'{target} <-- {title}')

        return title

    return None

def generate_fn(folder):
    # finds the last file and generated fn above that
    files = os.listdir(folder)

    # get list of filenames w/o ext
    fs = [os.path.splitext(os.path.basename(f))[0]  for f in files]

    if not fs:
        n = 0
    else:
        try:
            nums = [int(f) for f in fs]
        except ValueError as ex:
            print(f'[E] cannot convert one of filenames to number: {ex}')
            return None

        nums.sort()
        n = nums[-1]

    fn = f'{n+1:04}'

    return fn

def yaml_update(fname, title):
    # date = datetime.now().date()
    date = datetime.now()
    utils.cacheAdd(fname, title, date)

def download(url, folder):
    id = utils.cacheId()
    fname = f'{id:04}'
    target = os.path.join(folder, fname)

    title = get_yt(url, target)
    fname += '.mp3'

    if title is not None:
        yaml_update(fname, title)
    else:
        print('[E] the title is empty, seems a fatal download issue')

if __name__ == '__main__':
    argv = sys.argv
    if len(argv) > 1:
        url = argv[1]
    else:
        print('[E] you need to provide url to download')
        exit(1)

    utils.cacheLoad()
    download(url, storage)

    utils.cacheDump()
