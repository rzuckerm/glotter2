from typing import Annotated, ClassVar, Dict, List, Optional

from glotter_core.project import AcronymScheme, CoreProjectMixin
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from glotter.auto_gen_test import AutoGenTest, AutoGenUseTests
from glotter.errors import raise_simple_validation_error, validate_str_dict, validate_str_list


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

        return {
            test_name: {
                **test,
                "requires_parameters": info.data.get("requires_parameters") or False,
                "strings": info.data.get("strings") or {},
                "name": test_name,
            }
            for test_name, test in value.items()
        }

    def set_tests(self, project: "Project"):
        """
        If there is a "use_tests" item, then set the specified tests, renaming them
        according to the "use_tests" item. The "use_tests" item is then removed

        :params tests: Project with tests to use
        """

        if self.use_tests:
            self.tests = {}
            for test_name_, test in project.tests.items():
                test_name = test_name_.replace(self.use_tests.search, self.use_tests.replace)
                self.tests[test_name] = AutoGenTest(
                    **test.model_dump(exclude={"name"}), name=test_name
                )

            self.requires_parameters = project.requires_parameters
            self.use_tests = None
