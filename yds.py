import os
import ssl
import sys
import json
import asyncio
import logging
import argparse
import subprocess
from aiohttp import web
from urllib.parse import urlparse

q = asyncio.Queue()

abspath = lambda x: os.path.join(os.getcwd(), x)

LOGGING_FORMAT = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s'
logging.basicConfig(format=LOGGING_FORMAT, stream=sys.stdout)

log = logging.getLogger('ydl-server')
log.setLevel(logging.DEBUG)

ALLOWED_NETLOCS = ['www.youtube.com']


class Response(web.Response):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        if 'ACCESS-CONTROL-ALLOW-ORIGIN' not in self.headers:
            self.headers.extend({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'})


@asyncio.coroutine
def handle(request):
    url = request.GET.get('url')
    if url:
        parsed_url = urlparse(url)
        if parsed_url.netloc not in ALLOWED_NETLOCS:
            return Response(
                body=json.dumps({'status': 'error', 'msg': 'unsupported url %s' % url})
            )
        future = asyncio.Future()
        q.put_nowait((future, url))
        result = yield from future
        log.info('Got result: %s', result)
        return Response(body=result.encode())
    return Response(status=404)


@asyncio.coroutine
def init(loop, sslcontext, host, port):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/save', handle)
    srv = yield from loop.create_server(app.make_handler(), host, port, ssl=sslcontext)
    log.info('Started server on %s:%s', host, port)
    return srv


@asyncio.coroutine
def worker():
    while True:
        future, url = yield from q.get()
        log.info('Processing %s' % url)

        p = subprocess.Popen(CMD.format(url), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while p.poll() is None:  # calling p.communicate before process terminated will block server
            yield from asyncio.sleep(0.1)

        stdout, stderr = p.communicate()
        stdout, stderr = stdout.decode(), stderr.decode()

        if p.poll() == 0:
            try:
                res = json.loads(stdout)
            except ValueError:
                future.set_result(json.dumps({'status': 'error', 'msg': 'unexpected error'}))
                return
            future.set_result(json.dumps({'status': 'ok', 'msg': res['fulltitle']}))
        else:
            log.error(stderr)
            future.set_result(json.dumps({'status': 'error', 'msg': stderr.splitlines()[-1]}))


parser = argparse.ArgumentParser(description="Run yds http server")
parser.add_argument(
    '--host', action='store', dest='host', default='127.0.0.1',
    help='Host name')
parser.add_argument(
    '--port', action='store', dest='port', default=8070,
    type=int, help='Port number')
parser.add_argument(
    '--dest', action='store', dest='dest',
    default=abspath('downloads/%(title)s.%(ext)s'),
    help='Folder where yds will download files')
parser.add_argument(
    '--sslcert', action='store', dest='certfile', default=abspath('ssl/cert.pem'), help='SSL cert file')
parser.add_argument(
    '--sslkey', action='store', dest='keyfile', default=abspath('ssl/key.pem'), help='SSL key file')


if __name__ == '__main__':
    args = parser.parse_args()
    f = os.path.join(args.dest, '%(title)s.%(ext)s')
    CMD = 'youtube-dl --print-json -f "bestaudio/best" --no-progress -x -o "' + f + '" --audio-format "mp3" {}'

    sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    sslcontext.load_cert_chain(args.certfile, args.keyfile)

    loop = asyncio.get_event_loop()
    srv = loop.run_until_complete(init(loop, sslcontext, args.host, args.port))
    asyncio.async(worker())
    try:
        loop.run_forever()
    finally:
        srv.close()
        loop.stop()
