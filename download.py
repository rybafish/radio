from __future__ import unicode_literals
import sys
import os
# import youtube_dl
import yt_dlp as youtube_dl

import utils
from utils import cfg
from utils import log

from datetime import datetime
from urllib.request import urlopen

import eyed3

url = 'https://youtu.be/ncjYz6RhYwk'
storage = cfg('storage')

class myLogger:
    def debug(self, msg):
        log(f'[D]: {msg}')
    def warning(self, msg):
        log(f'[W]: {msg}')
    def error(self, msg):
        log(f'[E]: {msg}')

def get_yt(url, target):
    
    if cfg('forse_mp3', False) == False:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]',
            'nocolor': True,
            'logger': myLogger(),
            'outtmpl': target
        }

    if cfg('forse_mp3', False):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': target,
            'nocolor': True,
            'logger': myLogger(),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                # 'preferredquality': '192',
            }],
            # 'postprocessor_args': ['-threads', '4'], # - don't have any effect
        }
        
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:

        r = ydl.extract_info(url)
        r = ydl.extract_info(url)

        duration = r.get('duration')
        title = r.get('title', 'no title')
        desctiption = r.get('description', 'no desc')
        dur_str = utils.formatTime(duration, skipSeconds=True, skipMs=True)
        log(f'{target} <-- {title}, {dur_str}')

        return title, dur_str

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

    log(f'need to download mp3: {url} and save to {target}')

    with urlopen(url) as file:
        log('Download started...', end='', flush=True)
        content = file.read()
        log('done')


    target += '.mp3'            # target is without extention

    with open(target, 'wb') as download:
        download.write(content)

    log('Saved')

    mp3 = eyed3.load(target)

    title = mp3.tag.title

    log('title:', title)

    return title, None

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
            log(f'[E] cannot convert one of filenames to number: {ex}')
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
    '''
        long time sync processing
    '''
    
    log(f'url: {url}')
    log(f'folder: {folder}')
    
    id = utils.cacheId()
    fname = f'{id:04}'
    target = os.path.join(folder, fname)

    if isYoutube(url):
        if cfg('forse_mp3', False) == False:
            title, dur = get_yt(url, target+'.m4a')
            fname += '.m4a'
        else:
            title, dur = get_yt(url, target) # extention will be added by recoder I guess
            fname += '.mp3'
    else:
        title, dur = get_mp3(url, target)
        fname += '.mp3'

    try:
        st = os.stat(os.path.join(storage, fname))
        length = st.st_size
    except Exception as ex:
        log(f'[!] file length error: {ex}')
        return

    if title is not None:
        yaml_update(fname, title, length)
        lenmb = f'{round(length/1024/1024, 1):.1f}MB'
        return f'got it: {title} [{dur}], {lenmb}'
    else:
        log('[E] the title is empty, seems a fatal download issue')
        return '[E] check logs...'

if __name__ == '__main__':
    argv = sys.argv
    if len(argv) > 1:
        # url = argv[1]
        pass
    else:
        log('[E] you need to provide url to download')
        exit(1)

    utils.cacheLoad()

    for url in argv[1:]:
        download(url, storage)

    utils.cacheDump()
