import base64
import ipaddress
import re
import uuid

from rfc3339_validator import validate_rfc3339

from .exceptions import ValidatorError

_EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
_HOSTNAME_REGEX = re.compile(r"(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)


def sf_uuid_validator(value: str) -> None:
    try:
        uuid.UUID(value)
    except ValueError:
        raise ValidatorError("value should be uuid")


def sf_date_validator(value: str) -> None:
    if not validate_rfc3339(f"{value}T00:00:00Z"):
        raise ValidatorError("value should be date format")


def sf_date_time_validator(value: str) -> None:
    if not validate_rfc3339(value):
        raise ValidatorError("value should be datetime format")


def sf_email_validator(value: str) -> None:
    if not _EMAIL_REGEX.match(value):
        raise ValidatorError("value should be valid email")


def sf_byte_validator(value: str) -> None:
    try:
        base64.b64decode(value)
    except ValueError:
        raise ValidatorError("value should be base64-encoded string")


def sf_ipv4_validator(value: str) -> None:
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        raise ValidatorError("value should be valid ipv4 address")


def sf_ipv6_validator(value: str) -> None:
    try:
        ipaddress.IPv6Address(value)
    except ValueError:
        raise ValidatorError("value should be valid ipv6 address")


def sf_hostname_validator(value: str) -> None:
    if not value:
        raise ValidatorError("value should be valid hostname")
    hostname = value[:-1] if value[-1] == "." else value
    if len(hostname) > 255 or not all(_HOSTNAME_REGEX.match(x) for x in hostname.split(".")):
        raise ValidatorError("value should be valid hostname")
