import os

import pytest

from glotter.source import Source, filter_sources
from glotter.testinfo import TestInfo


def test_full_path(test_info_string_no_build):
    src = Source(
        "name",
        "python",
        os.path.join("this", "is", "a", "path"),
        test_info_string_no_build,
    )
    expected = os.path.join("this", "is", "a", "path", "name")
    actual = src.full_path
    assert actual == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [("name", ""), ("name.ext", ".ext"), ("name.name2.ext", ".ext")],
)
def test_name(name, expected, test_info_string_no_build):
    src = Source(
        name,
        "python",
        os.path.join("this", "is", "a", "path"),
        test_info_string_no_build,
    )
    actual = src.extension
    assert actual == expected


def test_test_info_matches_test_info_string(test_info_string_no_build):
    src = Source(
        "name",
        "python",
        os.path.join("this", "is", "a", "path"),
        test_info_string_no_build,
    )
    expected = TestInfo.from_string(test_info_string_no_build, src)
    actual = src.test_info
    assert actual == expected


def test_build_does_nothing_when_build_is_empty(test_info_string_no_build, monkeypatch):
    monkeypatch.setattr(
        "glotter.containerfactory.ContainerFactory.get_container",
        lambda *args, **kwargs: pytest.fail("get_container was called"),
    )
    src = Source(
        "name",
        "python",
        os.path.join("this", "is", "a", "path"),
        test_info_string_no_build,
    )
    src.build()


def test_build_runs_build_command(factory, source_with_build, monkeypatch, no_io):
    source_with_build.build()
    build_cmd = source_with_build.test_info.container_info.build.strip()
    container = factory.get_container(source_with_build)
    actual = container.execs[0]
    assert actual.cmd.strip() == build_cmd.strip()
    assert not actual["detach"]
    assert actual["workdir"] == "/src"


def test_build_raises_error_on_non_zero_exit_code_from_exec(
    source_with_build, monkeypatch, no_io
):
    monkeypatch.setattr(
        "glotter.source.Source._container_exec",
        lambda *args, **kwargs: (1, "error message".encode("utf-8")),
    )
    with pytest.raises(RuntimeError):
        source_with_build.build()


def test_run_execs_run_command(factory, source_no_build, no_io):
    source_no_build.run()
    run_cmd = source_no_build.test_info.container_info.cmd.strip()
    container = factory.get_container(source_no_build)
    actual = container.execs[0]
    assert actual.cmd.strip() == run_cmd.strip()
    assert not actual["detach"]
    assert actual["workdir"] == "/src"


def test_run_execs_run_command_with_params(factory, source_no_build, no_io):
    params = "-p param1 --longparam"
    source_no_build.run(params=params)
    run_cmd = f"{source_no_build.test_info.container_info.cmd.strip()} {params}"
    container = factory.get_container(source_no_build)
    actual = container.execs[0]
    assert actual.cmd.strip() == run_cmd.strip()
    assert not actual["detach"]
    assert actual["workdir"] == "/src"


def test_run_on_non_zero_exit_code_from_exec_raises_no_error(
    source_no_build, monkeypatch, no_io
):
    monkeypatch.setattr(
        "glotter.source.Source._container_exec",
        lambda *args, **kwargs: (1, "error message".encode("utf-8")),
    )
    source_no_build.run()


def test_exec_runs_command(factory, source_no_build, no_io):
    exec_cmd = "command -p param1 --longparam"
    source_no_build.exec(exec_cmd)
    container = factory.get_container(source_no_build)
    actual = container.execs[0]
    assert actual.cmd.strip() == exec_cmd.strip()
    assert not actual["detach"]
    assert actual["workdir"] == "/src"


def test_exec_on_non_zero_exit_code_raises_no_error(
    source_no_build, monkeypatch, no_io
):
    exec_cmd = "command -p param1 --longparam"
    monkeypatch.setattr(
        "glotter.source.Source._container_exec",
        lambda *args, **kwargs: (1, "error message".encode("utf-8")),
    )
    source_no_build.exec(exec_cmd)


def test_filter_nothing():
    args = MockArgs()
    filtered_sources = filter_sources(args, {})
    assert not filtered_sources


def test_filter_all(mock_sources):
    args = MockArgs()
    filtered_sources = filter_sources(args, mock_sources)
    assert filtered_sources == mock_sources


def test_filter_project(mock_sources):
    args = MockArgs(project="baklava")
    filtered_sources = filter_sources(args, mock_sources)
    assert filtered_sources == {"baklava": mock_sources["baklava"]}


def test_filter_project_not_found(mock_sources, capsys):
    with pytest.raises(SystemExit) as e:
        args = MockArgs(project="bogus")
        filter_sources(args, mock_sources)

    assert e.value.code != 0
    assert 'No valid sources found for project: "bogus"' in capsys.readouterr().out


def test_filter_language(mock_sources):
    args = MockArgs(language="bar")
    filtered_sources = filter_sources(args, mock_sources)
    assert filtered_sources == {
        "baklava": [mock_sources["baklava"][0]],
        "quine": [mock_sources["quine"][0]],
    }


def test_filter_language_not_found(mock_sources, capsys):
    with pytest.raises(SystemExit) as e:
        args = MockArgs(language="foo")
        filter_sources(args, mock_sources)

    assert e.value.code != 0
    assert (
        'No valid sources found for the following combination: language "foo"'
        in capsys.readouterr().out
    )


@pytest.mark.parametrize(
    "source,project,indices",
    [
        ("quine.b", "quine", [0, 1]),
        ("BakLava.b", "baklava", [0, 1]),
        ("File-Input-Output.B", "fileinputoutput", [0]),
    ],
)
def test_filter_source(source, project, indices, mock_sources):
    args = MockArgs(source=source)
    filtered_sources = filter_sources(args, mock_sources)
    assert filtered_sources == {
        project: [mock_sources[project][index] for index in indices]
    }


def test_filter_source_not_found(mock_sources, capsys):
    with pytest.raises(SystemExit) as e:
        args = MockArgs(source="Baklava.foo")
        filter_sources(args, mock_sources)

    assert e.value.code != 0
    assert (
        'No valid sources found for the following combination: source "Baklava.foo"'
        in capsys.readouterr().out
    )


def test_filter_language_and_source(mock_sources):
    args = MockArgs(language="bart", source="baklava.b")
    filtered_sources = filter_sources(args, mock_sources)
    assert filtered_sources == {"baklava": [mock_sources["baklava"][1]]}


def test_filter_language_and_source_not_found(mock_sources, capsys):
    with pytest.raises(SystemExit) as e:
        args = MockArgs(language="bar", source="file-input-output.b")
        filter_sources(args, mock_sources)

    assert e.value.code != 0
    assert (
        'No valid sources found for the following combination: language "bar", '
        'source "file-input-output.b"' in capsys.readouterr().out
    )


def test_filter_project_and_language(mock_sources):
    args = MockArgs(project="quine", language="bar")
    filtered_sources = filter_sources(args, mock_sources)
    assert filtered_sources == {"quine": [mock_sources["quine"][0]]}


def test_filter_project_and_language_not_found(mock_sources, capsys):
    with pytest.raises(SystemExit) as e:
        args = MockArgs(project="baklava", language="cool")
        filter_sources(args, mock_sources)

    assert e.value.code != 0
    assert (
        'No valid sources found for the following combination: project "baklava", '
        'language "cool"' in capsys.readouterr().out
    )


class MockArgs:
    def __init__(self, project="", language="", source=""):
        self.project = project
        self.language = language
        self.source = source
