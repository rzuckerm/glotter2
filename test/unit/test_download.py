from unittest.mock import ANY, call, patch

import pytest

from glotter import download

from .common import set_mock_thread_pool_executor_map


@pytest.mark.parametrize("parallel", [False, True])
def test_download_images(
    parallel, mock_filter_sources, mock_thread_pool_executor, mock_container_factory
):
    mock_map = set_mock_thread_pool_executor_map(mock_thread_pool_executor)

    args = MockArgs(parallel=parallel)
    download.download(args)

    if parallel:
        mock_thread_pool_executor.assert_called_once_with(max_workers=4)
        mock_map.assert_called_once()
    else:
        mock_thread_pool_executor.assert_not_called()

    mock_get_image = mock_container_factory.return_value.get_image
    expected_container_info = get_expected_container_info(mock_filter_sources)
    expected_calls = [call(ci, parallel=ANY) for ci in expected_container_info.values()]
    mock_get_image.assert_has_calls(expected_calls, any_order=True)


@pytest.mark.parametrize("parallel", [False, True])
def test_remove_images(
    parallel, mock_filter_sources, mock_thread_pool_executor, mock_container_factory
):
    mock_map = set_mock_thread_pool_executor_map(mock_thread_pool_executor)

    container_info = get_expected_container_info(mock_filter_sources)
    download.remove_images(containers=container_info, parallel=parallel)

    if parallel:
        mock_thread_pool_executor.assert_called_once_with(max_workers=4)
        mock_map.assert_called_once()
    else:
        mock_thread_pool_executor.assert_not_called()

    mock_remove_image = mock_container_factory.return_value.remove_image
    expected_calls = [call(ci) for ci in container_info.values()]
    mock_remove_image.assert_has_calls(expected_calls, any_order=True)


def get_expected_container_info(mock_filter_sources):
    def get_key(source):
        return f"{source.test_info.container_info.image}:{source.test_info.container_info.tag}"

    return {
        get_key(source): source.test_info.container_info
        for sources in mock_filter_sources.return_value.values()
        for source in sources
    }


@pytest.fixture
def mock_filter_sources(source_no_build, source_with_build):
    with patch("glotter.download.filter_sources") as mock:
        mock.return_value = {"baklava": [source_no_build], "fibonacci": [source_with_build]}
        yield mock


@pytest.fixture
def mock_thread_pool_executor():
    with patch("glotter.download.ThreadPoolExecutor") as mock:
        yield mock


@pytest.fixture
def mock_container_factory():
    with patch("glotter.download.get_container_factory") as mock:
        yield mock


class MockArgs:
    def __init__(self, parallel):
        self.parallel = parallel
