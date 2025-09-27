from functools import partial
from typing import Annotated, Any, Callable, ClassVar, Dict, List, Optional, Tuple

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from glotter.errors import (
    get_error_details,
    raise_simple_validation_error,
    raise_validation_errors,
    validate_str_list,
)
from glotter.utils import indent, quote

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
                raise_simple_validation_error(cls, "Too few items", value)

            if len(value) > 1:
                raise_simple_validation_error(cls, "Too many items", value)

            key, item = tuple(*value.items())
            if key == "exec":
                if not isinstance(item, str):
                    raise_simple_validation_error(
                        cls, "Input should be a valid string", item, (key,)
                    )
                if not item:
                    raise_simple_validation_error(cls, "Value must not be empty", item, (key,))
            elif key != "self":
                raise_simple_validation_error(cls, 'Invalid "expected" type', item)
        elif isinstance(value, list):
            validate_str_list(cls, value)
        elif not isinstance(value, str):
            raise_simple_validation_error(
                cls, "Input should be a valid string, list, or dictionary", value
            )

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


def _append_method_to_actual(method: str, actual_var: str, expected_var) -> Tuple[str, str]:
    return f"{actual_var}.{method}()", expected_var


def _append_method_to_expected(method: str, actual_var: str, expected_var: str) -> Tuple[str, str]:
    return actual_var, f"{expected_var}.{method}()"


def _remove_chars(values: List[str], actual_var: str, expected_var: str) -> Tuple[str, str]:
    for value in values:
        actual_var += f'.replace({quote(value)}, "")'

    return actual_var, expected_var


def _strip_chars(values: List[str], actual_var: str, expected_var: str) -> Tuple[str, str]:
    for value in values:
        actual_var += f".strip({quote(value)})"

    return actual_var, expected_var


def _unique_sort(actual_var, expected_var):
    return f"sorted(set({actual_var}))", f"sorted(set({expected_var}))"


class AutoGenTest(BaseModel):
    """Object used to auto-generated a test"""

    name: Annotated[str, Field(strict=True, min_length=1, pattern="^[a-zA-Z][0-9a-zA-Z_]*$")]
    requires_parameters: bool = False
    inputs: Annotated[List[str], Field(strict=True, min_length=1)] = Field(
        ["Input"], validate_default=True
    )
    params: Annotated[List[AutoGenParam], Field(strict=True, min_length=1)] = Field(
        None, validate_default=True
    )
    transformations: List[Any] = []

    SCALAR_TRANSFORMATION_FUNCS: ClassVar[Dict[str, TransformationScalarFuncT]] = {
        "strip": partial(_append_method_to_actual, "strip"),
        "splitlines": partial(_append_method_to_actual, "splitlines"),
        "lower": partial(_append_method_to_actual, "lower"),
        "any_order": _unique_sort,
        "strip_expected": partial(_append_method_to_expected, "strip"),
        "splitlines_expected": partial(_append_method_to_expected, "splitlines"),
    }
    DICT_TRANSFORMATION_FUNCS: ClassVar[Dict[str, TransformationDictFuncT]] = {
        "remove": _remove_chars,
        "strip": _strip_chars,
    }

    @field_validator("inputs", mode="before")
    @classmethod
    def validate_inputs(cls, values):
        """
        Validate each input

        :param values: Inputs to validate
        :return: Original inputs
        :raises: :exc:`ValidationError` if input invalid
        """

        validate_str_list(cls, values)
        return values

    @field_validator("params", mode="before")
    @classmethod
    def validate_params(cls, values, info: ValidationInfo):
        """
        Validate each parameter

        :param values: Parameters to validate
        :param info: Test item
        :return: Original parameters
        :raises: :exc:`ValidationError` if project requires parameters but no input, no name,
            or empty name. Also, raised if no expected output
        """

        errors = []
        field_is_required = "Field is required when parameters required"

        for index, value in enumerate(values):
            if info.data.get("requires_parameters"):
                if not isinstance(value, dict):
                    errors.append(
                        get_error_details("Input should be a valid dictionary", (index,), value)
                    )
                    continue

                if "name" not in value:
                    errors.append(get_error_details(field_is_required, (index, "name"), value))
                elif isinstance(value["name"], str) and not value["name"]:
                    errors.append(
                        get_error_details(
                            "Value must not be empty when parameters required",
                            (index, "name"),
                            value,
                        )
                    )

                if "input" not in value:
                    errors.append(get_error_details(field_is_required, (index, "input"), value))

            if "expected" not in value:
                errors.append(get_error_details(field_is_required, (index, "expected"), value))

        if errors:
            # Collect inner errors
            for index, value in enumerate(values):
                if not isinstance(value, dict):
                    continue

                try:
                    AutoGenParam.model_validate(value)
                except ValidationError as exc:
                    for err in exc.errors():
                        loc = (index,) + tuple(err.get("loc", ()))
                        msg = err.get("msg") or str(err.get("type", "value_error"))
                        input_val = err.get("input", value)
                        errors.append(get_error_details(msg, loc, input_val))

            raise_validation_errors(cls, errors)

        return values

    @field_validator("transformations", mode="before")
    @classmethod
    def validate_transformation(cls, values):
        """
        Validate each transformation

        :param values: Transformations to validate
        :return: Original values
        :raises: :exc:`ValidationError` if Invalid transformation
        """

        if not isinstance(values, list):
            raise_simple_validation_error(cls, "Input should be a valid list", values)

        errors = []
        for index, value in enumerate(values):
            if isinstance(value, str):
                if value not in cls.SCALAR_TRANSFORMATION_FUNCS:
                    errors.append(
                        get_error_details(f'Invalid transformation "{value}"', (index,), value)
                    )
            elif isinstance(value, dict):
                key = str(*value)
                if key not in cls.DICT_TRANSFORMATION_FUNCS:
                    errors.append(
                        get_error_details(f'Invalid transformation "{key}"', (index,), value)
                    )
                else:
                    errors += validate_str_list(cls, value[key], (index, key), raise_exc=False)
            else:
                errors.append(
                    get_error_details(
                        "Input should be a valid string or dictionary", (index,), value
                    )
                )

        if errors:
            raise_validation_errors(cls, errors)

        return values

    def transform_vars(self) -> Tuple[str, str]:
        """
        Transform variables using the specified transformations

        :return: Transformed actual and expected variables
        """

        actual_var = "actual"
        expected_var = "expected"
        for transfomation in self.transformations:
            if isinstance(transfomation, str):
                actual_var, expected_var = self.SCALAR_TRANSFORMATION_FUNCS[transfomation](
                    actual_var, expected_var
                )
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
        test_code += indent(_get_assert(actual_var, expected_var, self.params[0].expected), 4)
        return test_code


def _get_expected_file(project_name_underscores: str, expected_output: Dict[str, str]) -> str:
    if "exec" in expected_output:
        script = quote(expected_output["exec"])
        return f"expected = {project_name_underscores}.exec({script})\n"

    test_code = f"""\
with open({project_name_underscores}.full_path, "r", encoding="utf-8") as file:
    expected = file.read()
"""

    if "self" in expected_output:
        test_code += """\
diff_len = len(actual) - len(expected)
if diff_len > 0:
    expected += "\\n"
elif diff_len < 0:
    actual += "\\n"
"""

    return test_code


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
    search: Annotated[str, Field(strict=True, pattern="^[0-9a-zA-Z_]*$")] = ""
    replace: Annotated[str, Field(strict=True, pattern="^[0-9a-zA-Z_]*$")] = ""

    @model_validator(mode="before")
    @classmethod
    def validate_search_with_replace(cls, values):
        """
        Validate that if either search or replace is specified, both must be specified

        :param values: Values to validate
        :return: Original values
        :raise: `exc`:ValidationError if either search or replace is specified, both are specified
        """

        if "search" in values and "replace" not in values:
            raise_simple_validation_error(
                cls, '"search" item specified without "replace" item', values
            )

        if "search" not in values and "replace" in values:
            raise_simple_validation_error(
                cls, '"replace" item specified without "search" item', values
            )

        return values
