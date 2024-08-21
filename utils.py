import sys, os, time
import datetime

from yaml import safe_load, dump, YAMLError #pip install pyyaml

config = {}
fileCache = {}

# commit test

def loadConfig(silent=False):

    global config

    script = sys.argv[0]
    path, file = os.path.split(script)
    
    cfgFile = os.path.join(path, 'config.yaml')

    config.clear()

    try: 
        f = open(cfgFile, 'r')
        config = safe_load(f)
        f.close()
    except:
        print('[!] No config file?')
        config = {}
        return False
        
    return True
    
def cfg(param, default = None):

    global config

    if param in config:
        return config[param]
    else:
        return default

def cacheId():
    global fileCache

    items = fileCache.get('items')

    if items is None:
        items = []
        fileCache['items'] = items

    if items:
        id = items[-1][0] + 1
    else:
        id = 1

    return id

def cacheAdd(fname, title, date, length):
    global fileCache

    items = fileCache.get('items')

    id = cacheId()
    date_str = date.strftime('%Y-%m-%d %H:%M:%S')

    items.append([id, fname, title, date_str, length])

    # fileCache['items'] = items

def cachePurge(s3client, purgeList):

    if not cfg('uploadContent'):
        print('[W] cache purge currently only works for S3 bucket, not local storage (uploadContent is False)')

    bucket = cfg('bucket')
    subfolder = cfg('urlFolder', '')
    if subfolder:
        subfolder += '/'

    print('Purging the storage...')

    for item in purgeList:
        fname = f'{subfolder}{item[1]}'
        print(f'{fname}...',  end='', flush=True)

        s3client.delete_object(Bucket=bucket, Key=fname)

        print(' [D]')


def cacheClean(s3client):
    global fileCache

    items = fileCache.get('items')

    maxLen = cfg('maxFiles', 32)
    maxDays = cfg('maxDays', 14)
    maxDate = datetime.datetime.today() + datetime.timedelta(days=-maxDays)
    maxDate = maxDate.strftime('%Y-%m-%d %H:%M:%S')

    purgeList = []              # list of items to delete
    newItems = []

    # first purge outdated items
    for item in items:
        if item[3] < maxDate:
            purgeList.append(item)
        else:
            newItems.append(item)

    # now check the number of entries
    if len(newItems) > maxLen:
        # purgeList += newItems[maxLen-1:] -- oops
        purgeList += newItems[:-maxLen]
        newItems = newItems[-maxLen:]

    fileCache['items'] = newItems

    if purgeList:
        cachePurge(s3client, purgeList)
    else:
        print('no items to purge, skipping')

def cacheLoad():
    global fileCache

    script = sys.argv[0]
    path, file = os.path.split(script)

    yamlFile = os.path.join(path, 'files.yaml')

    fileCache.clear()

    try:
        f = open(yamlFile, 'r', encoding='utf-8')
        fileCache = safe_load(f)
        f.close()
    except Exception as e:
        print('Seems file cache does not exist yet...')
        print(e)
        fileCache = {}
        return False

    return True

def cacheDump():
    try:
        f = open('files.yaml', 'w', encoding='utf-8')
        dump(fileCache, f, default_flow_style=None, sort_keys=False, allow_unicode=True)
        f.close()
    except:
        print('[E] File cache dump issue')

        return False

def formatTime(t, skipSeconds = False, skipMs = False):

    (ti, ms) = divmod(t, 1)

    ms = round(ms, 3)

    if ms == 1:
        ti += 1
        ms = '0'
    else:
        ms = str(int(ms*1000)).rstrip('0')

    if ti < 60:

        s = str(round(t, 3)) + ' s'

    elif ti < 3600:
        format = '%M:%S'

        msStr = '.%s' % ms if not skipMs else ''

        s = time.strftime(format, time.gmtime(ti)) + msStr
    else:
        format = '%H:%M:%S'
        msStr = '.%s' % ms if not skipMs else ''
        s = time.strftime(format, time.gmtime(ti)) + msStr

    if not skipSeconds:
        s += '   (' + str(round(t, 3)) + ')'

    return s


loadConfig()
