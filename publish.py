import boto3
from botocore.exceptions import ClientError
from utils import cfg, log
import utils
import os
from generate import generate

bucket = cfg('bucket')
storage = cfg('storage')
feedFile = cfg('feedFile')

def checkUploads():
    # checks if there are files in storage to be uploaded to s3
    files = os.listdir(storage)
    return files


def s3Connect():
    aws_key = cfg('key_id')
    aws_secret = cfg('access_key')
    s3 = boto3.resource('s3', aws_access_key_id=aws_key, aws_secret_access_key=aws_secret)
    s3client = boto3.client('s3', aws_access_key_id=aws_key, aws_secret_access_key=aws_secret)

    log('connected...')
    return s3client

def cleanup(s3client, target):
    utils.cacheLoad(target)
    utils.cacheClean(s3client, target)
    utils.cacheDump(target)

def publish(s3client, target=None):
    files = []

    prefix = cfg('urlPrefix', '')
    log(f'publish: {target=}, {prefix=}')

    if target:
        trgcfg = cfg('target')
        if trgcfg:
            subfolder = trgcfg.get(target).get('urlFolder', '')
        else:
            subfolder = ''
    else:
        subfolder = cfg('urlfolder', '')

    if subfolder:
        subfolder += '/'

    feedFileName = prefix + subfolder + feedFile

    try:
        log(f'Uploading feed itself: {feedFileName}...')

        s3client.upload_file(f'podcast_{target}.xml', bucket, feedFileName, ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/xml'})

        if cfg('uploadContent'):
            files = checkUploads()

        if not files:
            log('No content to upload.')

        for f in files:
            trgt = f'{prefix}{subfolder}{f}'
            src = os.path.join(storage, f)
            log(f'Uploading {src} --> {trgt}...', nonl=True)
            s3client.upload_file(src, bucket, trgt, ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/xml'})

            os.remove(src)
            log(' [D]', nots=True)

    except ClientError as e:
        log('\n[E] '+str(e))
        return False

    log('publish done')

    return True

if __name__ == '__main__':
    s3client = s3Connect()
    # publish(s3client)

    cleanup(s3client)
    generate()
    publish(s3client)
