import sys, os, time
import datetime

from yaml import safe_load, dump, YAMLError #pip install pyyaml

config = {}
fileCache = {}

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

def cacheAdd(fname, title, date):
    global fileCache

    items = fileCache.get('items')

    id = cacheId()

    items.append([id, fname, title, str(date)])

    maxLen = cfg('maxFiles', 32)
    maxDays = cfg('maxDays', 14)
    maxDate = str(date + datetime.timedelta(days=-maxDays))

    # remove old ones
    items = [i for i in items if i[3] > maxDate]

    # truncate if too many items
    if len(items) > maxLen:
        items = items[-maxLen:]

    fileCache['items'] = items

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

loadConfig()
