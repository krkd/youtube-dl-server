import os
import ssl
import sys
import json
import asyncio
import logging
import argparse
import subprocess
from functools import wraps
from aiohttp import web

q = asyncio.Queue()

abspath = lambda x: os.path.join(os.getcwd(), x)

LOGGING_FORMAT = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s'
logging.basicConfig(format=LOGGING_FORMAT, stream=sys.stdout)

log = logging.getLogger('ydl-server')
log.setLevel(logging.DEBUG)

CMD_DOWNLOAD_VIDEO_FORMAT = \
    'youtube-dl --add-meta -f "bestvideo/best" --no-progress --no-playlist -o "{}"  "{{}}"'
CMD_DOWNLOAD_AUDIO_FORMAT = \
    'youtube-dl --add-meta -f "bestaudio/best" --no-progress --no-playlist -x -o "{}" --audio-format "mp3" "{{}}"'


class Response(web.Response):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        if 'ACCESS-CONTROL-ALLOW-ORIGIN' not in self.headers:
            self.headers.extend({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'})


def required_params(GET=None, POST=None):
    assert GET or POST, "There is no point of using this decorator"

    def func_wrapper(func):
        @wraps(func)
        def wrapped(request):
            passed = True
            if GET:
                key_view = request.GET.keys()
                passed = all(k in key_view for k in GET)
            # calling request.POST when it is None will raise runtime error
            if passed and POST and request._post is not None:
                key_view = request.POST.keys()
                passed = all(k in key_view for k in GET)

            if passed:
                return func(request)
            else:
                return Response(text="Page not found", status=404)
        return wrapped

    return func_wrapper


@asyncio.coroutine
@required_params(GET=['url', 'action'])
def handle(request):
    action = request.GET['action']
    if action == 'store_audio':
        cmd = CMD_DOWNLOAD_AUDIO_FORMAT.format(request.GET['url'])
    elif action == 'store_video':
        cmd = CMD_DOWNLOAD_VIDEO_FORMAT.format(request.GET['url'])
    else:
        return Response(text="Page not found", status=404)

    future = asyncio.Future()
    q.put_nowait((future, cmd))
    result = yield from future
    log.info('Got result: %s', result)
    return Response(body=result.encode())


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
        future, cmd = yield from q.get()
        log.info(cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while p.poll() is None:  # calling p.communicate before process terminated will block server
            yield from asyncio.sleep(0.1)

        stdout, stderr = p.communicate()
        stdout, stderr = stdout.decode(), stderr.decode()

        if p.poll() == 0:
            log.info(stdout)
            future.set_result(json.dumps({'status': 'ok', 'msg': 'download successful'}))
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
    '--dest_audio', action='store', dest='dest_audio',
    default=abspath('downloads/audio'),
    help='Folder where yds will download files')
parser.add_argument(
    '--dest_video', action='store', dest='dest_video',
    default=abspath('downloads/video'),
    help='Folder where yds will download files')
parser.add_argument(
    '--sslcert', action='store', dest='certfile', default=abspath('ssl/cert.pem'), help='SSL cert file')
parser.add_argument(
    '--sslkey', action='store', dest='keyfile', default=abspath('ssl/key.pem'), help='SSL key file')


if __name__ == '__main__':
    args = parser.parse_args()

    CMD_DOWNLOAD_VIDEO_FORMAT = CMD_DOWNLOAD_VIDEO_FORMAT.format(os.path.join(args.dest_video, '%(title)s.%(ext)s'))
    CMD_DOWNLOAD_AUDIO_FORMAT = CMD_DOWNLOAD_AUDIO_FORMAT.format(os.path.join(args.dest_audio, '%(title)s.%(ext)s'))

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
