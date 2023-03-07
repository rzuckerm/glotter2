class AutoGenTest:
    """Object used for an auto-generated test"""

    def __init__(self, test_name, params):
        """
        Initialize auto-generated test

        :param test_name: Name of auto-generated test
        :param params: List of auto-generated test parameters
        :param test_output_filters: List of test output filters
        """

        self._test_name = test_name
        self._params = [AutoGenParam(param) for param in params]
        self._test_output_filters = test_output_filters

        @property
        def test_name(self):
            """Return a test name"""
            return self._test_name

        @property
        def params(self):
            """return test parameters"""
            return self._params


class AutoGenParam:
    """Object used for an auto-generated test parameter"""

    def __init__(self, param):
        """
        Initialize auto-generated test parameter

        :param param: Auto-generated test parameter
        """

        self._name = param.get("name")
        self._input_param = param.get("input")
        self._expected_output = param.get("expected_output")

    @property
    def name(self):
        """Return name of auto-generated test parameter"""
        return self._name

    @property
    def input_param(self):
        """Return input parameter"""
        return self._input_param

    @property
    def expected_output(self):
        """Return expected output"""
        return self._expected_output
