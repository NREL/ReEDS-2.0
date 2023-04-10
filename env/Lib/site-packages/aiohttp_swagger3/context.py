from contextvars import ContextVar
from typing import Dict

COMPONENTS: ContextVar[Dict] = ContextVar("components")
STRING_FORMATS: ContextVar[Dict] = ContextVar("string_formats")
