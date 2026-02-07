import sys
from unittest.mock import patch

import pytest

from glotter.__main__ import main
from glotter.source import BAD_SOURCES


def test_check_no_errors(mock_get_sources, mock_settings, mock_sources, capsys):
    mock_get_sources.return_value = {**mock_sources, BAD_SOURCES: []}

    with pytest.raises(SystemExit) as e:
        call_check()

    assert e.value.code == 0

    output = capsys.readouterr().out
    assert "All filenames correspond to valid projects" in output


def test_check_errors(mock_get_sources, mock_settings, mock_sources, capsys):
    mock_get_sources.return_value = {
        **mock_sources,
        BAD_SOURCES: ["stuff/nonsense", "garbage/blah", "junk/whatever"],
    }

    with pytest.raises(SystemExit) as e:
        call_check()

    assert e.value.code != 0

    output = capsys.readouterr().out
    expected_output = """\
- garbage/blah
- junk/whatever
- stuff/nonsense
"""
    assert expected_output in output


def call_check(args=None):
    args = args or []
    with patch.object(sys, "argv", ["glotter", "check"] + args):
        main()


class MockArgs:
    pass


@pytest.fixture()
def mock_get_sources():
    with patch("glotter.check.get_sources") as mock:
        yield mock


@pytest.fixture()
def mock_settings():
    with patch("glotter.test_doc_generator.get_settings") as mock:
        yield mock
