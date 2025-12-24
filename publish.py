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

def cleanup(s3client):
    utils.cacheLoad()
    utils.cacheClean(s3client)
    utils.cacheDump()

def publish(s3client):
    files = []

    subfolder = cfg('urlFolder', '')
    if subfolder:
        subfolder += '/'

    feedFileName = subfolder + feedFile

    try:
        log(f'Uploading feed itself: {feedFileName}...')
        s3client.upload_file('podcast.xml', bucket, feedFileName, ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/xml'})

        if cfg('uploadContent'):
            files = checkUploads()

        if not files:
            log('No content to upload.')

        for f in files:
            trgt = f'{subfolder}{f}'
            src = os.path.join(storage, f)
            log(f'Uploading {src} --> {trgt}...', nots=True)
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
