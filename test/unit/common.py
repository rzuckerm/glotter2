def set_mock_thread_pool_executor_map(mock_executor):
    def mock_map_func(func, iterable):
        return [func(item) for item in iterable]

    mock_map = mock_executor.return_value.__enter__.return_value.map
    mock_map.side_effect = mock_map_func
    return mock_map
