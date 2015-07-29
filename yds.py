import asyncio
import ssl

from aiohttp.web import Application

from .log import applog as log
from .worker import AUDIO, VIDEO, worker
from .utils import Response


q = asyncio.Queue()

async def audio(request):
    future = asyncio.Future()
    q.put_nowait((future, (request.GET['url'], AUDIO)))
    response = await future
    return Response(body=b'ok')

async def video(request):
    future = asyncio.Future()
    q.put_nowait((future, (request.GET['url'], VIDEO)))
    response = await future
    return Response(body=b'ok')


async def init(loop, sslcontext, host, port):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/save/a', audio)
    # app.router.add_route('GET', '/save/v', video)
    srv = yield from loop.create_server(app.make_handler(), host, port, ssl=sslcontext)
    log.info('Started server on %s:%s', host, port)
    return srv


if __name__ == '__main__':

    LOGGING_FORMAT = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s'
    logging.basicConfig(format=LOGGING_FORMAT, stream=sys.stdout)

    sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    sslcontext.load_cert_chain(args.certfile, args.keyfile)

    loop = asyncio.get_event_loop()
    srv = loop.run_until_complete(init(loop, sslcontext, args.host, args.port))
    asyncio.async(worker(q, loop))
    try:
        loop.run_forever()
    finally:
        srv.close()
        loop.stop()
