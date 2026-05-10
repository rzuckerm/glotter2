from typing import Annotated, ClassVar, Dict, List, Optional

from glotter_core.project import AcronymScheme, CoreProjectMixin
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from glotter.auto_gen_test import AutoGenTest, AutoGenUseTests
from glotter.errors import (
    InitErrorDetails,
    get_error_details,
    raise_simple_validation_error,
    raise_validation_errors,
    validate_str_dict,
    validate_str_list,
)


class Project(BaseModel, CoreProjectMixin):
    VALID_REGEX: ClassVar[str] = "^[0-9a-zA-Z]+$"

    words: Annotated[
        List[Annotated[str, Field(min_length=1, pattern=VALID_REGEX, strict=True)]],
        Field(min_length=1, strict=True),
    ]
    requires_parameters: bool = False
    strings: Dict[str, str] = {}
    acronyms: List[Annotated[str, Field(min_length=1, pattern=VALID_REGEX, strict=True)]] = []
    acronym_scheme: AcronymScheme = AcronymScheme.two_letter_limit
    use_tests: Optional[AutoGenUseTests] = None
    repeat: Dict[str, int] = {}
    tests: Dict[str, AutoGenTest] = {}

    @field_validator("acronyms", mode="before")
    @classmethod
    def get_acronym(cls, values):
        validate_str_list(cls, values)
        return [value.upper() for value in values]

    @field_validator("strings", mode="before")
    @classmethod
    def validate_strings(cls, values):
        validate_str_dict(cls, values)
        return values

    @field_validator("repeat", mode="before")
    @classmethod
    def validate_repeat(cls, values, info: ValidationInfo):
        errors = []
        if not isinstance(values, dict):
            errors.append(get_error_details("Input should be a valid dictionary", (), values))
        else:
            for key, value in values.items():
                if not isinstance(key, str):
                    errors.append(get_error_details("Key should be a valid string", (key,), key))

                if not isinstance(value, int):
                    errors.append(
                        get_error_details("Value should be a valid integer", (key,), value)
                    )
                elif value < 1:
                    errors.append(get_error_details("Value should be at least 1", (key,), value))

        if errors:
            raise_validation_errors(cls, errors)

        return values

    @field_validator("tests", mode="before")
    @classmethod
    def get_tests(cls, value, info: ValidationInfo):
        if not isinstance(value, dict) or not all(
            isinstance(test, dict) for test in value.values()
        ):
            return value

        if info.data.get("use_tests"):
            raise_simple_validation_error(
                cls, '"tests" and "use_tests" items are mutually exclusive', {"use_tests": "..."}
            )

        repeat = info.data.get("repeat") or {}
        _validate_test_keys(cls, value, repeat)

        return {
            test_name: {
                **test,
                "requires_parameters": info.data.get("requires_parameters") or False,
                "strings": info.data.get("strings") or {},
                "name": test_name,
                "repeat": repeat.get(test_name, 1),
            }
            for test_name, test in value.items()
        }

    def set_tests(self, project: "Project") -> List[InitErrorDetails]:
        """
        If there is a "use_tests" item, then set the specified tests, renaming them
        according to the "use_tests" item. The "use_tests" item is then removed

        :params tests: Project with tests to use
        """

        errors = []
        if self.use_tests:
            self.tests = {}
            for test_name_, test in project.tests.items():
                test_name = test_name_.replace(self.use_tests.search, self.use_tests.replace)
                self.tests[test_name] = AutoGenTest(
                    **test.model_dump(exclude={"name", "repeat"}),
                    name=test_name,
                    repeat=self.repeat.get(test_name, 1),
                )

            self.requires_parameters = project.requires_parameters
            self.use_tests = None
            errors += _validate_test_keys(
                self.__class__, self.tests, self.repeat, raise_exc=False
            )

        return errors


def _validate_test_keys(cls, tests, repeat, raise_exc: bool = True) -> List[InitErrorDetails]:
    errors = []
    for test_name in repeat:
        if isinstance(test_name, str) and test_name not in tests:
            errors.append(
                get_error_details(
                    "Refers to a non-existent test name",
                    ("repeat", test_name),
                    test_name,
                )
            )

    if raise_exc and errors:
        raise_validation_errors(cls, errors)

    return errors
