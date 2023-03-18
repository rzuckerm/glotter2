# pylint hates pydantic
# pylint: disable=E0213,E0611
from typing import Dict, Optional, ClassVar
from enum import Enum, auto

from pydantic import BaseModel, validator, conlist, constr

from glotter.auto_gen_test import AutoGenTest, AutoGenUseTests


class NamingScheme(Enum):
    hyphen = auto()
    underscore = auto()
    camel = auto()
    pascal = auto()
    lower = auto()


class AcronymScheme(Enum):
    lower = "lower"
    upper = "upper"
    two_letter_limit = "two_letter_limit"


class Project(BaseModel):
    VALID_REGEX: ClassVar[str] = "^[0-9a-zA-Z]+$"

    words: conlist(constr(min_length=1, regex=VALID_REGEX, strict=True), min_items=1)
    requires_parameters: bool = False
    acronyms: conlist(constr(min_length=1, regex=VALID_REGEX, strict=True)) = []
    acronym_scheme: AcronymScheme = AcronymScheme.two_letter_limit
    use_tests: Optional[AutoGenUseTests] = None
    tests: Dict[str, AutoGenTest] = {}

    @validator("acronyms", pre=True, each_item=True)
    def get_acronym(cls, value):
        if not isinstance(value, str):
            return value

        return value.upper()

    @validator("tests", pre=True)
    def get_tests(cls, value, values):
        if not isinstance(value, dict) or not all(
            isinstance(test, dict) for test in value.values()
        ):
            return value

        if values.get("use_tests"):
            raise ValueError('"tests" and "use_tests" items are mutually exclusive')

        return {
            test_name: {
                **test,
                "requires_parameters": values.get("requires_parameters") or False,
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
            for test_name, test in project.tests.items():
                test_name = test_name.replace(
                    self.use_tests.search, self.use_tests.replace
                )
                self.tests[test_name] = AutoGenTest(
                    **test.dict(exclude={"name"}), name=test_name
                )

            self.requires_parameters = project.requires_parameters
            self.use_tests = None

    @property
    def display_name(self):
        return self._as_display()

    def get_project_name_by_scheme(self, naming):
        """
        gets a project name for a specific naming scheme

        :param naming: the naming scheme
        :return: the project type formatted by the directory's naming scheme
        """
        try:
            return {
                NamingScheme.hyphen: self._as_hyphen(),
                NamingScheme.underscore: self._as_underscore(),
                NamingScheme.camel: self._as_camel(),
                NamingScheme.pascal: self._as_pascal(),
                NamingScheme.lower: self._as_lower(),
            }[naming]
        except KeyError as e:
            raise KeyError(f'Unknown naming scheme "{naming}"') from e

    def _as_hyphen(self):
        return "-".join(
            self._try_as_acronym(word, NamingScheme.hyphen) for word in self.words
        )

    def _as_underscore(self):
        return "_".join(
            self._try_as_acronym(word, NamingScheme.underscore) for word in self.words
        )

    def _as_camel(self):
        return self.words[0].lower() + "".join(
            self._try_as_acronym(word.title(), NamingScheme.camel)
            for word in self.words[1:]
        )

    def _as_pascal(self):
        return "".join(
            self._try_as_acronym(word.title(), NamingScheme.pascal)
            for word in self.words
        )

    def _as_lower(self):
        return "".join(word.lower() for word in self.words)

    def _as_display(self):
        return " ".join(
            self._try_as_acronym(word.title(), NamingScheme.underscore)
            for word in self.words
        )

    def _is_acronym(self, word):
        return word.upper() in self.acronyms

    def _try_as_acronym(self, word, naming_scheme):
        if self._is_acronym(word):
            if self.acronym_scheme == AcronymScheme.upper:
                return word.upper()
            elif self.acronym_scheme == AcronymScheme.lower:
                return word.lower()
            else:
                if len(word) <= 2 and naming_scheme in [
                    NamingScheme.camel,
                    NamingScheme.pascal,
                ]:
                    return word.upper()

        return word
