import argparse
import os
import sys
from unittest.mock import call, patch

import pytest

from glotter.__main__ import main
from glotter.source import Source

LANGUAGES = ["bar", "bart", "cool", "d", "eiffel"]


@pytest.mark.parametrize("num_batches", [-1, 0])
def test_invalid_num_batches(num_batches, mock_download, mock_test, mock_remove, capsys):
    with pytest.raises(SystemExit) as e:
        batch_command(num_batches=num_batches)

    assert e.value.code != 0

    output = capsys.readouterr().out
    assert "Number of batches must be at least 1" in output

    mock_download.assert_not_called()
    mock_test.assert_not_called()
    mock_remove.assert_not_called()


@pytest.mark.parametrize("batch_num,num_batches", [(0, 3), (5, 4)])
def test_invalid_batch_num(batch_num, num_batches, mock_download, mock_test, mock_remove, capsys):
    with pytest.raises(SystemExit) as e:
        batch_command(num_batches=num_batches, batch_num=batch_num)

    assert e.value.code != 0

    output = capsys.readouterr().out
    assert f"Batch number must be from 1 to {num_batches}" in output

    mock_download.assert_not_called()
    mock_test.assert_not_called()
    mock_remove.assert_not_called()


@pytest.mark.parametrize(
    "test_options",
    [
        pytest.param(
            {
                "num_batches": 1,
                "indices": [(0, 5)],
                "exit_codes": [42],
                "expected_exit_code": 42,
            },
            id="num_batches=1",
        ),
        pytest.param(
            {
                "num_batches": 2,
                "indices": [(0, 2), (2, 5)],
                "exit_codes": [0, 13],
                "expected_exit_code": 13,
            },
            id="num_batches=2",
        ),
        pytest.param(
            {
                "num_batches": 3,
                "indices": [(0, 1), (1, 3), (3, 5)],
                "exit_codes": [0, 0, 0],
                "expected_exit_code": 0,
            },
            id="num_batches=2",
        ),
        pytest.param(
            {
                "num_batches": 6,
                "indices": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)],
                "exit_codes": [0, 0, 8, 2, 0],
                "expected_exit_code": 8,
            },
            id="too-many-batches",
        ),
    ],
)
@pytest.mark.parametrize("remove", [True, False])
@pytest.mark.parametrize("parallel", [True, False])
def test_without_batch_num(
    parallel,
    remove,
    test_options,
    mock_download,
    mock_test,
    mock_remove,
    mock_containers,
):
    mock_download.side_effect = [
        dict(mock_containers[start_index:end_index])
        for start_index, end_index in test_options["indices"]
    ]
    mock_test.side_effect = [SystemExit(exit_code) for exit_code in test_options["exit_codes"]]

    with pytest.raises(SystemExit) as e:
        batch_command(num_batches=test_options["num_batches"], parallel=parallel, remove=remove)

    assert e.value.code == test_options["expected_exit_code"]

    expected_batch_args = [
        call(
            mock_batch_args(
                languages=LANGUAGES[start_index:end_index],
                parallel=parallel,
            )
        )
        for start_index, end_index in test_options["indices"]
    ]
    mock_download.assert_has_calls(expected_batch_args)
    mock_test.assert_has_calls(expected_batch_args)
    if remove:
        expected_remove_args = [
            call(dict(mock_containers[start_index:end_index]), parallel)
            for start_index, end_index in test_options["indices"]
        ]
        mock_remove.assert_has_calls(expected_remove_args)
    else:
        mock_remove.assert_not_called()


@pytest.mark.parametrize(
    "test_options",
    [
        pytest.param(
            {
                "num_batches": 3,
                "batch_num": 1,
                "parallel": True,
                "remove": False,
                "exit_code": 0,
                "start_index": 0,
                "end_index": 1,
            },
            id="num_batches=3,batch_num=0",
        ),
        pytest.param(
            {
                "num_batches": 3,
                "batch_num": 2,
                "parallel": False,
                "remove": True,
                "exit_code": 5,
                "start_index": 1,
                "end_index": 3,
            },
            id="num_batches=3,batch_num=1",
        ),
        pytest.param(
            {
                "num_batches": 3,
                "batch_num": 3,
                "parallel": True,
                "remove": True,
                "exit_code": 9,
                "start_index": 3,
                "end_index": 5,
            },
            id="num_batches=3,batch_num=2",
        ),
    ],
)
def test_with_batch_num(test_options, mock_download, mock_test, mock_remove, mock_containers):
    start_index = test_options["start_index"]
    end_index = test_options["end_index"]
    mock_download.return_value = dict(mock_containers[start_index:end_index])
    mock_test.side_effect = SystemExit(test_options["exit_code"])

    with pytest.raises(SystemExit) as e:
        batch_command(
            num_batches=test_options["num_batches"],
            batch_num=test_options["batch_num"],
            parallel=test_options["parallel"],
            remove=test_options["remove"],
        )

    assert e.value.code == test_options["exit_code"]

    expected_mock_batch_args = mock_batch_args(
        languages=LANGUAGES[start_index:end_index],
        parallel=test_options["parallel"],
    )
    mock_download.assert_called_once_with(expected_mock_batch_args)
    mock_test.assert_called_once_with(expected_mock_batch_args)
    if test_options["remove"]:
        expected_remove_args = dict(mock_containers[start_index:end_index])
        mock_remove.assert_called_once_with(expected_remove_args, test_options["parallel"])
    else:
        mock_remove.assert_not_called()


def test_do_nothing_when_no_languages_available(
    mock_download, mock_test, mock_remove, mock_containers
):
    with pytest.raises(SystemExit) as e:
        batch_command(num_batches=6, batch_num=6, remove=True)

    assert e.value.code == 0
    mock_download.assert_not_called()
    mock_test.assert_not_called()
    mock_remove.assert_not_called()


def batch_command(num_batches, batch_num=None, parallel=False, remove=False):
    args = [str(num_batches)]
    if batch_num is not None:
        args += ["--batch", str(batch_num)]

    if parallel:
        args.append("--parallel")

    if remove:
        args.append("--remove")

    with patch.object(sys, "argv", ["glotter", "batch"] + args):
        main()


def mock_batch_args(languages, parallel):
    return argparse.Namespace(source=None, project=None, language=set(languages), parallel=parallel)


@pytest.fixture()
def mock_download():
    with patch("glotter.batch.download") as mock:
        yield mock


@pytest.fixture()
def mock_test():
    with patch("glotter.batch.test") as mock:
        yield mock


@pytest.fixture()
def mock_remove():
    with patch("glotter.batch.remove_images") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_sources_batch(mock_sources, test_info_string_no_build):
    sources = {
        "baklava": mock_sources["baklava"]
        + [
            Source(
                name="baklava.d",
                language="d",
                path=os.path.join("archive", "d", "d", "baklava.d"),
                test_info_string=test_info_string_no_build,
            ),
            Source(
                name="baklava.e",
                language="eiffel",
                path=os.path.join("archive", "e", "eiffel", "baklava.e"),
                test_info_string=test_info_string_no_build,
            ),
        ],
        "fileinputoutput": mock_sources["fileinputoutput"]
        + [
            Source(
                name="file-input-output.d",
                language="d",
                path=os.path.join("archive", "d", "d", "file-input-output.d"),
                test_info_string=test_info_string_no_build,
            ),
        ],
        "quine": mock_sources["quine"]
        + [
            Source(
                name="quine.e",
                language="eiffel",
                path=os.path.join("archive", "e", "eiffel", "quine.e"),
                test_info_string=test_info_string_no_build,
            ),
        ],
    }
    with patch("glotter.batch.get_sources") as mock:
        mock.return_value = sources
        yield mock


@pytest.fixture()
def mock_containers(container_info):
    yield [
        ("bar:1", container_info),
        ("bart:2", container_info),
        ("cool:3", container_info),
        ("d:4", container_info),
        ("eiffel:5", container_info),
    ]
