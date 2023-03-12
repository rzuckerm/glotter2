import pytest

from glotter import utils

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
BACKSLASH = "\\"
TRIPLE_DOUBLE_QUOTE = DOUBLE_QUOTE * 3


@pytest.mark.parametrize(
    ("value", "expected_value"),
    [
        pytest.param("hello", '"hello"', id="no-has-quotes"),
        pytest.param(
            "I can't",
            f"{DOUBLE_QUOTE}I can{SINGLE_QUOTE}t{DOUBLE_QUOTE}",
            id="has-single-quote",
        ),
        pytest.param(
            'Hi "there"',
            f"{SINGLE_QUOTE}Hi {DOUBLE_QUOTE}there{DOUBLE_QUOTE}{SINGLE_QUOTE}",
            id="has-double-quote",
        ),
        pytest.param(
            f"foo{SINGLE_QUOTE}bar{DOUBLE_QUOTE}baz",
            f"{TRIPLE_DOUBLE_QUOTE}foo{SINGLE_QUOTE}bar{DOUBLE_QUOTE}baz{TRIPLE_DOUBLE_QUOTE}",
            id="has-both-middle",
        ),
        pytest.param(
            f"{DOUBLE_QUOTE}whatever{SINGLE_QUOTE}",
            (
                f"{TRIPLE_DOUBLE_QUOTE}{BACKSLASH}{DOUBLE_QUOTE}whatever"
                f"{SINGLE_QUOTE}{TRIPLE_DOUBLE_QUOTE}"
            ),
            id="has-both-double-quote-begin",
        ),
        pytest.param(
            f"{SINGLE_QUOTE}something{SINGLE_QUOTE} {DOUBLE_QUOTE}good{DOUBLE_QUOTE}",
            (
                f"{TRIPLE_DOUBLE_QUOTE}{SINGLE_QUOTE}something{SINGLE_QUOTE} "
                f"{DOUBLE_QUOTE}good{DOUBLE_QUOTE}{TRIPLE_DOUBLE_QUOTE}"
            ),
            id="has-both-double-quote-end",
        ),
    ],
)
def test_quote(value, expected_value):
    assert utils.quote(value) == expected_value


@pytest.mark.parametrize(
    ("value", "num_spaces", "expected_value"),
    [
        pytest.param("Hello", 4, "    Hello", id="single_line-no_newline"),
        pytest.param("Goodbye\n", 8, "        Goodbye\n", id="single_line-newline"),
        pytest.param(
            "Some words\nSome more words",
            4,
            "    Some words\n    Some more words",
            id="multi_line-no_newline",
        ),
        pytest.param(
            "Blah blah\nBlah blah blah\nMore blahs\n",
            2,
            "  Blah blah\n  Blah blah blah\n  More blahs\n",
            id="multi_line-newline",
        ),
    ],
)
def test_indent(value, num_spaces, expected_value):
    assert utils.indent(value, num_spaces) == expected_value
