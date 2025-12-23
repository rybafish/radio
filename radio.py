from flask import Flask, request, Response, render_template_string, redirect
from download import download
from publish import s3Connect, cleanup, publish
from generate import generate
from utils import cfg, log
import utils

from redis import Redis
from rq import Queue
from rq.job import Job, JobStatus
from rq.exceptions import NoSuchJobError

import time

app = Flask(__name__)

username = "dug"
pwd = "neuromancer1024"

HTML_FORM = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Simple Form</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: sans-serif;
            margin: 20px;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            font-size: 18px;
            box-sizing: border-box;
            margin-bottom: 10px;
        }
        button {
            padding: 12px 20px;
            font-size: 18px;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
        }
    </style>
	
</head>
<body>
    <h1>one at a time</h1>
    <form method="post" autocomplete="off">
        <input type="text" name="user_input" autocomplete="off" value="">
        <button type="submit">send</button>
    </form>
    {% if submitted %}
        <p>got this: {{ submitted }}</p>
    {% endif %}
</body>
</html>
"""

def check_auth(username, password):
    return username == username and password == pwd


def authenticate():
    return Response(
        'identify yourself', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

def enqueueOne(url):
    utils.cacheLoad()
    storage = cfg('storage')
    download(url, storage)
        
    utils.cacheDump()
    
    s3client = s3Connect()

    cleanup(s3client)
    generate()
    publish(s3client)

@app.route("/status/<job_id>")
@requires_auth
def status(job_id):
    redis = Redis(host="127.0.0.1", port=6379)
    contentType = {'Content-Type': 'text/plain'}

    try:
        job = Job.fetch(job_id, connection=redis)
    except NoSuchJobError:
        return 'not found', 404, contentType
    
    status = job.get_status()
    last_log = job.meta.get('last_msg')
    
    body = f'{status}\n'
    body += str(last_log)
    
    return body, 200, contentType
    
@app.route("/", methods=["GET", "POST"])
@requires_auth
def index():
    result = None
    status = None
    log('', nots=True)
    if request.method == "POST":
        
        url = request.form.get("user_input")
        
        if url and url[:8] == 'https://':
            redis = Redis(host="127.0.0.1", port=6379)
            q = Queue("default", connection=redis)

            log('connected to queue')

            job = q.enqueue(enqueueOne, url=url, job_timeout=600)
            log(f'sent to queue, job id: {job.id}')
            time.sleep(0.345)
            return redirect(f'/status/{job.id}', code=303)
        else:
            status = '[E] seems invalid url, aborted'

        log(status)
        
    return render_template_string(HTML_FORM, submitted=status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
