"""Render / Gunicorn entrypoint. Local preview remains python app.py."""
import io
import os
from urllib.parse import urlsplit
from flask import Flask, Response, request, send_from_directory, redirect

os.environ.setdefault('REFUNDLY_HOSTED', '1')
origin = (os.environ.get('PUBLIC_BASE_URL') or os.environ.get('RENDER_EXTERNAL_URL', '')).rstrip('/')
if not origin.startswith('https://') or not urlsplit(origin).hostname:
    raise RuntimeError('Set PUBLIC_BASE_URL to the HTTPS site URL (Render supplies RENDER_EXTERNAL_URL).')

import staff
from app import Handler, RULES, ROOT
staff.initialize(RULES)
app = Flask(__name__, static_folder=None)
app.config['MAX_CONTENT_LENGTH'] = 100000

class RequestAdapter(Handler):
    def __init__(self):
        self.path = request.path
        self.headers = request.headers
        self.client_address = (request.remote_addr or 'unknown', 0)
        self.rfile = io.BytesIO(request.get_data())
        self.wfile = io.BytesIO()
        self.output_headers = {}
        self.extra_headers = {}
        self.status = 200
    def valid_host(self):
        return request.host == urlsplit(origin).netloc
    def send_response(self, status, message=None):
        self.status = status
    def send_header(self, name, value):
        self.output_headers[name] = value
    def end_headers(self):
        pass
    def response(self):
        return Response(self.wfile.getvalue(), status=self.status, headers=self.output_headers)

@app.before_request
def check_host():
    # Health probes do not access application data.
    if request.path != '/health' and request.host != urlsplit(origin).netloc:
        return {'error': 'Unrecognized host.'}, 403

@app.after_request
def security_headers(response):
    response.headers.update({'Referrer-Policy':'no-referrer','X-Frame-Options':'DENY',
        'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
        'Strict-Transport-Security':'max-age=31536000'})
    return response

@app.get('/health')
def health():
    return {'ok': True}

@app.route('/api/<path:path>', methods=['GET','POST'])
def api(path):
    adapter = RequestAdapter()
    if request.method == 'POST':
        adapter.do_POST()
    elif path.startswith('staff/'):
        staff.handle(adapter, 'GET')
    elif path == 'config':
        adapter.respond(200,{k:v for k,v in staff.configuration().items() if k!='announcement'})
    elif path == 'rules':
        adapter.respond(200,staff.rules_snapshot(RULES))
    else:
        adapter.respond(404,{'error':'Not found.'})
    return adapter.response()

@app.get('/')
@app.get('/<path:path>')
def static_files(path='index.html'):
    pages = {'review': 'review.html', 'staff': 'staff.html', 'policies': 'policies.html'}
    reverse = {v: k for k, v in pages.items()}
    if path in reverse:
        query = ('?' + request.query_string.decode('latin-1')) if request.query_string else ''
        return redirect('/' + reverse[path] + query, code=308)
    return send_from_directory(ROOT / 'static', pages.get(path, path))
