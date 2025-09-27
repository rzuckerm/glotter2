from typing import List, NoReturn, Optional

from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError


def get_error_details(msg: str, loc: tuple, input) -> InitErrorDetails:
    return InitErrorDetails(
        type=PydanticCustomError("value_error", msg),
        loc=loc,
        input=input,
    )


def raise_simple_validation_error(cls, msg, input, loc: Optional[tuple] = None) -> NoReturn:
    raise ValidationError.from_exception_data(
        title=cls.__name__,
        line_errors=[get_error_details(msg, loc or (), input)],
    )


def raise_validation_errors(cls, errors: List[InitErrorDetails]) -> NoReturn:
    raise ValidationError.from_exception_data(title=cls.__name__, line_errors=errors)


def validate_str_list(
    cls, values, item_loc: Optional[tuple] = None, raise_exc: bool = True
) -> List[InitErrorDetails]:
    loc = item_loc or ()
    errors = []
    if not isinstance(values, list):
        errors += [get_error_details("Input should be a valid list", loc, values)]
    else:
        errors += [
            get_error_details("Input should be a valid string", loc + (index,), value)
            for index, value in enumerate(values)
            if not isinstance(value, str)
        ]

    if errors and raise_exc:
        raise_validation_errors(cls, errors)

    return errors
