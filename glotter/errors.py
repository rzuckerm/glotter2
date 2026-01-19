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


def validate_str_dict(
    cls, values, item_loc: Optional[tuple] = None, raise_exc: bool = True
) -> List[InitErrorDetails]:
    loc = item_loc or ()
    errors = []
    if not isinstance(values, dict):
        errors += [get_error_details("Input should be a valid dictionary", loc, values)]
    else:
        errors += sum(
            (
                _get_str_dict_error_details(loc + (key,), key, value)
                for key, value in values.items()
                if not isinstance(key, str) or not isinstance(value, str)
            ),
            [],
        )

    if errors and raise_exc:
        raise_validation_errors(cls, errors)

    return errors


def _get_str_dict_error_details(loc, key, value) -> List[InitErrorDetails]:
    errors = []
    if not isinstance(key, str):
        errors += [get_error_details("Key should be a valid string", loc, key)]

    if not isinstance(value, str):
        errors += [get_error_details("Value should be a valid string", loc, value)]

    return errors
