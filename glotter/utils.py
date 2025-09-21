import sys
from typing import List, NoReturn, Optional

from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError


def quote(value: str) -> str:
    """
    Enclose a value in quotes

    :param value: Value to enclosed
    :return: Quoted value

    """

    if '"' in value:
        if "'" in value:
            quote_chars = '"""'
            if value.startswith('"'):
                value = f"\\{value}"

            if value.endswith('"'):
                value = f'{value[:-1]}\\"'
        else:
            quote_chars = "'"
    else:
        quote_chars = '"'

    return f"{quote_chars}{value}{quote_chars}"


def indent(value: str, num_spaces: int) -> str:
    """
    Indent each line of a string by a specified number of spaces

    :param value: String to indent
    :param num_spaces: Number of spaces to indent
    :return: Indented string
    """

    spaces = " " * num_spaces
    return "".join(f"{spaces}{line}" for line in value.splitlines(keepends=True))


def error_and_exit(msg):
    print(msg)
    sys.exit(1)


def raise_simple_validation_error(cls, msg, input, loc: Optional[tuple]=None) -> NoReturn:
    raise ValidationError.from_exception_data(
        title=cls.__name__,
        line_errors=[get_error_details(msg, loc or (), input)],
    )


def get_error_details(msg: str, loc: tuple, input) -> InitErrorDetails:
    return InitErrorDetails(
        type=PydanticCustomError("value_error", msg),
        loc=loc,
        input=input,
    )


def raise_validation_errors(cls, errors: List[InitErrorDetails]) -> NoReturn:
    raise ValidationError.from_exception_data(title=cls.__name__, line_errors=errors)
