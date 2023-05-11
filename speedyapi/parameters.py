import ast

from flask import request, Response

from .respond import malformed, missing
from .exceptions import InvalidParameter
from .types import *


class Parameter:
    def __init__(self, name: str, type: Object | Array | String | Null | Number | Integer | Boolean = String,
                 checks: list = None, options: list = None, required: bool = True, default=None, description: str = ""):
        """
        A Parameter object used for creating endpoint inputs

        :param name: The name of the parameter
        :param type: The data type of the parameter
        :param checks: Any checks that should be run on the parameter to make sure it meets the expected specification
        :param options: If there is only a select number of options the parameter should accept
        :param required: If the parameter is required for the endpoint
        :param default: A default value for the parameter if none are provided by the external user
        :param description: A description for the parameter to be used for the generation of the `swagger.json`

        :example usage:

            >>> PathParameter(
            >>>     name="version",
            >>>     options=["staging", "v1", "v2"],
            >>>     default="v2",
            >>>     description="Choose the version of API to use."
            >>> )

            >>> QueryParameter(
            >>>     name="uuid",
            >>>     type=String,
            >>>     required=True,
            >>>     checks=[lambda uuid: all([char in "abcdef0123456789" for char in uuid.lower()]) and len(uuid) == 32],
            >>>     description="uuid of some type of resource."
            >>> )

        """
        self.name, self.type, self.checks, self.options, self.required, self.default, self.description = name, type, checks, options, required, default, description


class PathParameter(Parameter):
    """
    A Parameter object used for creating endpoint inputs that are provided via the request path

    :param name: The name of the parameter
    :param type: The data type of the parameter
    :param checks: Any checks that should be run on the parameter to make sure it meets the expected specification
    :param options: If there is only a select number of options the parameter should accept
    :param required: If the parameter is required for the endpoint
    :param default: A default value for the parameter if none are provided by the external user
    :param description: A description for the parameter to be used for the generation of the `swagger.json`
    """  # Docstring repeated due to parent docstring not being passed by some IDEs
    pass


class QueryParameter(Parameter):
    """
    A Parameter object used for creating endpoint inputs that are provided via the request query

    :param name: The name of the parameter
    :param type: The data type of the parameter
    :param checks: Any checks that should be run on the parameter to make sure it meets the expected specification
    :param options: If there is only a select number of options the parameter should accept
    :param required: If the parameter is required for the endpoint
    :param default: A default value for the parameter if none are provided by the external user
    :param description: A description for the parameter to be used for the generation of the `swagger.json`
    """  # Docstring repeated due to parent docstring not being passed by some IDEs
    pass


class HeaderParameter(Parameter):
    """
    A Parameter object used for creating endpoint inputs that are provided via request headers

    :param name: The name of the parameter
    :param type: The data type of the parameter
    :param checks: Any checks that should be run on the parameter to make sure it meets the expected specification
    :param options: If there is only a select number of options the parameter should accept
    :param required: If the parameter is required for the endpoint
    :param default: A default value for the parameter if none are provided by the external user
    :param description: A description for the parameter to be used for the generation of the `swagger.json`
    """  # Docstring repeated due to parent docstring not being passed by some IDEs
    pass


class CookieParameter(Parameter):
    """
    A Parameter object used for creating endpoint inputs that are provided via request cookies

    :param name: The name of the parameter
    :param type: The data type of the parameter
    :param checks: Any checks that should be run on the parameter to make sure it meets the expected specification
    :param options: If there is only a select number of options the parameter should accept
    :param required: If the parameter is required for the endpoint
    :param default: A default value for the parameter if none are provided by the external user
    :param description: A description for the parameter to be used for the generation of the `swagger.json`
    """  # Docstring repeated due to parent docstring not being passed by some IDEs
    pass


class JsonBodyParameter(Parameter):
    """
    A Parameter object used for creating endpoint inputs that are provided via request body

    This only supports json format payloads.

        (Due to this not being a standard part of the OpenAPI specification or Redoc I add these as query parameters to swagger.json)

    :param name: The name of the parameter
    :param type: The data type of the parameter
    :param checks: Any checks that should be run on the parameter to make sure it meets the expected specification
    :param options: If there is only a select number of options the parameter should accept
    :param required: If the parameter is required for the endpoint
    :param default: A default value for the parameter if none are provided by the external user
    :param description: A description for the parameter to be used for the generation of the `swagger.json`
    """  # Docstring repeated due to parent docstring not being passed by some IDEs
    pass


def get_request_inputs(parameter: Parameter, **kwargs) -> dict:
    """
    Parse the various allowed types of request inputs to python dictionaries ready to be used.

    :param parameter: A Parameter object which is to be used to create a parsed input
    :return: A dictionary of key, values for the parameter to be extracted from
    """
    if type(parameter) == PathParameter:
        return kwargs
    elif type(parameter) == QueryParameter:
        return dict(request.args)
    elif type(parameter) == HeaderParameter:
        return dict(request.headers)
    elif type(parameter) == CookieParameter:
        return dict(request.cookies)
    elif type(parameter) == JsonBodyParameter:
        return request.json

    else:
        raise InvalidParameter(parameter)


def test_parameter_type(parameter_object):
    """ Check the parameter is an allowed type. """
    if type(parameter_object) not in [PathParameter, QueryParameter, HeaderParameter, CookieParameter,
                                      JsonBodyParameter]:
        raise TypeError("All arguments must be of type Parameter!")


def input_handler(parameter: Parameter, **kwargs) -> dict | Response:
    request_inputs, parsed_inputs = get_request_inputs(parameter, **kwargs), {}
    if (input_value := request_inputs.get(parameter.name,
                                          None)) is not None:  # Check if the parameter was provided with the request
        try:
            parameter.type(input_value)  # Check the type of the provided value
        except ValueError:
            return malformed(malformed_item=parameter.name)
        for check in (parameter.checks or []):  # Run checks on the provided value
            if not check(input_value):
                return malformed(malformed_item=parameter.name)
        if parameter.options is not None:  # If options were limits check that the value is allowed
            if input_value not in parameter.options:
                return malformed(malformed_item=parameter.name)
        if parameter.type == Boolean:
            input_value = True if input_value.lower() == "true" else False
        if parameter.type != String:
            try:
                parsed_inputs[parameter.name] = ast.literal_eval(
                    input_value)  # Attempt to convert to desired python type (literal_eval is safe to use do not worry)
            except (ValueError, SyntaxError):
                parsed_inputs[
                    parameter.name] = input_value  # Value remains as a string to be parsed by the user in the request function context
        else:
            parsed_inputs[parameter.name] = input_value
    elif parameter.required:  # Handle failure to provide required parameter with standard `missing` response
        return missing(missing_field=parameter.name)
    else:
        parsed_inputs[parameter.name] = parameter.default  # Set to the default parameter value
    return parsed_inputs


def convert_param_to_in(param: Parameter):
    """ Convert a paramater object to its OpenAPI string name for the `in` field of the ParameterObject (4.8.12) """
    param_type = type(param)

    if param_type == PathParameter:
        return "path"
    elif param_type == QueryParameter:
        return "query"
    elif param_type == HeaderParameter:
        return "header"
    elif param_type == CookieParameter:
        return "cookie"
    elif param_type == JsonBodyParameter:
        return "query"

    else:
        raise TypeError("Not a valid Parameter type!")
