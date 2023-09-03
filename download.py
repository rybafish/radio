from __future__ import unicode_literals
import sys
import os
# import youtube_dl
import yt_dlp as youtube_dl

import utils
from utils import cfg

from datetime import datetime
from urllib.request import urlopen

import eyed3

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

        duration = r.get('duration')
        title = r.get('title', 'no title')
        desctiption = r.get('description', 'no desc')
        dur_str = utils.formatTime(duration, skipSeconds=True, skipMs=True)
        print(f'{target} <-- {title}, {dur_str}')

        return title

    return None

def isYoutube(url):
    """Detect if url is youtobe"""

    pref = url.find('//') + 2
    naked = url[pref:]

    if naked[:8] == 'youtu.be':
        return True

    if naked[:15] == 'www.youtube.com':
        return True

    return False



def get_mp3(url, target):
    """download mp3 file from mp3 and save it to target file"""

    print(f'need to download mp3: {url} and save to {target}')

    with urlopen(url) as file:
        print('Download started...', end='', flush=True)
        content = file.read()
        print('done')


    target += '.mp3'            # target is without extention

    with open(target, 'wb') as download:
        download.write(content)

    print('Saved')

    mp3 = eyed3.load(target)

    title = mp3.tag.title

    print('title:', title)

    return title

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

def yaml_update(fname, title, length):
    # date = datetime.now().date()
    date = datetime.now()
    utils.cacheAdd(fname, title, date, length)

def download(url, folder):
    id = utils.cacheId()
    fname = f'{id:04}'
    target = os.path.join(folder, fname)

    if isYoutube(url):
        title = get_yt(url, target)
    else:
        title = get_mp3(url, target)

    fname += '.mp3'

    try:
        st = os.stat(os.path.join(storage, fname))
        length = st.st_size
    except Exception as ex:
        print(f'[!] file length error: {ex}')
        return

    if title is not None:
        yaml_update(fname, title, length)
    else:
        print('[E] the title is empty, seems a fatal download issue')

if __name__ == '__main__':
    argv = sys.argv
    if len(argv) > 1:
        # url = argv[1]
        pass
    else:
        print('[E] you need to provide url to download')
        exit(1)

    utils.cacheLoad()

    for url in argv[1:]:
        download(url, storage)

    utils.cacheDump()
