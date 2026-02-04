from publish import s3Connect, cleanup, publish
from download import download
from generate import generate
import utils
from utils import cfg, log

def enqueueOne(url, target):
    log(f'enqueueOne: {target=}')
    if not utils.cacheLoad(target):
        log('cache load issue, abort')
        return 'cacheLoad issue, exiting'
    log(utils.fileCache)
    
    # log(f'enqueue one for {target}')
    storage = cfg('storage')
    log('Starting download...')
    download(url, storage)
    log('Download done')
        
    utils.cacheDump(target)
    
    log('S3 manipulations:')
    s3client = s3Connect()

    cleanup(s3client, target)
    generate(target)
    publish(s3client, target)

    log('Done.')
