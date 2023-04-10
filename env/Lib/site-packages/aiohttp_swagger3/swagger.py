import json
import pathlib
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Awaitable, Callable, DefaultDict, Dict, Optional, Set, Tuple, Type, Union

import fastjsonschema
from aiohttp import hdrs, web
from aiohttp.abc import AbstractView

from .context import STRING_FORMATS
from .handlers import application_json, x_www_form_urlencoded
from .index_templates import RAPIDOC_UI_TEMPLATE, REDOC_UI_TEMPLATE, SWAGGER_UI_TEMPLATE
from .routes import (
    _RAPIDOC_UI_INDEX_HTML,
    _REDOC_UI_INDEX_HTML,
    _SWAGGER_UI_INDEX_HTML,
    _rapidoc_ui,
    _redirect,
    _redoc_ui,
    _swagger_spec,
    _swagger_ui,
)
from .string_formats import (
    sf_byte_validator,
    sf_date_time_validator,
    sf_date_validator,
    sf_email_validator,
    sf_hostname_validator,
    sf_ipv4_validator,
    sf_ipv6_validator,
    sf_uuid_validator,
)
from .ui_settings import RapiDocUiSettings, ReDocUiSettings, SwaggerUiSettings

if TYPE_CHECKING:
    from .swagger_route import SwaggerRoute


WebHandler = Callable[[web.Request], Awaitable[web.StreamResponse]]
ExpectHandler = Callable[[web.Request], Awaitable[None]]


class Swagger(web.UrlDispatcher):
    __slots__ = ("_app", "validate", "spec", "request_key", "handlers", "spec_validate")

    def __init__(
        self,
        app: web.Application,
        *,
        validate: bool,
        spec: Dict,
        request_key: str,
        swagger_ui_settings: Optional[SwaggerUiSettings],
        redoc_ui_settings: Optional[ReDocUiSettings],
        rapidoc_ui_settings: Optional[RapiDocUiSettings],
    ) -> None:
        self._app = app
        self.validate = validate
        self.spec = spec
        self.request_key = request_key
        self.handlers: DefaultDict[str, Dict[str, Callable[[web.Request], Awaitable[Tuple[Any, bool]]]]] = defaultdict(
            dict
        )

        uis = (rapidoc_ui_settings, redoc_ui_settings, swagger_ui_settings)
        paths: Set[str] = set()
        for ui in uis:
            if ui is None:
                continue
            if ui.path in paths:
                raise Exception("cannot bind two UIs on the same path")
            paths.add(ui.path)

        base_path = pathlib.Path(__file__).parent
        with open(base_path / "schema/schema.json") as f:
            schema = json.load(f)

        self.spec_validate = fastjsonschema.compile(
            schema, formats={"uri-reference": r"^\w+:(\/?\/?)[^\s]+\Z|^#(\/\w+)+"}
        )
        self.spec_validate(self.spec)

        for ui in uis:
            if ui is not None:
                self._register_ui(ui)

        STRING_FORMATS.set({})
        if self.validate:
            self.register_media_type_handler("application/json", application_json)
            self.register_media_type_handler("application/x-www-form-urlencoded", x_www_form_urlencoded)

            self.register_string_format_validator("byte", sf_byte_validator)
            self.register_string_format_validator("date-time", sf_date_time_validator)
            self.register_string_format_validator("date", sf_date_validator)
            self.register_string_format_validator("email", sf_email_validator)
            self.register_string_format_validator("hostname", sf_hostname_validator)
            self.register_string_format_validator("ipv4", sf_ipv4_validator)
            self.register_string_format_validator("ipv6", sf_ipv6_validator)
            self.register_string_format_validator("uuid", sf_uuid_validator)

        super().__init__()

    def _register_ui(self, ui_settings: Union[SwaggerUiSettings, ReDocUiSettings, RapiDocUiSettings]) -> None:
        ui_path = ui_settings.path
        if not ui_path.startswith("/"):
            raise Exception("path should start with /")
        need_redirect = ui_path != "/"
        ui_path = ui_path.rstrip("/")
        if need_redirect:
            self._app.router.add_route("GET", ui_path, _redirect)

        if isinstance(ui_settings, SwaggerUiSettings):
            ui_handler = _swagger_ui
            ui_template = SWAGGER_UI_TEMPLATE
            ui_index_html = _SWAGGER_UI_INDEX_HTML
            dir_name = "swagger_ui"
        elif isinstance(ui_settings, ReDocUiSettings):
            ui_handler = _redoc_ui
            ui_template = REDOC_UI_TEMPLATE
            ui_index_html = _REDOC_UI_INDEX_HTML
            dir_name = "redoc_ui"
        else:
            ui_handler = _rapidoc_ui
            ui_template = RAPIDOC_UI_TEMPLATE
            ui_index_html = _RAPIDOC_UI_INDEX_HTML
            dir_name = "rapidoc_ui"
        self._app.router.add_route("GET", f"{ui_path}/", ui_handler)
        self._app.router.add_route("GET", f"{ui_path}/swagger.json", _swagger_spec)

        base_path = pathlib.Path(__file__).parent
        self._app.router.add_static(f"{ui_path}/{dir_name}_static", base_path / dir_name)

        self._app[ui_index_html] = ui_template.substitute({"settings": json.dumps(ui_settings.to_settings())})

    def add_head(self, path: str, handler: WebHandler, **kwargs: Any) -> web.AbstractRoute:
        return self.add_route(hdrs.METH_HEAD, path, handler, **kwargs)

    def add_options(self, path: str, handler: WebHandler, **kwargs: Any) -> web.AbstractRoute:
        return self.add_route(hdrs.METH_OPTIONS, path, handler, **kwargs)

    def add_get(
        self,
        path: str,
        handler: WebHandler,
        name: Optional[str] = None,
        allow_head: bool = True,
        **kwargs: Any,
    ) -> web.AbstractRoute:
        if allow_head:
            self.add_route(hdrs.METH_HEAD, path, handler, **kwargs)
        return self.add_route(hdrs.METH_GET, path, handler, name=name, **kwargs)

    def add_post(self, path: str, handler: WebHandler, **kwargs: Any) -> web.AbstractRoute:
        return self.add_route(hdrs.METH_POST, path, handler, **kwargs)

    def add_put(self, path: str, handler: WebHandler, **kwargs: Any) -> web.AbstractRoute:
        return self.add_route(hdrs.METH_PUT, path, handler, **kwargs)

    def add_patch(self, path: str, handler: WebHandler, **kwargs: Any) -> web.AbstractRoute:
        return self.add_route(hdrs.METH_PATCH, path, handler, **kwargs)

    def add_delete(self, path: str, handler: WebHandler, **kwargs: Any) -> web.AbstractRoute:
        return self.add_route(hdrs.METH_DELETE, path, handler, **kwargs)

    def add_view(self, path: str, handler: Type[AbstractView], **kwargs: Any) -> web.AbstractRoute:
        return self.add_route(hdrs.METH_ANY, path, handler, **kwargs)

    def register_media_type_handler(
        self,
        media_type: str,
        handler: Callable[[web.Request], Awaitable[Tuple[Any, bool]]],
    ) -> None:
        """This method allows registering custom handler for a media type

        Please, see `example <https://github.com/hh-h/aiohttp-swagger3/blob/master/examples/custom_media_type_handler/main.py>`__

        .. warning::

           `register_media_type_handler` must be called before adding route with media type

           ✘

           .. code-block:: python

              swagger = SwaggerDocs(app)
              swagger.add_post("/r", handler)
              swagger.register_media_type_handler("custom/handler", custom_handler)

           ✔

           .. code-block:: python

              swagger = SwaggerDocs(app)
              swagger.register_media_type_handler("custom/handler", custom_handler)
              swagger.add_post("/r", handler)

        :param str media_type: The name of custom string format
        :param handler: The handler function that will be executed for the media type
        """
        typ, subtype = media_type.split("/")
        self.handlers[typ][subtype] = handler

    def register_string_format_validator(self, string_format: str, validator: Callable[[str], None]) -> None:
        """This method allows registering a custom validator for string format

        Please, see `example <https://github.com/hh-h/aiohttp-swagger3/blob/master/examples/custom_string_format/main.py>`__

        :param str string_format: The name of custom string format
        :param validator: The validator function that should be used for
            validating passed string format
        """
        sf_validators = STRING_FORMATS.get()
        sf_validators[string_format] = validator

    def _get_media_type_handler(self, media_type: str) -> Callable[[web.Request], Awaitable[Tuple[Any, bool]]]:
        typ, subtype = media_type.split("/")
        if typ not in self.handlers:
            if "*" not in self.handlers:
                raise Exception(f"register handler for {media_type} first")
            if subtype not in self.handlers["*"]:
                if "*" not in self.handlers["*"]:
                    raise Exception("missing handler for media type */*")
                return self.handlers["*"]["*"]
            return self.handlers["*"][subtype]
        if subtype not in self.handlers[typ]:
            if "*" not in self.handlers[typ]:
                raise Exception(f"register handler for {media_type} first")
            return self.handlers[typ]["*"]
        return self.handlers[typ][subtype]


async def _handle_swagger_call(route: "SwaggerRoute", request: web.Request) -> web.StreamResponse:
    kwargs = await route.parse(request)
    return await route.handler(**kwargs)


async def _handle_swagger_method_call(view: web.View, route: "SwaggerRoute") -> web.StreamResponse:
    kwargs = await route.parse(view.request)
    return await route.handler(view, **kwargs)
