import enum
import operator
import re
from typing import Any, Dict, List, Optional, Pattern, Set, Type, Union

import attr
from aiohttp import web

from .context import COMPONENTS, STRING_FORMATS
from .exceptions import DiscriminatorValidationError, ValidatorError


class _MissingType:
    pass


MISSING = _MissingType()


@attr.attrs(slots=True, frozen=True, auto_attribs=True)
class DiscriminatorObject:
    property_name: str
    mapping: Dict[str, str]


@attr.attrs(slots=True, frozen=True, auto_attribs=True)
class Validator:
    def validate(self, value: Any, raw: bool) -> Any:
        raise NotImplementedError


class IntegerFormat(enum.Enum):
    Int32 = "int32"
    Int64 = "int64"


class NumberFormat(enum.Enum):
    Float = "float"
    Double = "double"


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class Integer(Validator):
    format: IntegerFormat = attr.attrib(converter=IntegerFormat)
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    exclusiveMinimum: bool = False
    exclusiveMaximum: bool = False
    enum: Optional[List[int]] = None
    nullable: bool = False
    readOnly: bool = False
    default: Optional[int] = None
    enum_set: Optional[Set[int]] = attr.attrib(init=False)

    @enum_set.default
    def _enum_set_default(self) -> Optional[Set[int]]:
        return None if self.enum is None else set(self.enum)

    def validate(self, raw_value: Union[None, int, str, _MissingType], raw: bool) -> Union[None, int, _MissingType]:
        is_missing = isinstance(raw_value, _MissingType)
        if not is_missing and self.readOnly:
            raise ValidatorError("property is read-only")
        if isinstance(raw_value, str):
            if not raw:
                raise ValidatorError("value should be type of int")
            try:
                value = int(raw_value)
            except ValueError:
                raise ValidatorError("value should be type of int")
        elif isinstance(raw_value, int) and not isinstance(raw_value, bool):
            value = raw_value
        elif raw_value is None:
            if self.nullable:
                return None
            raise ValidatorError("value should be type of int")
        elif is_missing:
            if self.default is None:
                return raw_value
            value = self.default
        else:
            raise ValidatorError("value should be type of int")
        if self.format == IntegerFormat.Int32 and not -2_147_483_648 <= value <= 2_147_483_647:
            raise ValidatorError("value out of bounds int32")

        if self.minimum is not None:
            op = operator.le if self.exclusiveMinimum else operator.lt
            if op(value, self.minimum):
                msg = "" if self.exclusiveMinimum else " or equal to"
                raise ValidatorError(f"value should be more than{msg} {self.minimum}")
        if self.maximum is not None:
            op = operator.ge if self.exclusiveMaximum else operator.gt
            if op(value, self.maximum):
                msg = "" if self.exclusiveMaximum else " or equal to"
                raise ValidatorError(f"value should be less than{msg} {self.maximum}")
        if self.enum_set is not None and value not in self.enum_set:
            raise ValidatorError(f"value should be one of {self.enum}")
        return value


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class Number(Validator):
    format: NumberFormat = attr.attrib(converter=NumberFormat)
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    exclusiveMinimum: bool = False
    exclusiveMaximum: bool = False
    enum: Optional[List[float]] = None
    nullable: bool = False
    readOnly: bool = False
    default: Optional[float] = None
    enum_set: Optional[Set[float]] = attr.attrib(init=False)

    @enum_set.default
    def _enum_set_default(self) -> Optional[Set[float]]:
        return None if self.enum is None else set(self.enum)

    def validate(
        self, raw_value: Union[None, int, float, str, _MissingType], raw: bool
    ) -> Union[None, float, _MissingType]:
        is_missing = isinstance(raw_value, _MissingType)
        if not is_missing and self.readOnly:
            raise ValidatorError("property is read-only")
        if isinstance(raw_value, str):
            if not raw:
                raise ValidatorError("value should be type of float")
            try:
                value = float(raw_value)
            except ValueError:
                raise ValidatorError("value should be type of float")
        elif isinstance(raw_value, float):
            value = raw_value
        elif isinstance(raw_value, int) and not isinstance(raw_value, bool):
            value = float(raw_value)
        elif raw_value is None:
            if self.nullable:
                return None
            raise ValidatorError("value should be type of float")
        elif is_missing:
            if self.default is None:
                return raw_value
            value = self.default
        else:
            raise ValidatorError("value should be type of float")

        if self.minimum is not None:
            op = operator.le if self.exclusiveMinimum else operator.lt
            if op(value, self.minimum):
                msg = "" if self.exclusiveMinimum else " or equal to"
                raise ValidatorError(f"value should be more than{msg} {self.minimum}")
        if self.maximum is not None:
            op = operator.ge if self.exclusiveMaximum else operator.gt
            if op(value, self.maximum):
                msg = "" if self.exclusiveMaximum else " or equal to"
                raise ValidatorError(f"value should be less than{msg} {self.maximum}")
        if self.enum_set is not None and value not in self.enum_set:
            raise ValidatorError(f"value should be one of {self.enum}")
        return value


def _re_compile(pattern: Optional[str]) -> Optional[Pattern]:
    if pattern is None:
        return None
    return re.compile(pattern)


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class String(Validator):
    pattern: Optional[Pattern] = attr.attrib(converter=_re_compile)
    format: Optional[str] = None
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    enum: Optional[List[str]] = None
    nullable: bool = False
    readOnly: bool = False
    default: Optional[str] = None
    enum_set: Optional[Set[str]] = attr.attrib(init=False)

    @enum_set.default
    def _enum_set_default(self) -> Optional[Set[str]]:
        return None if self.enum is None else set(self.enum)

    def validate(
        self, raw_value: Union[None, str, bytes, _MissingType], raw: bool
    ) -> Union[None, str, bytes, _MissingType]:
        is_missing = isinstance(raw_value, _MissingType)
        if not is_missing and self.readOnly:
            raise ValidatorError("property is read-only")
        if isinstance(raw_value, (str, bytes)):
            value = raw_value
        elif raw_value is None:
            if self.nullable:
                return None
            raise ValidatorError("value should be type of str")
        elif is_missing:
            if self.default is None:
                return raw_value
            value = self.default
        else:
            raise ValidatorError("value should be type of str")

        if self.minLength is not None and len(value) < self.minLength:
            raise ValidatorError(f"value length should be more than {self.minLength}")
        if self.maxLength is not None and len(value) > self.maxLength:
            raise ValidatorError(f"value length should be less than {self.maxLength}")
        if self.enum_set is not None and value not in self.enum_set:
            raise ValidatorError(f"value should be one of {self.enum}")

        if self.format is not None:
            string_formats = STRING_FORMATS.get()
            if isinstance(value, str) and self.format in string_formats:
                string_formats[self.format](value)

        if self.pattern and not self.pattern.search(value):
            raise ValidatorError(f"value should match regex pattern '{self.pattern.pattern}'")

        return value


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class Boolean(Validator):
    nullable: bool = False
    readOnly: bool = False
    default: Optional[bool] = None

    def validate(self, raw_value: Union[None, bool, str, _MissingType], raw: bool) -> Union[None, bool, _MissingType]:
        is_missing = isinstance(raw_value, _MissingType)
        if not is_missing and self.readOnly:
            raise ValidatorError("property is read-only")
        if isinstance(raw_value, str):
            if not raw:
                raise ValidatorError("value should be type of bool")
            if raw_value == "true":
                value = True
            elif raw_value == "false":
                value = False
            else:
                raise ValidatorError("value should be type of bool")
        elif isinstance(raw_value, bool):
            value = raw_value
        elif raw_value is None:
            if self.nullable:
                return None
            raise ValidatorError("value should be type of bool")
        elif is_missing:
            if self.default is None:
                return raw_value
            value = self.default
        else:
            raise ValidatorError("value should be type of bool")
        return value


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class Array(Validator):
    validator: Validator
    uniqueItems: bool
    minItems: Optional[int] = None
    maxItems: Optional[int] = None
    nullable: bool = False
    readOnly: bool = False

    def validate(self, raw_value: Union[None, str, List, _MissingType], raw: bool) -> Union[None, List, _MissingType]:
        is_missing = isinstance(raw_value, _MissingType)
        if not is_missing and self.readOnly:
            raise ValidatorError("property is read-only")
        if isinstance(raw_value, str):
            if not raw:
                raise ValidatorError("value should be type of list")
            items = []
            index = 0
            if raw_value:
                try:
                    for i, value in enumerate(raw_value.split(",")):
                        index = i
                        items.append(self.validator.validate(value, raw))
                except ValidatorError as e:
                    raise ValidatorError({index: e.error})
        elif isinstance(raw_value, list):
            items = []
            index = 0
            try:
                for i, value in enumerate(raw_value):
                    index = i
                    items.append(self.validator.validate(value, raw))
            except ValidatorError as e:
                raise ValidatorError({index: e.error})
        elif raw_value is None:
            if self.nullable:
                return None
            raise ValidatorError("value should be type of list")
        elif is_missing:
            return raw_value
        else:
            raise ValidatorError("value should be type of list")

        if self.minItems is not None and len(items) < self.minItems:
            raise ValidatorError(f"number or items must be more than {self.minItems}")
        if self.maxItems is not None and len(items) > self.maxItems:
            raise ValidatorError(f"number or items must be less than {self.maxItems}")
        if self.uniqueItems and len(items) != len(set(items)):
            raise ValidatorError("all items must be unique")
        return items


def to_discriminator(data: Optional[Dict]) -> Optional[DiscriminatorObject]:
    if data is None:
        return None
    return DiscriminatorObject(property_name=data["propertyName"], mapping=data.get("mapping", {}))


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class Object(Validator):
    properties: Dict[str, Validator]
    required: Set[str]
    minProperties: Optional[int] = None
    maxProperties: Optional[int] = None
    additionalProperties: Union[bool, Validator] = True
    nullable: bool = False
    readOnly: bool = False

    def validate(self, raw_value: Union[None, Dict, _MissingType], raw: bool) -> Union[None, Dict, _MissingType]:
        is_missing = isinstance(raw_value, _MissingType)
        if not is_missing and self.readOnly:
            raise ValidatorError("property is read-only")
        if raw_value is None:
            if self.nullable:
                return None
            raise ValidatorError("value should be type of dict")
        if not isinstance(raw_value, dict):
            if is_missing:
                return raw_value
            raise ValidatorError("value should be type of dict")
        value = {}
        errors: Dict = {}
        for name in self.required:
            if name not in raw_value:
                errors[name] = "required property"
        if errors:
            raise ValidatorError(errors)

        for name, validator in self.properties.items():
            prop = raw_value.get(name, MISSING)
            try:
                val = validator.validate(prop, raw)
                if val != MISSING:
                    value[name] = val
            except ValidatorError as e:
                errors[name] = e.error
        if errors:
            raise ValidatorError(errors)

        if isinstance(self.additionalProperties, bool):
            if not self.additionalProperties:
                additional_properties = raw_value.keys() - value.keys()
                if additional_properties:
                    raise ValidatorError({k: "additional property not allowed" for k in additional_properties})
            else:
                for key in raw_value.keys() - value.keys():
                    value[key] = raw_value[key]
        else:
            for name in raw_value.keys() - value.keys():
                validator = self.additionalProperties
                value[name] = validator.validate(raw_value[name], raw)
        if self.minProperties is not None and len(value) < self.minProperties:
            raise ValidatorError(f"number or properties must be more than {self.minProperties}")
        if self.maxProperties is not None and len(value) > self.maxProperties:
            raise ValidatorError(f"number or properties must be less than {self.maxProperties}")
        return value


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class Discriminator(Validator):
    validators: List[Validator]
    discriminator: Optional[DiscriminatorObject] = attr.attrib(converter=to_discriminator)
    mapping: Dict[str, int]

    def validate(self, raw_value: Any, raw: bool) -> Any:
        if self.discriminator is None:
            raise DiscriminatorValidationError
        if not isinstance(raw_value, dict):
            raise ValidatorError("value should be type of dict")
        schema_name = raw_value.get(self.discriminator.property_name)
        if schema_name is None:
            raise ValidatorError({self.discriminator.property_name: "is required"})
        validator_index = self.mapping.get(schema_name)
        if validator_index is None:
            mapping_schema_name = self.discriminator.mapping.get(schema_name)
            if mapping_schema_name is None:
                keys = list(self.discriminator.mapping.keys() | self.mapping.keys())
                raise ValidatorError({self.discriminator.property_name: f"must be one of {keys}"})
            validator_index = self.mapping[mapping_schema_name]
        try:
            return self.validators[validator_index].validate(raw_value, raw)
        except ValidatorError:
            raise DiscriminatorValidationError


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class OneOf(Discriminator):
    nullable: bool = False

    def validate(self, raw_value: Any, raw: bool) -> Any:
        if raw_value is None and self.nullable:
            return raw_value

        if self.discriminator is not None:
            try:
                return super().validate(raw_value, raw)
            except DiscriminatorValidationError:
                raise ValidatorError("fail to validate oneOf")

        found = False
        value = None
        for validator in self.validators:
            try:
                value = validator.validate(raw_value, raw)
            except ValidatorError:
                continue
            if found:
                raise ValidatorError("fail to validate oneOf")
            found = True
        if not found:
            raise ValidatorError("fail to validate oneOf")
        return value


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class AnyOf(Discriminator):
    nullable: bool = False

    def validate(self, raw_value: Any, raw: bool) -> Any:
        if raw_value is None and self.nullable:
            return raw_value

        if self.discriminator is not None:
            try:
                return super().validate(raw_value, raw)
            except DiscriminatorValidationError:
                raise ValidatorError("fail to validate anyOf")

        for validator in self.validators:
            try:
                return validator.validate(raw_value, raw)
            except ValidatorError:
                pass
        raise ValidatorError("fail to validate anyOf")


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True, kw_only=True)
class AllOf(Validator):
    nullable: bool = False
    validators: List[Validator]

    def validate(self, raw_value: Any, raw: bool) -> Any:
        if raw_value is None and self.nullable:
            return raw_value

        value: Dict = {}
        for validator in self.validators:
            value.update(validator.validate(raw_value, raw))
        return value


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class AuthNone(Validator):
    def validate(self, request: web.Request, _: bool) -> Dict[str, str]:
        return {}


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class AuthBasic(Validator):
    name: str = "authorization"

    def validate(self, request: web.Request, _: bool) -> Dict[str, str]:
        try:
            value = request.headers.getone(self.name)
        except KeyError:
            raise ValidatorError({self.name: "is required"})

        if not value.startswith("Basic "):
            raise ValidatorError({self.name: "value should start with 'Basic' word"})
        return {self.name: value.replace("Basic ", "")}


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class AuthBearer(Validator):
    name: str = "authorization"

    def validate(self, request: web.Request, _: bool) -> Dict[str, str]:
        try:
            value = request.headers.getone(self.name)
        except KeyError:
            raise ValidatorError({self.name: "is required"})

        if not value.startswith("Bearer "):
            raise ValidatorError({self.name: "value should start with 'Bearer' word"})
        return {self.name: value.replace("Bearer ", "")}


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class AuthApiKeyHeader(Validator):
    name: str

    def validate(self, request: web.Request, _: bool) -> Dict[str, str]:
        try:
            value = request.headers.getone(self.name)
        except KeyError:
            raise ValidatorError({self.name: "is required"})

        if len(value) == 0:
            raise ValidatorError({self.name: "value length should be more than 1"})
        return {self.name: value}


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class AuthApiKeyQuery(Validator):
    name: str

    def validate(self, request: web.Request, _: bool) -> Dict[str, str]:
        try:
            value = request.rel_url.query.getone(self.name)
        except KeyError:
            raise ValidatorError({self.name: "is required"})

        if len(value) == 0:
            raise ValidatorError({self.name: "value length should be more than 1"})
        return {self.name: value}


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class AuthApiKeyCookie(Validator):
    name: str

    def validate(self, request: web.Request, _: bool) -> Dict[str, str]:
        try:
            value = request.cookies[self.name]
        except KeyError:
            raise ValidatorError({self.name: "is required"})

        if len(value) == 0:
            raise ValidatorError({self.name: "value length should be more than 1"})
        return {self.name: value}


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class AnyOfAuth(Validator):
    validators: List[Validator]

    def validate(self, request: web.Request, raw: bool) -> Dict[str, str]:
        values: Dict[str, str] = {}
        valid = False
        for validator in self.validators:
            try:
                value: Dict[str, str] = validator.validate(request, raw)
                if value:
                    values.update(value)
                valid = True
            except ValidatorError:
                continue
        if not valid:
            raise ValidatorError("no auth has been provided")
        return values


@attr.attrs(slots=True, frozen=True, eq=False, hash=False, auto_attribs=True)
class AllOfAuth(Validator):
    validators: List[Validator]

    def validate(self, request: web.Request, raw: bool) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for validator in self.validators:
            values.update(validator.validate(request, raw))
        return values


def to_integer(schema: Dict, is_property: bool) -> Integer:
    read_only = schema.get("readOnly", False) if is_property else False
    return Integer(
        nullable=schema.get("nullable", False),
        readOnly=read_only,
        minimum=schema.get("minimum"),
        maximum=schema.get("maximum"),
        exclusiveMinimum=schema.get("exclusiveMinimum", False),
        exclusiveMaximum=schema.get("exclusiveMaximum", False),
        enum=schema.get("enum"),
        format=schema.get("format", IntegerFormat.Int64),
        default=schema.get("default"),
    )


def to_number(schema: Dict, is_property: bool) -> Number:
    read_only = schema.get("readOnly", False) if is_property else False
    return Number(
        nullable=schema.get("nullable", False),
        readOnly=read_only,
        minimum=schema.get("minimum"),
        maximum=schema.get("maximum"),
        exclusiveMinimum=schema.get("exclusiveMinimum", False),
        exclusiveMaximum=schema.get("exclusiveMaximum", False),
        enum=schema.get("enum"),
        format=schema.get("format", NumberFormat.Double),
        default=schema.get("default"),
    )


def to_string(schema: Dict, is_property: bool) -> String:
    read_only = schema.get("readOnly", False) if is_property else False
    return String(
        format=schema.get("format"),
        nullable=schema.get("nullable", False),
        readOnly=read_only,
        minLength=schema.get("minLength"),
        maxLength=schema.get("maxLength"),
        enum=schema.get("enum"),
        default=schema.get("default"),
        pattern=schema.get("pattern"),
    )


def to_boolean(schema: Dict, is_property: bool) -> Boolean:
    read_only = schema.get("readOnly", False) if is_property else False
    return Boolean(
        nullable=schema.get("nullable", False),
        readOnly=read_only,
        default=schema.get("default"),
    )


def to_array(schema: Dict, is_property: bool) -> Array:
    read_only = schema.get("readOnly", False) if is_property else False
    return Array(
        nullable=schema.get("nullable", False),
        readOnly=read_only,
        validator=schema_to_validator(schema["items"]),
        uniqueItems=schema.get("uniqueItems", False),
        minItems=schema.get("minItems"),
        maxItems=schema.get("maxItems"),
    )


def to_object(schema: Dict, is_property: bool) -> Object:
    properties = {k: schema_to_validator(v, is_property=True) for k, v in schema.get("properties", {}).items()}
    raw_additional_properties = schema.get("additionalProperties", True)
    if isinstance(raw_additional_properties, dict):
        additional_properties = schema_to_validator(raw_additional_properties)
    else:
        additional_properties = raw_additional_properties

    required = set(schema.get("required", []))
    for name, validator in properties.items():
        if getattr(validator, "readOnly", False):
            required.discard(name)

    read_only = schema.get("readOnly", False) if is_property else False
    return Object(
        nullable=schema.get("nullable", False),
        readOnly=read_only,
        properties=properties,
        required=required,
        minProperties=schema.get("minProperties"),
        maxProperties=schema.get("maxProperties"),
        additionalProperties=additional_properties,
    )


_TYPE_TO_FACTORY = {
    "integer": to_integer,
    "number": to_number,
    "string": to_string,
    "boolean": to_boolean,
    "array": to_array,
    "object": to_object,
}


def _type_to_validator(schema: Dict, *, is_property: bool) -> Validator:
    if "type" not in schema:
        raise KeyError("type is required")
    if schema["type"] not in _TYPE_TO_FACTORY:
        raise Exception(f"Unknown type '{schema['type']}'")
    return _TYPE_TO_FACTORY[schema["type"]](schema, is_property)


def schema_to_validator(schema: Dict, *, is_property: bool = False) -> Validator:
    if "$ref" in schema:
        components = COMPONENTS.get()
        if not components:
            raise Exception("file with components definitions is missing")
        # #/components/schemas/Pet
        *_, section, obj = schema["$ref"].split("/")
        schema = components[section][obj]

    if not any(field in schema for field in ("oneOf", "anyOf", "allOf")):
        return _type_to_validator(schema, is_property=is_property)

    if "oneOf" in schema:
        cls: Type[Union[OneOf, AnyOf]] = OneOf
        type_ = "oneOf"
    elif "anyOf" in schema:
        cls = AnyOf
        type_ = "anyOf"
    else:
        return AllOf(
            nullable=schema.get("nullable", False),
            validators=[schema_to_validator(sch) for sch in schema["allOf"]],
        )

    validators = []
    discriminator = schema.get("discriminator")
    mapping: Dict[str, int] = {}
    schema_names: Set[str] = set()
    for i, sch in enumerate(schema[type_]):
        validators.append(schema_to_validator(sch))
        if discriminator is not None and "$ref" in sch:
            # #/components/schemas/Pet
            *_, obj = sch["$ref"].split("/")
            mapping[obj] = i
            schema_names.add(obj)
    if discriminator is not None and "mapping" in discriminator:
        for key, value in discriminator["mapping"].items():
            if value.startswith("#"):
                value = value.split("/")[-1]
                discriminator["mapping"][key] = value
            if value not in schema_names:
                raise Exception(f"schema '{value}' must be defined in components")
    return cls(
        nullable=schema.get("nullable", False),
        validators=[schema_to_validator(sch) for sch in schema[type_]],
        discriminator=schema.get("discriminator"),
        mapping=mapping,
    )


def _security_to_validator(sec_name: str, components: Dict) -> Validator:
    if sec_name not in components["securitySchemes"]:
        raise Exception(f"security schema {sec_name} must be defined in components")
    sec_def = components["securitySchemes"][sec_name]
    if sec_def["type"] == "http":
        if sec_def["scheme"] == "basic":
            return AuthBasic()
        if sec_def["scheme"] == "bearer":
            return AuthBearer()
        raise Exception(f"Unknown scheme {sec_def['scheme']} in {sec_name}")
    if sec_def["type"] == "apiKey":
        if sec_def["in"] == "header":
            return AuthApiKeyHeader(name=sec_def["name"].lower())
        if sec_def["in"] == "query":
            return AuthApiKeyQuery(name=sec_def["name"])
        if sec_def["in"] == "cookie":
            return AuthApiKeyCookie(name=sec_def["name"])
        raise Exception(f"Unknown value of in {sec_def['in']} in {sec_name}")
    raise Exception(f"Unsupported auth type {sec_def['type']}")


def security_to_validator(schema: List[Dict]) -> Validator:
    components = COMPONENTS.get()
    if "securitySchemes" not in components:
        raise Exception("securitySchemes must be defined in components")
    if len(schema) > 1:
        validators = []
        for security in schema:
            if len(security) > 1:
                validator: Validator = AllOfAuth(
                    validators=[_security_to_validator(sec_name, components) for sec_name in security]
                )
            elif len(security) == 1:
                validator = _security_to_validator(next(iter(security)), components)
            else:
                validator = AuthNone()
            validators.append(validator)
        return AnyOfAuth(validators=validators)

    security = schema[0]
    if len(security) == 1:
        return _security_to_validator(next(iter(security)), components)
    return AllOfAuth(validators=[_security_to_validator(sec_name, components) for sec_name in security])
