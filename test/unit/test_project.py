import string

import pytest
from pydantic import ValidationError

from glotter.project import Project, NamingScheme, AcronymScheme

VALID_CHARS = string.ascii_letters + string.digits
BAD_WORDS = ["a#xyz", "z_x blah", "yoo-hoo"]

project_scheme_permutation_map = [
    {
        "id": "single_word_no_acronym",
        "words": ["word"],
        "acronyms": None,
        "schemes": {
            NamingScheme.hyphen: "word",
            NamingScheme.underscore: "word",
            NamingScheme.camel: "word",
            NamingScheme.pascal: "Word",
            NamingScheme.lower: "word",
        },
    },
    {
        "id": "multiple_words_no_acronym",
        "words": ["multiple", "words"],
        "acronyms": None,
        "schemes": {
            NamingScheme.hyphen: "multiple-words",
            NamingScheme.underscore: "multiple_words",
            NamingScheme.camel: "multipleWords",
            NamingScheme.pascal: "MultipleWords",
            NamingScheme.lower: "multiplewords",
        },
    },
    {
        "id": "single_acronym",
        "words": ["io"],
        "acronyms": ["io"],
        "schemes": {
            NamingScheme.hyphen: "io",
            NamingScheme.underscore: "io",
            NamingScheme.camel: "io",
            NamingScheme.pascal: "IO",
            NamingScheme.lower: "io",
        },
    },
    {
        "id": "multiple_words_with_acronym_at_front",
        "words": ["io", "word"],
        "acronyms": ["io"],
        "schemes": {
            NamingScheme.hyphen: "io-word",
            NamingScheme.underscore: "io_word",
            NamingScheme.camel: "ioWord",
            NamingScheme.pascal: "IOWord",
            NamingScheme.lower: "ioword",
        },
    },
    {
        "id": "multiple_words_with_acronym_in_middle",
        "words": ["words", "io", "multiple"],
        "acronyms": ["io"],
        "schemes": {
            NamingScheme.hyphen: "words-io-multiple",
            NamingScheme.underscore: "words_io_multiple",
            NamingScheme.camel: "wordsIOMultiple",
            NamingScheme.pascal: "WordsIOMultiple",
            NamingScheme.lower: "wordsiomultiple",
        },
    },
    {
        "id": "multiple_words_with_acronym_at_end",
        "words": ["multiple", "words", "io"],
        "acronyms": ["io"],
        "schemes": {
            NamingScheme.hyphen: "multiple-words-io",
            NamingScheme.underscore: "multiple_words_io",
            NamingScheme.camel: "multipleWordsIO",
            NamingScheme.pascal: "MultipleWordsIO",
            NamingScheme.lower: "multiplewordsio",
        },
    },
    {
        "id": "same_acronym_twice",
        "words": ["io", "word", "io"],
        "acronyms": ["io"],
        "schemes": {
            NamingScheme.hyphen: "io-word-io",
            NamingScheme.underscore: "io_word_io",
            NamingScheme.camel: "ioWordIO",
            NamingScheme.pascal: "IOWordIO",
            NamingScheme.lower: "iowordio",
        },
    },
    {
        "id": "multiple_acronyms",
        "words": ["io", "word", "ui"],
        "acronyms": ["ui", "io"],
        "schemes": {
            NamingScheme.hyphen: "io-word-ui",
            NamingScheme.underscore: "io_word_ui",
            NamingScheme.camel: "ioWordUI",
            NamingScheme.pascal: "IOWordUI",
            NamingScheme.lower: "iowordui",
        },
    },
    {
        "id": "multiple_acronyms_together",
        "words": ["word", "io", "ui"],
        "acronyms": ["ui", "io"],
        "schemes": {
            NamingScheme.hyphen: "word-io-ui",
            NamingScheme.underscore: "word_io_ui",
            NamingScheme.camel: "wordIOUI",
            NamingScheme.pascal: "WordIOUI",
            NamingScheme.lower: "wordioui",
        },
    },
]


def get_project_scheme_permutations():
    for perm in project_scheme_permutation_map:
        id_ = perm["id"]
        words = perm["words"]
        acronyms = perm["acronyms"]
        for scheme, expected in perm["schemes"].items():
            yield id_, words, acronyms, scheme, expected


@pytest.mark.parametrize(
    ("words", "acronyms", "scheme", "expected"),
    [perm[1:] for perm in get_project_scheme_permutations()],
    ids=[f"{perm[0]}_{perm[3]}" for perm in get_project_scheme_permutations()],
)
def test_get_project_name_by_scheme(words, acronyms, scheme, expected):
    value = {"words": words}
    if acronyms is not None:
        value["acronyms"] = acronyms

    project = Project(**value)
    actual = project.get_project_name_by_scheme(scheme)
    assert actual == expected


def test_get_project_name_by_scheme_bad():
    project = Project(words=["blah"])
    with pytest.raises(KeyError):
        project.get_project_name_by_scheme("junk")


@pytest.mark.parametrize(
    ("value", "expected_value"),
    [
        pytest.param(
            {"words": [f"{char1}{char2}", f"{char2}{char1}"]},
            {
                "words": [f"{char1}{char2}", f"{char2}{char1}"],
                "requires_parameters": False,
                "acronyms": [],
                "acronym_scheme": AcronymScheme.two_letter_limit,
                "use_tests": None,
                "tests": {},
            },
            id=f"just-words-{char1}{char2}-{char2}{char1}",
        )
        for char1, char2 in zip(VALID_CHARS[::2], VALID_CHARS[1::2])
    ]
    + [
        pytest.param(
            {"words": ["longest", "word"], "requires_parameters": True},
            {
                "words": ["longest", "word"],
                "requires_parameters": True,
                "acronyms": [],
                "acronym_scheme": AcronymScheme.two_letter_limit,
                "use_tests": None,
                "tests": {},
            },
            id="requires-parameters",
        )
    ]
    + [
        pytest.param(
            {
                "words": [
                    "file",
                    "input",
                    "output",
                    f"{char1}{char2}",
                    f"{char2}{char1}",
                ],
                "acronyms": ["file", "io", f"{char1}{char2}", f"{char2}{char1}"],
            },
            {
                "words": [
                    "file",
                    "input",
                    "output",
                    f"{char1}{char2}",
                    f"{char2}{char1}",
                ],
                "requires_parameters": False,
                "acronyms": [
                    "FILE",
                    "IO",
                    f"{char1}{char2}".upper(),
                    f"{char2}{char1}".upper(),
                ],
                "acronym_scheme": AcronymScheme.two_letter_limit,
                "use_tests": None,
                "tests": {},
            },
            id=f"has-acronyms-{char1}{char2}-{char2}{char1}",
        )
        for char1, char2 in zip(VALID_CHARS[::2], VALID_CHARS[1::2])
    ]
    + [
        pytest.param(
            {"words": ["binary", "search"], "acronym_scheme": acronym_scheme.name},
            {
                "words": ["binary", "search"],
                "requires_parameters": False,
                "acronyms": [],
                "acronym_scheme": acronym_scheme,
                "use_tests": None,
                "tests": {},
            },
            id=f"has-acronym-scheme-{acronym_scheme.name}",
        )
        for acronym_scheme in AcronymScheme
    ]
    + [
        pytest.param(
            {
                "words": ["prime", "number"],
                "requires_parameters": True,
                "tests": {
                    "prime_number_valid": {
                        "params": [
                            {"name": "one", "input": "1", "expected": "composite"},
                            {"name": "two", "input": "2", "expected": "prime"},
                        ],
                        "transformations": ["strip", "lower"],
                    },
                    "prime_number_invalid": {
                        "params": [
                            {
                                "name": "no input",
                                "input": None,
                                "expected": "some-usage",
                            },
                            {
                                "name": "empty input",
                                "input": '""',
                                "expected": "some-usage",
                            },
                        ],
                        "transformations": ["strip"],
                    },
                },
            },
            {
                "words": ["prime", "number"],
                "requires_parameters": True,
                "acronyms": [],
                "acronym_scheme": AcronymScheme.two_letter_limit,
                "tests": {
                    "prime_number_valid": {
                        "name": "prime_number_valid",
                        "requires_parameters": True,
                        "params": [
                            {"name": "one", "input": "1", "expected": "composite"},
                            {"name": "two", "input": "2", "expected": "prime"},
                        ],
                        "transformations": ["strip", "lower"],
                    },
                    "prime_number_invalid": {
                        "name": "prime_number_invalid",
                        "requires_parameters": True,
                        "params": [
                            {
                                "name": "no input",
                                "input": None,
                                "expected": "some-usage",
                            },
                            {
                                "name": "empty input",
                                "input": '""',
                                "expected": "some-usage",
                            },
                        ],
                        "transformations": ["strip"],
                    },
                },
                "use_tests": None,
            },
            id="tests",
        ),
    ],
)
def test_good_project(value, expected_value):
    project = Project(**value)
    assert project.dict() == expected_value


@pytest.mark.parametrize(
    ("value", "expected_errors"),
    [
        pytest.param({}, "words\n  field required", id="missing-words"),
        pytest.param(
            {"words": []},
            ["words\n  ensure this value has at least 1 item"],
            id="no-words",
        ),
        pytest.param(
            {"words": ["help", ""]},
            ["words -> 1\n  ensure this value has at least 1 char"],
            id="empty-words",
        ),
    ]
    + [
        pytest.param(
            {"words": [bad_word]},
            ["words -> 0\n  string does not match regex"],
            id=f"bad-words-{bad_word}",
        )
        for bad_word in BAD_WORDS
    ]
    + [
        pytest.param(
            {"words": None}, ["words\n  none is not an allowed"], id="words-none"
        ),
        pytest.param(
            {"words": {"some": "thing"}},
            ["words\n  value is not a valid list"],
            id="words-dict",
        ),
        pytest.param(
            {"words": ["foo"], "acronyms": ["", "foo"]},
            ["acronyms -> 0\n  ensure this value has at least 1 char"],
            id="empty-acronyms",
        ),
    ]
    + [
        pytest.param(
            {"words": ["foo"], "acronyms": ["foo", bad_word]},
            ["acronyms -> 1\n  string does not match regex"],
            id=f"bad-acronyms-{bad_word}",
        )
        for bad_word in BAD_WORDS
    ]
    + [
        pytest.param(
            {"words": ["foo"], "acronyms": None},
            ["acronyms\n  none is not an allowed"],
            id="acronyms-none",
        ),
        pytest.param(
            {"words": ["foo"], "acronyms": {"what": "ever"}},
            ["acronyms\n  value is not a valid list"],
            id="acronyms-dict",
        ),
        pytest.param(
            {"words": ["foo"], "acronyms": ["blah", None]},
            ["acronyms -> 1\n  none is not an allowed"],
            id="acronyms-item-none",
        ),
        pytest.param(
            {"words": ["foo"], "acronym_scheme": "blah"},
            ["acronym_scheme\n  value is not a valid enumeration"],
            id="bad-acronym-scheme",
        ),
        pytest.param(
            {"words": ["foo"], "use_tests": {}},
            ["use_tests -> name\n  field required"],
            id="bad-use-tests",
        ),
        pytest.param(
            {"words": ["foo"], "tests": {"foo": {"params": []}}},
            ["tests -> foo -> params\n  ensure this value has at least 1 item"],
            id="bad-tests",
        ),
        pytest.param(
            {
                "words": ["foo"],
                "tests": {"foo": {"params": [{"expected": "blah"}]}},
                "use_tests": {"name": "bar"},
            },
            ['tests\n  "tests" and "use_tests" items are mutually exclusive'],
            id="tests-and-use-tests",
        ),
        pytest.param(
            {"words": ["foo"], "tests": 1},
            ["tests\n  value is not a valid dict"],
            id="bad-tests-int",
        ),
        pytest.param(
            {
                "words": ["foo"],
                "requires_parameters": True,
                "tests": {
                    "blah": {
                        "params": [
                            {"name": "whatever", "input": None, "expected": "stuff"}
                        ]
                    },
                    "xyz": 32,
                },
            },
            [
                "tests -> blah -> name\n  field required",
                "tests -> xyz\n  value is not a valid dict",
            ],
            id="tests-not-all-dict",
        ),
    ],
)
def test_bad_project(value, expected_errors):
    with pytest.raises(ValidationError) as e:
        Project(**value)

    for expected_error in expected_errors:
        assert expected_error in str(e.value)


@pytest.mark.parametrize(
    ("value", "expected_display_name"),
    [
        pytest.param({"words": ["foo", "bar"]}, "Foo Bar", id="not-in-acronyms"),
        pytest.param(
            {
                "words": ["file", "io", "stuff"],
                "acronyms": ["io", "stuff"],
                "acronym_scheme": "upper",
            },
            "File IO STUFF",
            id="acronym-upper",
        ),
        pytest.param(
            {
                "words": ["file", "io", "stuff"],
                "acronyms": ["io", "stuff"],
                "acronym_scheme": "lower",
            },
            "File io stuff",
            id="acronym-lower",
        ),
        pytest.param(
            {"words": ["some", "xyz"], "acronyms": ["xyz"]},
            "Some Xyz",
            id="acronym-two-letter-limit",
        ),
    ],
)
def test_get_display_name(value, expected_display_name):
    project = Project(**value)
    assert project.display_name == expected_display_name


def test_set_tests():
    valid_tests = {
        "params": [
            {
                "name": "not sorted",
                "input": '"3, 4, 1, 2"',
                "expected": "1, 2, 3, 4",
            },
            {
                "name": "sorted",
                "input": '"1, 2, 3"',
                "expected": "1, 2, 3",
            },
        ],
        "transformations": ["strip"],
    }
    invalid_tests = {
        "params": [
            {"name": "no input", "input": None, "expected": "usage"},
            {"name": "empty input", "input": '""', "expected": "usage"},
        ],
        "transformations": ["strip"],
    }
    use_tests_project = Project(
        **{
            "words": ["selection", "sort"],
            "use_tests": {
                "name": "bubblesort",
                "search": "bubble_sort",
                "replace": "selection_sort",
            },
        },
    )
    project = Project(
        **{
            "words": ["bubble", "sort"],
            "requires_parameters": True,
            "tests": {
                "bubble_sort_valid": valid_tests,
                "bubble_sort_invalid": invalid_tests,
            },
        }
    )

    use_tests_project.set_tests(project)

    expected_project = {
        "words": ["selection", "sort"],
        "requires_parameters": True,
        "acronyms": [],
        "acronym_scheme": AcronymScheme.two_letter_limit,
        "tests": {
            "selection_sort_valid": {
                **valid_tests,
                "name": "selection_sort_valid",
                "requires_parameters": True,
            },
            "selection_sort_invalid": {
                **invalid_tests,
                "name": "selection_sort_invalid",
                "requires_parameters": True,
            },
        },
        "use_tests": None,
    }
    assert use_tests_project.dict() == expected_project


def test_set_tests_no_use_tests():
    project = Project(
        **{"words": ["foo"], "tests": {"valid": {"params": [{"expected": "blah"}]}}}
    )
    expected_project = project.copy()

    other_project = Project(
        **{
            "words": ["bar"],
            "tests": {"not_valid": {"params": [{"expected": "not blah"}]}},
        }
    )
    project.set_tests(other_project)
    assert project == expected_project
