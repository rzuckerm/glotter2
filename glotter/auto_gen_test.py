class AutoGenTest:
    """Object containing information about an auto-generated test"""

    def __init__(self, params, transformations):
        """
        Initialize auto-generated test information

        :param params: List of auto-generated test parameters
        :param transformations: List of output transformations
        """

        self._params = [AutoGenParam(param) for param in params]
        self._transformations = transformations

    @property
    def params(self):
        """return test parameters"""
        return self._params

    @property
    def transformations(self):
        """return output transformations"""
        return self._transformations


class AutoGenParam:
    """Object used for an auto-generated test parameter"""

    def __init__(self, param):
        """
        Initialize auto-generated test parameter

        :param param: Auto-generated test parameter
        """

        self._name = param.get("name")
        self._input_param = param.get("input")
        self._expected_output = param.get("expected")

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
