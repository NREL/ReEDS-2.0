import json
from types import FunctionType
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, cast

import attr
from aiohttp import web

from .context import COMPONENTS
from .swagger import Swagger
from .validators import MISSING, Validator, ValidatorError, schema_to_validator, security_to_validator

_SwaggerHandler = Callable[..., Awaitable[web.StreamResponse]]

REQUEST_BODY_NAME: str = "body"


class RequestValidationFailed(web.HTTPBadRequest):
    """This exception can be caught in a aiohttp middleware.

    :param dict errors: This dict stores validation errors.
    """

    def __init__(self, errors: Dict, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.errors = errors


def _get_fn_parameters(fn: _SwaggerHandler) -> Tuple[str, ...]:
    func = cast(FunctionType, fn)
    if func.__closure__ is None:
        arg_count = func.__code__.co_argcount + func.__code__.co_kwonlyargcount
        return func.__code__.co_varnames[:arg_count]
    return _get_fn_parameters(func.__closure__[0].cell_contents)


@attr.attrs(slots=True, auto_attribs=True)
class Parameter:
    name: str
    validator: Validator
    required: bool


class SwaggerRoute:
    __slots__ = (
        "_swagger",
        "method",
        "path",
        "handler",
        "qp",
        "pp",
        "hp",
        "cp",
        "bp",
        "is_body_required",
        "auth",
        "params",
    )

    def __init__(self, method: str, path: str, handler: _SwaggerHandler, *, swagger: Swagger) -> None:
        self.method = method
        self.path = path
        self.handler = handler
        self.qp: List[Parameter] = []
        self.pp: List[Parameter] = []
        self.hp: List[Parameter] = []
        self.cp: List[Parameter] = []
        self.bp: Dict[str, Parameter] = {}
        self.auth: Optional[Parameter] = None
        self._swagger = swagger
        method_section = self._swagger.spec["paths"][path][method]
        parameters = method_section.get("parameters")
        body = method_section.get("requestBody")
        self.is_body_required = body and body.get("required", False)
        method_security = method_section.get("security")
        security = method_security if method_security is not None else self._swagger.spec.get("security", [])
        components = self._swagger.spec.get("components", {})
        COMPONENTS.set(components)
        if security:
            parameter = Parameter("", security_to_validator(security), True)
            self.auth = parameter
        if parameters is not None:
            for param in parameters:
                if "$ref" in param:
                    if not components:
                        raise Exception("file with components definitions is missing")
                    # '#/components/parameters/Month'
                    *_, section, obj = param["$ref"].split("/")
                    param = components[section][obj]
                parameter = Parameter(
                    param["name"],
                    schema_to_validator(param["schema"]),
                    param.get("required", False),
                )
                if param["in"] == "query":
                    self.qp.append(parameter)
                elif param["in"] == "path":
                    self.pp.append(parameter)
                elif param["in"] == "header":
                    parameter.name = parameter.name.lower()
                    self.hp.append(parameter)
                elif param["in"] == "cookie":
                    self.cp.append(parameter)

        if body is not None:
            for media_type, value in body["content"].items():
                # check that we have handler for media_type
                self._swagger._get_media_type_handler(media_type)
                value = body["content"][media_type]
                self.bp[media_type] = Parameter(
                    REQUEST_BODY_NAME,
                    schema_to_validator(value["schema"]),
                    body.get("required", False),
                )
        self.params = set(_get_fn_parameters(self.handler))

    async def parse(self, request: web.Request) -> Dict:
        params: Dict = {}
        if "request" in self.params:
            params["request"] = request
        request_key = self._swagger.request_key
        request[request_key] = {}
        errors: Dict = {}
        # check auth
        if self.auth:
            try:
                values = self.auth.validator.validate(request, True)
            except ValidatorError as e:
                if isinstance(e.error, str):
                    errors["authorization"] = e.error
                else:
                    errors = e.error
                raise RequestValidationFailed(reason=json.dumps(errors), errors=errors)

            for key, value in values.items():
                request[request_key][key] = value

        # query parameters
        if self.qp:
            for param in self.qp:
                if param.required:
                    try:
                        v: Any = request.rel_url.query.getall(param.name)
                    except KeyError:
                        errors[param.name] = "is required"
                        continue
                    if len(v) == 1:
                        v = v[0]
                else:
                    v = request.rel_url.query.getall(param.name, MISSING)
                    if v != MISSING and len(v) == 1:
                        v = v[0]
                try:
                    value = param.validator.validate(v, True)
                except ValidatorError as e:
                    errors[param.name] = e.error
                    continue
                if value != MISSING:
                    request[request_key][param.name] = value
                    if param.name in self.params:
                        params[param.name] = value
        # body parameters
        if self.bp:
            if request.body_exists:
                if "Content-Type" not in request.headers:
                    if next(iter(self.bp.values())).required:
                        errors[REQUEST_BODY_NAME] = "is required"
                else:
                    media_type = request.content_type
                    if media_type not in self.bp:
                        errors[REQUEST_BODY_NAME] = f"no handler for {media_type}"
                    else:
                        handler = self._swagger._get_media_type_handler(media_type)
                        param = self.bp[media_type]
                        try:
                            v, has_raw = await handler(request)
                        except ValidatorError as e:
                            errors[param.name] = e.error
                        else:
                            try:
                                value = param.validator.validate(v, has_raw)
                            except ValidatorError as e:
                                errors[param.name] = e.error
                            else:
                                request[request_key][param.name] = value
                                if param.name in self.params:
                                    params[param.name] = value

            elif self.is_body_required:
                errors[REQUEST_BODY_NAME] = "is required"

            else:
                request[request_key][REQUEST_BODY_NAME] = None
                if REQUEST_BODY_NAME in self.params:
                    params[REQUEST_BODY_NAME] = None

        # header parameters
        if self.hp:
            for param in self.hp:
                if param.required:
                    try:
                        v = request.headers.getone(param.name)
                    except KeyError:
                        errors[param.name] = "is required"
                        continue
                else:
                    v = request.headers.get(param.name, MISSING)
                try:
                    value = param.validator.validate(v, True)
                except ValidatorError as e:
                    errors[param.name] = e.error
                    continue
                if value != MISSING:
                    request[request_key][param.name] = value
                    if param.name in self.params:
                        params[param.name] = value
        # path parameters
        if self.pp:
            for param in self.pp:
                v = request.match_info[param.name]
                try:
                    value = param.validator.validate(v, True)
                except ValidatorError as e:
                    errors[param.name] = e.error
                    continue
                request[request_key][param.name] = value
                if param.name in self.params:
                    params[param.name] = value
        # cookie parameters
        if self.cp:
            for param in self.cp:
                if param.required:
                    try:
                        v = request.cookies[param.name]
                    except KeyError:
                        errors[param.name] = "is required"
                        continue
                else:
                    v = request.cookies.get(param.name, MISSING)
                try:
                    value = param.validator.validate(v, True)
                except ValidatorError as e:
                    errors[param.name] = e.error
                    continue
                if value != MISSING:
                    request[request_key][param.name] = value
                    if param.name in self.params:
                        params[param.name] = value

        if errors:
            raise RequestValidationFailed(reason=json.dumps(errors), errors=errors)
        return params
