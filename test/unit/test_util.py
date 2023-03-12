import pytest

from glotter.utils import quote

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
    assert quote(value) == expected_value
