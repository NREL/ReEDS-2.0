from typing import Dict, Union

import attr


@attr.attrs(slots=True, auto_attribs=True)
class ValidatorError(Exception):
    error: Union[str, Dict]


class DiscriminatorValidationError(Exception):
    pass
