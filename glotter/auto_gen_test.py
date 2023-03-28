# pylint hates pydantic
# pylint: disable=E0213,E0611
from typing import Optional, List, Dict, Tuple, Callable, ClassVar, Any
from functools import partial

from pydantic import (
    BaseModel,
    validator,
    root_validator,
    constr,
    conlist,
    ValidationError,
)
from pydantic.error_wrappers import ErrorWrapper

from glotter.utils import quote, indent

TransformationScalarFuncT = Callable[[str, str], Tuple[str, str]]
TransformationDictFuncT = Callable[[List[str], str, str], Tuple[str, str]]


class AutoGenParam(BaseModel):
    """Object used to auto-generated a test parameter"""

    name: str = ""
    input: Optional[str] = None
    expected: Any

    @validator("expected")
    def validate_expected(cls, value):
        """
        Validate expected value

        :param value: Expected value
        :return: Original expected value
        :raises: :exc:`ValueError` if invalid expected value
        """

        if isinstance(value, dict):
            if not value:
                raise ValueError("too few items")

            if len(value) > 1:
                raise ValueError("too many items")

            key, item = tuple(*value.items())
            if key == "exec":
                if not isinstance(item, str):
                    raise ValidationError(
                        [
                            ErrorWrapper(ValueError("str type expected"), loc="exec"),
                        ],
                        model=cls,
                    )
                if not item:
                    raise ValidationError(
                        [
                            ErrorWrapper(
                                ValueError("value must not be empty"), loc="exec"
                            )
                        ],
                        model=cls,
                    )
            elif key != "self":
                raise ValueError('invalid "expected" type')
        elif isinstance(value, list):
            _validate_str_list(cls, value)
        elif not isinstance(value, str):
            raise ValueError("str, list, or dict type expected")

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

        return (
            f"pytest.param({input_param}, {expected_output}, id={quote(self.name)}),\n"
        )


def _validate_str_list(cls, values, item_name: str = ""):
    loc = ()
    if item_name:
        loc += (item_name,)

    if not isinstance(values, list):
        errors = [ErrorWrapper(ValueError("value is not a valid list"), loc=loc)]
    else:
        errors = [
            ErrorWrapper(ValueError("str type expected"), loc=loc + (index,))
            for index, value in enumerate(values)
            if not isinstance(value, str)
        ]

    if errors:
        raise ValidationError(errors, model=cls)


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


class AutoGenTest(BaseModel):
    """Object used to auto-generated a test"""

    name: constr(strict=True, min_length=1, regex="^[a-zA-Z][0-9a-zA-Z_]*$")
    requires_parameters: bool = False
    inputs: conlist(str, min_items=1) = ["Input"]
    params: conlist(AutoGenParam, min_items=1)
    transformations: List[Any] = []

    SCALAR_TRANSFORMATION_FUNCS: ClassVar[Dict[str, TransformationScalarFuncT]] = {
        "strip": partial(_append_method_to_actual, "strip"),
        "splitlines": partial(_append_method_to_actual, "splitlines"),
        "lower": partial(_append_method_to_actual, "lower"),
        "any_order": _unique_sort,
        "strip_expected": partial(_append_method_to_expected, "strip"),
    }
    DICT_TRANSFORMATION_FUNCS: ClassVar[Dict[str, TransformationDictFuncT]] = {
        "remove": _remove_chars,
        "strip": _strip_chars,
    }

    @validator("inputs", each_item=True, pre=True, always=True)
    def validate_inputs(cls, value):
        """
        Validate each input

        :param value: Input to validate
        :return: Original input
        :raises: :exc:`ValueError` if input invalid
        """

        if not isinstance(value, str):
            raise ValueError("input is not a str")

        return value

    @validator("params", each_item=True, pre=True, always=True)
    def validate_params(cls, value, values):
        """
        Validate each parameter

        :param value: Parameter to validate
        :param values: Test item
        :return: Original parameter
        :raises: :exc:`ValueError` if project requires parameters but no input, no name,
            or empty name
        """

        if values.get("requires_parameters"):
            errors = []
            if "name" not in value:
                errors.append(
                    ErrorWrapper(
                        ValueError("field is required when parameters required"),
                        loc="name",
                    )
                )
            elif isinstance(value["name"], str) and not value["name"]:
                errors.append(
                    ErrorWrapper(
                        ValueError("value must not be empty when parameters required"),
                        loc="name",
                    )
                )

            if "input" not in value:
                errors.append(
                    ErrorWrapper(
                        ValueError("field is required when parameters required"),
                        loc="input",
                    )
                )

            if "expected" not in value:
                errors.append(
                    ErrorWrapper(
                        ValueError("field is required when parameters required"),
                        loc="expected",
                    )
                )

            if errors:
                raise ValidationError(errors, model=cls)

        return value

    @validator("transformations", each_item=True, pre=True)
    def validate_transformation(cls, value):
        """
        Validate each transformation

        :param value: Transformation to validate
        :return: Original value
        :raises: :exc:`ValueError` if invalid transformation
        """

        if isinstance(value, str):
            if value not in cls.SCALAR_TRANSFORMATION_FUNCS:
                raise ValueError(f'invalid transformation "{value}"')
        elif isinstance(value, dict):
            key = str(*value)
            if key not in cls.DICT_TRANSFORMATION_FUNCS:
                raise ValueError(f'invalid transformation "{key}"')

            _validate_str_list(cls, value[key], key)
        else:
            raise ValueError("str or dict type expected")

        return value

    def transform_vars(self) -> Tuple[str, str]:
        """
        Transform variables using the specified transformations

        :return: Transformed actual and expected variables
        """

        actual_var = "actual"
        expected_var = "expected"
        for transfomation in self.transformations:
            if isinstance(transfomation, str):
                actual_var, expected_var = self.SCALAR_TRANSFORMATION_FUNCS[
                    transfomation
                ](actual_var, expected_var)
            else:
                key, item = tuple(*transfomation.items())
                actual_var, expected_var = self.DICT_TRANSFORMATION_FUNCS[key](
                    item, actual_var, expected_var
                )

        return actual_var, expected_var

    def get_pytest_params(self) -> str:
        """
        Get pytest parameters

        :return: pytest parameters
        """

        if not self.requires_parameters:
            return ""

        pytest_params = "".join(
            indent(param.get_pytest_param(), 8) for param in self.params
        ).strip()
        return f"""\
@pytest.mark.parametrize(
    ("in_params", "expected"),
    [
        {pytest_params}
    ]
)
"""

    def get_test_function_and_run(self, project_name_underscores: str) -> str:
        """
        Get test function and run command

        :param project_name_underscores: Project name with underscores between each word
        :return: Test function and run command
        """

        func_params = ""
        run_param = ""
        if self.requires_parameters:
            func_params = "in_params, expected, "
            run_param = "params=in_params"

        return f"""\
def test_{self.name}({func_params}{project_name_underscores}):
    actual = {project_name_underscores}.run({run_param})
"""

    def get_expected_output(self, project_name_underscores: str) -> str:
        """
        Get test code that gets the expected output

        :param project_name_underscores: Project name with underscores between each word
        :return: Test code that gets the expected output

        """

        if self.requires_parameters:
            return ""

        expected_output = self.params[0].expected
        if isinstance(expected_output, str):
            expected_output = quote(expected_output)
        elif isinstance(expected_output, dict):
            return _get_expected_file(project_name_underscores, expected_output)

        return f"expected = {expected_output}\n"

    def generate_test(self, project_name_underscores: str) -> str:
        """
        Generate test code

        :param project_name_underscores: Project name with underscores between each word
        :return: Test code
        """

        test_code = "@project_test(PROJECT_NAME)\n"
        test_code += self.get_pytest_params()
        test_code += self.get_test_function_and_run(project_name_underscores)
        test_code += indent(self.get_expected_output(project_name_underscores), 4)
        actual_var, expected_var = self.transform_vars()
        test_code += indent(
            _get_assert(actual_var, expected_var, self.params[0].expected), 4
        )
        return test_code


def _get_expected_file(
    project_name_underscores: str, expected_output: Dict[str, str]
) -> str:
    if "exec" in expected_output:
        script = quote(expected_output["exec"])
        return f"expected = {project_name_underscores}.exec({script})\n"

    return f"""\
with open({project_name_underscores}.full_path, "r", encoding="utf-8") as file:
    expected = file.read()
"""


def _get_assert(actual_var: str, expected_var: str, expected_output) -> str:
    if isinstance(expected_output, list):
        return f"""\
actual_list = {actual_var}
expected_list = {expected_var}
assert len(actual_list) == len(expected_list), "Length not equal"
for index in range(len(expected_list)):
    assert actual_list[index] == expected_list[index], f"Item {{index + 1}} is not equal"
"""

    test_code = ""
    if actual_var != "actual":
        test_code += f"actual = {actual_var}\n"

    if expected_var != "expected":
        test_code += f"expected = {expected_var}\n"

    return f"{test_code}assert actual == expected\n"


class AutoGenUseTests(BaseModel):
    """Object used to specify what tests to use"""

    name: str
    search: constr(strict=True, regex="^[0-9a-zA-Z_]*$") = ""
    replace: constr(strict=True, regex="^[0-9a-zA-Z_]*$") = ""

    @root_validator(pre=True)
    def validate_search_with_replace(cls, values):
        """
        Validate that if either search or replace is specified, both must be specified

        :param values: Values to validate
        :return: Original values
        :raise: `exc`:ValueError if either search or replace is specified, both are specified
        """

        if "search" in values and "replace" not in values:
            raise ValueError('"search" item specified without "replace" item')

        if "search" not in values and "replace" in values:
            raise ValueError('"replace" item specified without "search" item')

        return values
