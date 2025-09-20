from typing import Any, Callable, List, Optional, Tuple

from pydantic import (
    BaseModel,
    ValidationError,
    field_validator,
)

from glotter.utils import get_error_details, quote, raise_simple_validation_error

TransformationScalarFuncT = Callable[[str, str], Tuple[str, str]]
TransformationDictFuncT = Callable[[List[str], str, str], Tuple[str, str]]


class AutoGenParam(BaseModel):
    """Object used to auto-generated a test parameter"""

    name: str = ""
    input: Optional[str] = None
    expected: Any

    @field_validator("expected")
    def validate_expected(cls, value):
        """
        Validate expected value

        :param value: Expected value
        :return: Original expected value
        :raises: :exc:`ValidationError` if invalid expected value
        """

        if isinstance(value, dict):
            if not value:
                raise_simple_validation_error(cls, "too few items", value)

            if len(value) > 1:
                raise_simple_validation_error(cls, "too many items", value)

            key, item = tuple(*value.items())
            if key == "exec":
                if not isinstance(item, str):
                    raise_simple_validation_error(cls, "str type expected", item, (key,))
                if not item:
                    raise_simple_validation_error(cls, "value must not be empty", item, (key,))
            elif key != "self":
                raise_simple_validation_error(cls, 'invalid "expected" type', item)
        elif isinstance(value, list):
            _validate_str_list(cls, value)
        elif not isinstance(value, str):
            raise raise_simple_validation_error(cls, "str, list, or dict type expected", value)

        return value

    def get_pytest_param(self) -> str:
        """
        Get pytest parameter string

        :return: pytest parameter string if name is not empty, empty string otherwise
        """

        if not self.name:
            return ""

        input_param = self.input
        if isinstance(input_param, str):
            input_param = quote(input_param)

        expected_output = self.expected
        if isinstance(expected_output, str):
            expected_output = quote(expected_output)

        return f"pytest.param({input_param}, {expected_output}, id={quote(self.name)}),\n"


def _validate_str_list(cls, values, item_name: str = ""):
    loc = ()
    if item_name:
        loc += (item_name,)

    if not isinstance(values, list):
        errors = [get_error_details("value is not a valid list", loc, values)]
    else:
        errors = [
            get_error_details("str type expected", loc + (index,), value)
            for index, value in enumerate(values)
            if not isinstance(value, str)
        ]

    if errors:
        raise ValidationError.from_exception_data(title=cls.__name__, line_errors=errors)
