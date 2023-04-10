import datetime
import json
from typing import Any

from aiohttp import web

_RAPIDOC_UI_INDEX_HTML = "AIOHTTP_SWAGGER3_RAPIDOC_INDEX_HTML"
_REDOC_UI_INDEX_HTML = "AIOHTTP_SWAGGER3_REDOC_INDEX_HTML"
_SWAGGER_UI_INDEX_HTML = "AIOHTTP_SWAGGER3_SWAGGER_INDEX_HTML"
_SWAGGER_SPECIFICATION = "AIOHTTP_SWAGGER3_SWAGGER_SPECIFICATION"


class CustomEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


async def _swagger_ui(request: web.Request) -> web.Response:
    return web.Response(text=request.app[_SWAGGER_UI_INDEX_HTML], content_type="text/html")


async def _redoc_ui(request: web.Request) -> web.Response:
    return web.Response(text=request.app[_REDOC_UI_INDEX_HTML], content_type="text/html")


async def _rapidoc_ui(request: web.Request) -> web.Response:
    return web.Response(text=request.app[_RAPIDOC_UI_INDEX_HTML], content_type="text/html")


async def _swagger_spec(request: web.Request) -> web.Response:
    return web.json_response(
        request.app[_SWAGGER_SPECIFICATION],
        dumps=lambda obj: json.dumps(obj, cls=CustomEncoder),
    )


async def _redirect(request: web.Request) -> web.Response:
    return web.HTTPMovedPermanently(f"{request.path}/")
