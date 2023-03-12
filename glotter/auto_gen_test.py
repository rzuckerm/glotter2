# pylint hates pydantic
# pylint: disable=E0213,E0611
from typing import List, Dict, Tuple, Union, Any, Callable
from functools import partial

from pydantic import BaseModel, validator, constr, conlist

from glotter.utils import quote

TransformationFuncT = Callable[[str, str], Tuple[str, str]]


class AutoGenParam(BaseModel):
    """Object used for an auto-generated test parameter"""

    name: constr(min_length=1)
    input: Union[None, str]
    expected: Union[str, List[str], Dict[str, str]]


class AutoGenTest(BaseModel):
    """Object containing information about an auto-generated test"""

    name: constr(min_length=1, regex="^[a-zA-Z][0-9a-zA-Z_]*$")
    requires_parameters: bool = False
    params: conlist(AutoGenParam, min_items=1)
    transformations: List[TransformationFuncT] = []

    @validator("params", each_item=True, pre=True)
    def validate_params(
        cls, value: Dict[str, Any], values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate each parameter

        :param value: Parameter to validate
        :param values: Test item
        :return: Original parameter if project requires parameters. Otherwise, parameter with
            an empty "name" and an "input" of `None`
        :raises: :exc:`ValueError` if project requires parameters but no input
        """

        if values.get("requires_parameters"):
            if "input" not in value:
                raise ValueError(
                    'This project requires parameters, but "input" is not specified'
                )

            return value

        return {**value, "name": value.get("name") or "na", "input": value.get("input")}

    @validator("transformations", each_item=True, pre=True)
    def validate_transformation(cls, value: Any) -> TransformationFuncT:
        """
        Validate each transformation

        :param value: Transformation to validate
        :return: Transformation function
        :raises: :exc:`ValueError` if invalid transformation
        """

        scalar_transformation_funcs = {
            "strip": partial(_append_method_to_actual, "strip"),
            "splitlines": partial(_append_method_to_actual, "splitlines"),
            "lower": partial(_append_method_to_actual, "lower"),
            "any_order": _unique_sort,
            "strip_expected": partial(_append_method_to_expected, "strip"),
        }
        dict_transformation_funcs = {
            "remove": {
                "validator": IsListOfStr,
                "func": _remove_chars,
            },
            "strip": {
                "validator": IsListOfStr,
                "func": _strip_chars,
            },
        }

        try:
            key = value
            if isinstance(value, str):
                return scalar_transformation_funcs[value]
            elif isinstance(value, dict):
                key, item = tuple(*value.items())
                dict_transformation_funcs[key]["validator"](item=item)
                return partial(dict_transformation_funcs[key]["func"], item)
        except KeyError as e:
            raise ValueError(f'Invalid transformation "{key}"') from e

        raise ValueError(f'Invalid transformation data type "{type(value).__name__}"')


class IsListOfStr(BaseModel):
    """Data model to make sure that the transformation value is a list of strings"""

    item: List[str]


def _append_method_to_actual(
    method: str, actual_var: str, expected_var
) -> Tuple[str, str]:
    return f"{actual_var}.{method}()", expected_var


def _append_method_to_expected(
    method: str, actual_var: str, expected_var: str
) -> Tuple[str, str]:
    return actual_var, f"{expected_var}.{method}()"


def _remove_chars(
    values: List[str], actual_var: str, expected_var: str
) -> Tuple[str, str]:
    for value in values:
        actual_var += f'.replace({quote(value)}, "")'

    return actual_var, expected_var


def _strip_chars(
    values: List[str], actual_var: str, expected_var: str
) -> Tuple[str, str]:
    for value in values:
        actual_var += f".strip({quote(value)})"

    return actual_var, expected_var


def _unique_sort(actual_var, expected_var):
    return f"sorted(set({actual_var}))", f"sorted(set({expected_var}))"
