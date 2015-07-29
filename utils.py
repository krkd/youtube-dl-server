from aiohttp.web import Response as _Response


class Response(_Response):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.headers.extend({'ACCESS-CONTROL-ALLOW-ORIGIN': '*'})
