import functools
from typing import Optional, Type, Union

import yaml
from aiohttp import hdrs, web
from aiohttp.abc import AbstractView

from .routes import _SWAGGER_SPECIFICATION
from .swagger import ExpectHandler, Swagger, _handle_swagger_call, _handle_swagger_method_call
from .swagger_route import SwaggerRoute, _SwaggerHandler
from .ui_settings import RapiDocUiSettings, ReDocUiSettings, SwaggerUiSettings


class SwaggerFile(Swagger):
    """This class should be used if you want to use swagger scheme.

    :param aiohttp.web.Application app: aiohttp's Application instance
    :param str spec_file: path to swagger file scheme
    :param bool validate: if ``False``, request validation is disabled, default ``True``
    :param str request_key: key name under which the data will be stored in ``request``
                            after validation, default ``data``
    :param swagger_ui_settings: class:`SwaggerUiSettings` (optional)
    :param redoc_ui_settings: class:`ReDocUiSettings` (optional)
    :param rapidoc_ui_settings: class:`RapiDocUiSettings` (optional)
    """

    __slots__ = ()

    def __init__(
        self,
        app: web.Application,
        spec_file: str = "",
        *,
        validate: bool = True,
        request_key: str = "data",
        swagger_ui_settings: Optional[SwaggerUiSettings] = None,
        redoc_ui_settings: Optional[ReDocUiSettings] = None,
        rapidoc_ui_settings: Optional[RapiDocUiSettings] = None,
    ) -> None:
        if not spec_file:
            raise Exception("spec file with swagger schema must be provided")
        with open(spec_file) as f:
            spec = yaml.safe_load(f)

        super().__init__(
            app,
            validate=validate,
            spec=spec,
            request_key=request_key,
            swagger_ui_settings=swagger_ui_settings,
            redoc_ui_settings=redoc_ui_settings,
            rapidoc_ui_settings=rapidoc_ui_settings,
        )
        self._app[_SWAGGER_SPECIFICATION] = self.spec

    def add_route(
        self,
        method: str,
        path: str,
        handler: Union[_SwaggerHandler, Type[AbstractView]],
        *,
        name: Optional[str] = None,
        expect_handler: Optional[ExpectHandler] = None,
        validate: Optional[bool] = None,
    ) -> web.AbstractRoute:
        if validate is None:
            need_validation: bool = self.validate
        else:
            need_validation = False if not self.validate else validate
        if need_validation and path in self.spec["paths"]:
            if isinstance(handler, type) and issubclass(handler, AbstractView):
                for meth in hdrs.METH_ALL:
                    meth = meth.lower()
                    if meth not in self.spec["paths"][path]:
                        continue
                    handler_ = getattr(handler, meth, None)
                    if handler_ is None:
                        continue
                    route = SwaggerRoute(meth, path, handler_, swagger=self)
                    setattr(
                        handler,
                        meth,
                        functools.partialmethod(_handle_swagger_method_call, route),
                    )
            else:
                method_lower = method.lower()
                if method_lower in self.spec["paths"][path]:
                    route = SwaggerRoute(method_lower, path, handler, swagger=self)
                    handler = functools.partial(_handle_swagger_call, route)

        return self._app.router.add_route(method, path, handler, name=name, expect_handler=expect_handler)
