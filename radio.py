from sys import set_coroutine_origin_tracking_depth
from flask import Flask, request, Response, render_template_string, redirect, url_for
from utils import cfg, log

from flask_session import Session
from flask import session

import os

import utils

from redis import Redis
from rq import Queue
from rq.job import Job, JobStatus
from rq.exceptions import NoSuchJobError

from tasks import enqueueOne

import time
from functools import wraps

app = Flask(__name__)
mydir = os.path.dirname(os.path.realpath(__file__))
sessionPath = os.path.join(mydir, 'sessions')

os.makedirs(sessionPath, exist_ok=True)

usernames = cfg('users')
pwds = cfg('pwds')

secretKey = cfg('secretKey')

app.config.update(
    SECRET_KEY = secretKey,
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=sessionPath,
    SESSION_PERMANENT=True,
    SESSION_REFRESH_EACH_REQUEST=False,
    PERMANENT_SESSION_LIFETIME=365*24*60*60
)


Session(app)

HTML_FORM = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Radio Nyanya</title>
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
        <select name="target">
        {% for val, sel in targets %}
        <option value="{{ val }}" {% if sel %}selected{% endif %}>{{ val }}</option>
        {% endfor %}
        </select>
        <input type="text" name="user_input" autocomplete="off" value="">
        <button type="submit">send</button>
    </form>
    {% if submitted %}
        <p>got this: {{ submitted }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        passwd = request.form.get("password")
        

        for username, pwd in zip(usernames, pwds):
            if user == username and passwd == pwd:
                session["user"] = username
                session.permanent = True
                return redirect(url_for("index"))

        return "Invalid credentials", 401

    return render_template_string("""
        <form method="post">
            <input name="username">
            <input name="password" type="password">
            <button type="submit">Login</button>
        </form>
    """)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/status/<job_id>")
@login_required
def status(job_id):
    redis = Redis(host="127.0.0.1", port=6379)
    contentType = {'Content-Type': 'text/plain; charset=utf-8'}
    job = None

    try:
        job = Job.fetch(job_id, connection=redis)
    except NoSuchJobError:
        return 'not found', 404, contentType
    
    status = job.get_status()
    last_log = job.meta.get('last_msg')
    
    body = f'{status}\n'
    body += str(last_log)

    if job and job.is_failed:
        body += job.exc_info
    
    return body, 200, contentType
    
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    result = None
    status = None
    log('', nots=True)
    if request.method == "POST":
        
        url = request.form.get("user_input")
        target = request.form.get("target")

        log(f'{url=}, {target=}')
        
        if url and url[:8] == 'https://':
            redis = Redis(host="127.0.0.1", port=6379)
            queue = cfg('env', 'default')
            q = Queue(queue, connection=redis)

            log(f'connected to queue {queue}')

            if session.get('target') != target:
                session['target'] = target

            job = q.enqueue(enqueueOne, url=url, target=target, job_timeout=600)
            log(f'sent to queue, job id: {job.id}')
            time.sleep(0.345)
            return redirect(f'/status/{job.id}', code=303)
        else:
            status = '[E] seems invalid url, aborted'

        log(status)
    else:
        log('get / request')
        
    targetCfg = cfg('target')
    targets = []

    for t in targetCfg:
        if t == session['target']:
            targets.append([t, True])
        else:
            targets.append([t, None])
    
    return render_template_string(HTML_FORM, submitted=status, targets=targets)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
