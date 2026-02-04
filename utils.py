from dataclasses import field
from ntpath import isfile
import sys, os, time
import datetime
from pathlib import Path
from yaml import safe_load, dump, YAMLError #pip install pyyaml
from rq import get_current_job

config = {}
fileCache = {}

# commit test2

logger = ''

def log(s, nots=False, nonl=False):
    job = get_current_job()
    pfx = ''

    if not nots:
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ' '
    else:
        ts = ''

    if cfg('bg'):
        pass
    else:
        print('[l]', pfx, s)
       
    if nonl:
        nl = ''
    else:
        nl = '\n'
        
    if job:
        global logger
        logger += ts + pfx + str(s) + nl
        job.meta['last_msg'] = logger
        job.save_meta()
   
    f = open('access.log', 'a')
   
    try:
        f.write(ts + pfx + str(s) + nl)

    except Exception as e:
        f.write(ts + str(e) + nl)
   
    f.close()
    
    
def loadConfig(silent=False):

    global config

    script = sys.argv[0]
    path, file = os.path.split(script)
    
    cfgfile = os.path.join(Path(__file__).resolve().parent, 'config.yaml')
    
    cfgFile = os.path.join(path, cfgfile)

    config.clear()

    try: 
        f = open(cfgFile, 'r')
        config = safe_load(f)
        f.close()
    except Exception as ex:
        log('[!] No config file?')
        log(ex)
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

    log(f'cacheId call')
    items = fileCache.get('items')

    if items is None:
        items = []
        fileCache['items'] = items

    if items:
        id = items[-1][0] + 1
    else:
        id = 1

    log(f'cacheId {fileCache=}')
    log(f'cacheId id: {id}')
    return id

def cacheAdd(fname, title, date, length):
    global fileCache

    log('cacheAdd')
    id = cacheId()
    items = fileCache.get('items')

    date_str = date.strftime('%Y-%m-%d %H:%M:%S')

    log(items)
    items.append([id, fname, title, date_str, length])
    log(items)

    # fileCache['items'] = items

def cachePurge(s3client, purgeList):

    if not cfg('uploadContent'):
        log('[W] cache purge currently only works for S3 bucket, not local storage (uploadContent is False)')

    bucket = cfg('bucket')
    subfolder = cfg('urlFolder', '')
    if subfolder:
        subfolder += '/'

    log('Cleaning the s3 storage...')

    for item in purgeList:
        fname = f'{subfolder}{item[1]}'
        log(f'{fname}...', nonl=True)

        s3client.delete_object(Bucket=bucket, Key=fname)

        log(' [D]')


def cacheClean(s3client):
    global fileCache

    log('cachePurge')

    items = fileCache.get('items') or {}

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
        log('no items to purge, skipping')

def cacheLoad(target):
    global fileCache

    log(f'cacheLoad: {target}')
    script = sys.argv[0]
    path, file = os.path.split(script)

    fname = f'files_{target}.yaml'
    filesFile = os.path.join(Path(__file__).resolve().parent, fname)

    yamlFile = os.path.join(path, filesFile)

    fileCache.clear()

    if not os.path.isfile(yamlFile):
        log(f'creating an empty {fname} file')
        open(yamlFile, 'a').close()

    try:
        f = open(yamlFile, 'r', encoding='utf-8')
        fileCache = safe_load(f)
        f.close()

        if not fileCache:
            fileCache = {}

    except Exception as e:
        log('Seems file cache does not exist yet...')
        log(e)
        fileCache = {}
        return False

    return True

def cacheDump(target):
    log(f'cacheDump: {fileCache}')
    try:
        fname = f'files_{target}.yaml'
        f = open(fname, 'w', encoding='utf-8')
        dump(fileCache, f, default_flow_style=None, sort_keys=False, allow_unicode=True)
        f.close()
    except:
        log('[E] File cache dump issue')

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
