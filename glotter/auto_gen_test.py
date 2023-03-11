# pylint hates pydantic
# pylint: disable=E0213,E0611
from typing import List, Dict, Union, Any

from pydantic import BaseModel, validator, constr, conlist

TransformationT = List[Union[str, Dict[str, List[str]]]]


class AutoGenParam(BaseModel):
    """Object used for an auto-generated test parameter"""

    name: constr(min_length=1)
    input: Union[None, str]
    expected: Union[str, List[str], Dict[str, str]]


class AutoGenTest(BaseModel):
    """Object containing information about an auto-generated test"""

    name: constr(min_length=1, regex="^[a-zA-Z][0-9a-zA-Z_]*$")
    requires_parameters: bool = False
    params: conlist(AutoGenParam, min_items=1)
    transformations: TransformationT = []

    @validator("params", each_item=True, pre=True)
    def validate_params(
        cls, value: Dict[str, Any], values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate each parameter

        :param value: Parameter to validate
        :param values: Test item
        :return: Original parameter if project requires parameters. Otherwise, parameter with
            an empty "name" and an "input" of `None`
        :raises: :exc:`ValueError` if project requires parameters but no input
        """

        if values.get("requires_parameters"):
            if "input" not in value:
                raise ValueError(
                    'This project requires parameters, but "input" is not specified'
                )

            return value

        return {**value, "name": value.get("name") or "na", "input": value.get("input")}
