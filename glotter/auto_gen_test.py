# pylint hates pydantic
# pylint: disable=E0213,E0611
from typing import Optional, List, Dict, Tuple, Union, Any, Callable, ClassVar
from functools import partial

from pydantic import BaseModel, validator, constr, conlist

from glotter.utils import quote, indent

ExpectedT = Union[str, List[str], Dict[str, str]]

TransformationT = Union[str, Dict[str, List[str]]]
TransformationScalarFuncT = Callable[[str, str], Tuple[str, str]]
TransformationDictFuncT = Callable[[List[str], str, str], Tuple[str, str]]


class AutoGenParam(BaseModel):
    """Object used to auto-generated a test parameter"""

    name: str = ""
    input: Optional[str] = None
    expected: ExpectedT

    @validator("expected")
    def validate_expected(cls, value: ExpectedT) -> ExpectedT:
        """
        Validate expected value

        :param value: Expected value
        :return: Original expected value
        :raises: :exc:`ValueError` if invalid expected value
        """

        if isinstance(value, dict):
            if not value:
                raise ValueError('Too few "expected" items')

            if len(value) > 1:
                raise ValueError('Too many "expected" items')

            key, item = tuple(*value.items())
            if key == "exec":
                if not item:
                    raise ValueError('No value for "exec" item in "expected"')
            elif key != "self":
                raise ValueError(f'Invalid key "{key}" in "expected" item')

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
    """Object use to auto-generated a test"""

    name: constr(min_length=1, regex="^[a-zA-Z][0-9a-zA-Z_]*$")
    requires_parameters: bool = False
    params: conlist(AutoGenParam, min_items=1)
    transformations: List[TransformationT] = []

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

    @validator("params", each_item=True, pre=True)
    def validate_params(
        cls, value: Dict[str, Any], values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate each parameter

        :param value: Parameter to validate
        :param values: Test item
        :return: Original parameter
        :raises: :exc:`ValueError` if project requires parameters but no input, no name,
            or empty name
        """

        if values.get("requires_parameters"):
            if "input" not in value:
                raise ValueError(
                    'This project requires parameters, but "input" is not specified'
                )

            if "name" not in value:
                raise ValueError(
                    'This project requires parameters, but "name" is not specified'
                )

            if not value["name"]:
                raise ValueError(
                    'This project requires parameters, but "name" is empty'
                )

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
                raise ValueError(f'Invalid transformation "{value}"')
        elif isinstance(value, dict):
            key = str(*value)
            if key not in cls.DICT_TRANSFORMATION_FUNCS:
                raise ValueError(f'Invalid transformation "{key}"')
        else:
            raise ValueError(
                f'Invalid transformation data type "{type(value).__name__}"'
            )

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


def _get_assert(actual_var: str, expected_var: str, expected_output: ExpectedT) -> str:
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
