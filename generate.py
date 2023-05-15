import os
from feedgen.feed import FeedGenerator
import utils
from datetime import datetime, timezone
from utils import cfg

base = cfg('urlBase')
subfolder = cfg('urlFolder')

def generate_feed():
    fg = FeedGenerator()
    fg.load_extension('podcast')
    fg.podcast.itunes_category('Podcasting')
    fg.id('http://lernfunk.de/media/654321')
    fg.title('radio proxy feed')
    fg.author( {'name':'John Doe','email':'john@example.de'} )
    fg.link( href='http://example.com', rel='alternate' )
    # fg.logo('http://ex.com/logo.jpg')
    fg.subtitle('dummy subtitle')
    fg.link( href=base, rel='self' )
    fg.language('en')

    return fg

def add_entry(fg, item):

    id = item[0]
    fname = item[1]
    title = item[2]
    date = item[3]

    if subfolder:
        url = f'{base}{subfolder}/{fname}'
    else:
        url = base + fname

    fe = fg.add_entry()
    fe.id(f'{id:04}')
    fe.title(title)

    dt = datetime.strptime(date, '%Y-%m-%d')
    dt = dt.replace(tzinfo=timezone.utc)

    fe.pubDate(dt)

    # fe.description('description: ' + title)
    fe.enclosure(url, 0, 'audio/mpeg')


def generate():

    fg = generate_feed()

    '''
    files = os.listdir(folder)

    for f in files:
        print(f'adding {f}...')
        add_entry(fg, f)
    '''

    utils.cacheLoad()

    items = utils.fileCache.get('items')
    for item in items:
        add_entry(fg, item)

    fg.rss_str(pretty=True)
    fg.rss_file('podcast.xml')

if __name__ == '__main__':
    generate()
