import functools
import re
import warnings
from collections import defaultdict
from typing import Callable, Dict, Optional, Type, Union

import fastjsonschema
import yaml
from aiohttp import hdrs, web
from aiohttp.abc import AbstractView

from .routes import _SWAGGER_SPECIFICATION
from .swagger import ExpectHandler, Swagger, _handle_swagger_call, _handle_swagger_method_call
from .swagger_info import SwaggerInfo
from .swagger_route import SwaggerRoute, _SwaggerHandler
from .ui_settings import RapiDocUiSettings, ReDocUiSettings, SwaggerUiSettings

_PATH_VAR_REGEX = re.compile(r"{([_a-zA-Z][_a-zA-Z0-9].+?):.+?}(/|$)")


def swagger_doc(path: str) -> Callable:
    """
    This decorator can be used if you don't want to include the whole schema into docstring,
    so it can be placed in the YAML file and provide the path to the file,
    see `docs_decorator_and_docstrings <https://github.com/hh-h/aiohttp-swagger3/tree/master/examples/docs_decorator_and_docstrings>`__ example

    :param str path: path to swagger route schema
    """

    def wrapper(fn: Callable) -> Callable:
        doc = fn.__doc__ or ""
        if "---" in doc:
            raise Exception(f"cannot use decorator swagger_doc with docstring, function: {fn}")

        with open(path) as f:
            doc = f"{doc}---\n{f.read()}"
        fn.__doc__ = doc
        return fn

    return wrapper


class SwaggerDocs(Swagger):
    """This class should be used if you want to use documentation through handler doctrings.

    :param aiohttp.web.Application app: aiohttp's Application instance
    :param bool validate: if ``False``, request validation is disabled, default ``True``
    :param info: class:`SwaggerInfo`
    :param str request_key: key name under which the data will be stored in ``request``
                            after validation, default ``data``
    :param str components: path to file with components definitions (optional)
    :param str security: path to file with security definition (optional)
    :param swagger_ui_settings: class:`SwaggerUiSettings` (optional)
    :param redoc_ui_settings: class:`ReDocUiSettings` (optional)
    :param rapidoc_ui_settings: class:`RapiDocUiSettings` (optional)
    """

    __slots__ = ()

    def __init__(
        self,
        app: web.Application,
        *,
        validate: bool = True,
        info: Optional[SwaggerInfo] = None,
        request_key: str = "data",
        title: Optional[str] = None,
        version: Optional[str] = None,
        description: Optional[str] = None,
        components: Optional[str] = None,
        security: Optional[str] = None,
        swagger_ui_settings: Optional[SwaggerUiSettings] = None,
        redoc_ui_settings: Optional[ReDocUiSettings] = None,
        rapidoc_ui_settings: Optional[RapiDocUiSettings] = None,
    ) -> None:
        if info is not None and (title is not None or version is not None or description is not None):
            raise Exception("do not use SwaggerDocs' info with title or version or description")

        if info is None:
            info = SwaggerInfo(title="OpenAPI3", version="1.0.0")

        if title is not None:
            warnings.warn(
                "SwaggerDocs' title is deprecated and will be removed in 0.8.0, use info object instead.",
                FutureWarning,
            )
            info.title = title

        if version is not None:
            warnings.warn(
                "SwaggerDocs' version is deprecated and will be removed in 0.8.0, use info object instead.",
                FutureWarning,
            )
            info.version = version

        if description is not None:
            warnings.warn(
                "SwaggerDocs' description is deprecated and will be removed in 0.8.0, use info object instead.",
                FutureWarning,
            )
            info.description = description

        spec: Dict = {
            "openapi": "3.0.0",
            "info": info.to_json(),
            "paths": defaultdict(lambda: defaultdict(dict)),
        }

        if components:
            with open(components) as f:
                spec.update(yaml.safe_load(f))

        if security:
            with open(security) as f:
                spec.update(yaml.safe_load(f))

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

    def _wrap_handler(
        self,
        method: str,
        path: str,
        handler: _SwaggerHandler,
        *,
        is_method: bool,
        validate: bool,
    ) -> _SwaggerHandler:
        if not handler.__doc__ or "---" not in handler.__doc__:
            return handler
        *_, spec = handler.__doc__.split("---")
        method_spec = yaml.safe_load(spec)
        path = _PATH_VAR_REGEX.sub(r"{\1}\2", path)
        if self.spec["paths"].get(path, {}).get(method) is not None:
            raise Exception(f"{method} {path} already exists")

        self.spec["paths"][path][method] = method_spec
        try:
            self.spec_validate(self.spec)
        except fastjsonschema.exceptions.JsonSchemaException as exc:
            fn_name = handler.__name__
            raise Exception(f"Invalid schema for handler '{fn_name}' {method.upper()} {path} - {exc}")
        self._app[_SWAGGER_SPECIFICATION] = self.spec
        if not validate:
            return handler
        route = SwaggerRoute(method, path, handler, swagger=self)
        if is_method:
            return functools.partialmethod(_handle_swagger_method_call, route)  # type: ignore
        return functools.partial(_handle_swagger_call, route)

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
        if isinstance(handler, type) and issubclass(handler, AbstractView):
            for meth in hdrs.METH_ALL:
                meth = meth.lower()
                handler_ = getattr(handler, meth, None)
                if handler_ is not None:
                    setattr(
                        handler,
                        meth,
                        self._wrap_handler(
                            meth,
                            path,
                            handler_,
                            is_method=True,
                            validate=need_validation,
                        ),
                    )
        else:
            if method == hdrs.METH_ANY:
                for meth in (
                    hdrs.METH_GET,
                    hdrs.METH_POST,
                    hdrs.METH_PUT,
                    hdrs.METH_PATCH,
                    hdrs.METH_DELETE,
                ):
                    meth = meth.lower()
                    handler = self._wrap_handler(
                        meth,
                        path,
                        handler,
                        is_method=False,
                        validate=need_validation,
                    )
            else:
                handler = self._wrap_handler(
                    method.lower(),
                    path,
                    handler,
                    is_method=False,
                    validate=need_validation,
                )

        return self._app.router.add_route(method, path, handler, name=name, expect_handler=expect_handler)
