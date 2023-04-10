from typing import Dict, Tuple
from urllib.parse import parse_qsl

from aiohttp import web

from .validators import ValidatorError


async def application_json(request: web.Request) -> Tuple[Dict, bool]:
    try:
        return await request.json(), False
    except ValueError as e:
        raise ValidatorError(str(e))


async def x_www_form_urlencoded(request: web.Request) -> Tuple[Dict, bool]:
    data = await request.read()
    charset = request.charset or "utf-8"
    d = parse_qsl(data.rstrip().decode(charset), keep_blank_values=True, encoding=charset)
    return dict(d), True
