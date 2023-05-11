import time
import functools
import logging
import click
import inspect
import json as json_lib

from flask import Flask, request, send_file, Response
from typing import Callable
from threading import Thread
from http.client import responses

from .handler import request_handler, async_request_handler
from .respond import invalid, error, missing, forbidden, json, html, rate_limited
from .logging import api_logging
from .exceptions import InvalidMethod
from .parameters import test_parameter_type, input_handler, PathParameter, QueryParameter, HeaderParameter,\
    CookieParameter, JsonBodyParameter, convert_param_to_in
from .tests import Test
from .util import clean_time, get_decorators_args, ThreadSafeDict
from .color import color_print, Color
from .swagger_objects import *
from .swagger import redoc_html, recursive_generation_of_json_response_schema
from .limiter import update_limits


class API(Flask):
    """
    Inherited from standard Flask object

    Allows for use of api features
    """
    def __init__(self, import_name: str, logger: Callable | str = "requests.log", print_traceback: bool = True,
                 info: InfoObject = None, servers: ServerObject | List[ServerObject] = None,
                 user_limits: list = None, ip_limits: list = None, global_limits: list = None,
                 path_to_favicon: str = "favicon.ico") -> None:
        """
        :param import_name: the name of the application package
        :param logger: either the path to a log file or a function / coroutine to be called after each request (this function will be passed the response object from flask)
        :param print_traceback: if python traceback should be printed for requests that throw exceptions during handling
        :param info: An OpenAPI info Object from `speedyapi.swagger_objects` used to provide details for documentation generation
        :param servers: An OpenAPI server Object or list of server Objects from `speedyapi.swagger_objects`
        :param user_limits: Whole API rate limits to be applied to unique `apikey` sent with requests by users
        :param ip_limits: Whole API external address rate limits to be applied
        :param global_limits: Rate limits for all requests on all endpoints for the API
        :param path_to_favicon: Path to a favicon.ico file

        :usage

            >>> from speedyapi import API
            >>> from speedyapi.swagger_objects import InfoObject, XLogoObject  # The complete collection of OpenAPI objects
            >>>
            >>> info = InfoObject(title="My First API", version="v1")  # Create an info object for the swagger
            >>>
            >>> # Create the 'app' in this case using the info object above and a rate limit of 1000 requests per minute
            >>> app = API(__name__, logger="requests.txt", print_traceback=True, info=info, global_limits=["1000/min"])
            >>>
            >>> # Add some extra parts of the OpenAPI specification or Redoc allowed specification extensions e.g. description and x-logo
            >>> app.swagger.info.logo = XLogoObject(url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTFfIP_NiAxmaKhPf0noGYmO2d103EV_s1GWP4rt8pH&s")
            >>> app.swagger.info.description = "# Introduction\nThis is an example API for the speedyapi python module.\n\nPowered By: `Python` `Flask` `SpeedyAPI`"
            >>>

        Any part of the OpenAPI specification can be easily added by using `speedyapi.swagger_objects` throughout your code however beside the info and servers objects all
        other esential parts will be generated automatically by the decorators below (if used to decorate endpoints).
        """
        Flask.__init__(self, import_name=import_name)
        self.api_endpoint_list = []
        self.print_traceback = print_traceback

        # Blocking of all standard Flask logging / alerts. This is done as all relevant simple alerts and logs are rebuilt in this library
        # Furthermore Flask logs are ignored when using a WSGI server to host the application (Which every developer should be doing)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        click.echo = click.secho = lambda *args, **kwargs: None

        self.host, self.port = None, None

        # If no server has been specified localhost http (port 80) is used
        if servers is None:
            servers = [ServerObject(url="http://localhost:80")]

        # Default OpenAPI Info object (This should not be used. Developers should pass their own Info Object.)
        if info is None:
            info = InfoObject(
                title=import_name,
                version="1.0.1"
            )
        if info.__getattribute__("logo") is None:  # Due to `x-logo` not being an allowed python variable name logo has been used and is swapped here
            info.__setattr__("x-logo", XLogoObject(url=servers[0].url + "/favicon.ico"))

        # The APIs swagger is created here using the base OpenAPI Object (4.8.1 in the latest specification)
        self.swagger = OpenAPIObject(
            openapi="3.1.0",
            info=info,
            servers=servers,
            paths=PathsObject(),
            components=ComponentsObject()
        )
        self.override_swagger = {}  # If an override swagger.json is used when the API is run it is stored here

        # Async and Sync default authentication functions for the API (These can be made to support all authentication methods in the standard OpenAPI specification)
        self.auth_function, self.auth_function_require_key = None, False
        self.async_auth_function, self.async_auth_function_require_key = None, False

        self.request_logging = False  # This is kept off until after tests have been run over localhost for cleanliness
        self.endpoint_tests = {}
        self.test_count = 0

        # Storage of the current state of all rate limits across the whole API
        # This is thread safe due to Flask and Async Flask using threading for request handling
        self.rate_limits = ThreadSafeDict(
            paths={},
            overall_limits={
                "user_limits": {},
                "ip_limits": {},
                "global_limits": {}
            }
        )
        self.user_limits = user_limits
        self.ip_limits = ip_limits
        self.global_limits = global_limits

        # Added to replace the standard `404 not found` and `405 wrong method` thrown on unknown endpoints by Flask
        @self.endpoint(path="/<path:path>", docs_ignore=True)
        def catch_all(path):
            return invalid(key="cause", data=f"Unknown endpoint: /{path}", success=False)

        # Added to automatically handle favicon.ico
        @self.endpoint(path=f"/favicon.ico", docs_ignore=True)
        def favicon():
            try:
                return send_file(path_to_favicon, mimetype='image/vnd.microsoft.icon')
            except FileNotFoundError:
                return error(cause="FileNotFoundError")

        # Async and Sync methods for logging with a passed function
        # Standard logging to a file
        if inspect.iscoroutinefunction(logger):  # Async
            @self.after_request
            async def after_request(response):
                if self.request_logging:
                    api_logging(response)
                    await logger(response)
                return response
        elif callable(logger):  # Sync
            @self.after_request
            async def after_request(response):
                if self.request_logging:
                    api_logging(response)
                    await logger(response)
                return response
        elif type(logger) == str:  # Log to file
            @self.after_request
            async def after_request(response):
                if self.request_logging:
                    api_logging(response, log_file=logger, print_logs=True)
                return response

        # Endpoint for the OpenAPI swagger.json (automatically fetched by Redoc documentation below)
        @self.endpoint(path=f"/swagger.json", method="GET", docs_ignore=True)
        async def swagger():
            swagger_json = self.override_swagger if self.override_swagger else self.swagger.json()
            return json(swagger_json)

        # The base path is used for Redoc documentation based on an automatically generated or manually set swagger.json file
        @self.endpoint(path=f"/", method="GET", docs_ignore=True)
        async def docs():
            return html(redoc_html(info.title, server=request.host_url))

    def endpoint(self, path: str, method: str = "GET", authentication: str | list = None, name: str = None, description: str = None, docs_ignore: bool = False, group: str = None):
        """
        Creation of endpoints for the API

        :param path: The path of the endpoint
        :param method: The method of the endpoint e.g. GET, POST, PUT .. (Unlike standard Flask please write separate endpoints for each method type if required)
        :param authentication: The authentication scope for the endpoint.
        :param name: The name of the endpoint (Used for swagger.json generation)
        :param description: A description of the expected use for the endpoint (Used for swagger.json generation)
        :param docs_ignore: If set to True the method for this endpoint will be skipped in the documentation

        :usage:

            >>> from speedyapi import types, respond, request
            >>>
            >>> app = ...  # Example app creation in the __init__ docstring
            >>>
            >>> @app.endpoint(path=f"/test", method="GET", name="Test Endpoint", description="Used for testing.")
            >>> @app.limits(ip_limits=["30/min"])
            >>> @app.tests(Test(url="/test", headers={"Apikey": "CorrectApikey"}, expected_status_code=200),
            >>>            Test(url="/test", headers={"Apikey": "WrongApikey"}, expected_status_code=403))
            >>> @app.parameters(QueryParameter(name="user", type=types.String, required=False, description="User who is testing.", default="user-1"))
            >>> def test_endpoint(user):
            >>>     return respond.json({"user": user, "authentication": request.authentication})

            The above example shows the creation of an endpoint with basic uses of each of the speedyapi endpoint decorators:
             - The `endpoint` decorator chooses the path and method and provides information for swagger.json generaton
                (authentication usage will be shown in the autentication method docstring)
             - The `limits` decorator is used to add various rate limits to the endpoint (for more info see `limits` below)
             - The 'tests' decorator is used to create tests that are run on the endpoint on startup and used to help generate OpenAPI schema
                In this example two tests are used to make sure the Apikey Authentication distinguishes between two provided keys
             - The `parameters` decorator is used to assist with parameter parsing. This is explained in more detail below.

             An endpoint must return a Flask `Response` object. If you wish you can use my `respond` library which includes most common
              response types with their appropriate status code.

            The Flask `request` object allows you to access information on the request being handled anywhere in the request context.
            I have added authentication and apikey attributes to the `request` object to assist with creation of security checks.
        """
        def decorator(f):
            if inspect.iscoroutinefunction(f):  # If the endpoint is to use Async Flask
                @self.route(rule=path, methods=method)
                @functools.wraps(f)
                async def async_decorated_function(*args, **kwargs) -> Response:
                    receive_time = time.time()
                    if authentication is not None:  # Standard Apikey authentication handling (As explained below in the `authentication` docstring you can use this for other methods e.g. oauth)
                        apikey = dict(request.args).get("key", dict(request.headers).get("Apikey", None))
                        request.apikey = apikey
                        auth_type = None
                        if apikey is None and self.async_auth_function_require_key:
                            return missing("key")  # If an apikey is required a missing key response is sent
                        if self.async_auth_function and (auth_type := await self.async_auth_function()) not in authentication:
                            if type(auth_type) == Response:
                                return auth_type
                            return forbidden(cause="Access is forbidden, usually due to an invalid API key being used.")  # Standard 403 response (You can return your own custom response anywhere in the request context)
                        if type(auth_type) == Response:
                            return auth_type
                        request.authentication = auth_type
                    else:
                        request.authentication, request.apikey = None, None
                    response = await async_request_handler(f, print_traceback=self.print_traceback, *args, **kwargs)
                    response.headers = {**response.headers, **{"Process-Time": round(time.time() - receive_time)}}   # A process time header is added here
                    return response

                return async_decorated_function
            else:  # If the endpoint is to use Standard Flask (not async) - See above for comments
                @self.route(rule=path, methods=method)
                @functools.wraps(f)
                def decorated_function(*args, **kwargs) -> Response:
                    receive_time = time.time()
                    if authentication is not None:
                        apikey = dict(request.args).get("key", dict(request.headers).get("Apikey", None))
                        request.apikey = apikey
                        auth_type = None
                        if apikey is None and self.auth_function_require_key:
                            return missing("key")
                        if self.auth_function and (auth_type := self.auth_function()) not in authentication:
                            if type(auth_type) == Response:
                                return auth_type
                            return forbidden(cause="Access is forbidden, usually due to an invalid API key being used.")
                        if type(auth_type) == Response:
                            return auth_type
                        request.authentication = auth_type
                    else:
                        request.authentication, request.apikey = None, None
                    response = request_handler(f, print_traceback=self.print_traceback, *args, **kwargs)
                    response.headers = {**response.headers, **{"Process-Time": round(time.time() - receive_time)}}
                    return response

                return decorated_function

        authentication = [authentication] if type(authentication) == str else authentication

        method = [method] if type(method) == str else method  # methods are placed in lists here as from this point onwards support for multiple methods is supported (Not yet supported throughout)
        if any(m.upper() not in ["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"] for m in method):
            raise InvalidMethod("Method must be one of `GET`, `POST`, `HEAD`, `PUT`, `DELETE`, `PATCH`")

        # Automatic documentation generation for the swagger.json file
        if not docs_ignore:

            # An api endpoint storage not used anywhere. Could be useful to a developer.
            self.api_endpoint_list.append({"path": path, "method": method, "authentication": authentication, "name": name, "description": description})

            if path not in self.swagger["paths"].keys():  # Path is not added to the PathsObject as a PathItemObject
                self.swagger["paths"][path] = PathItemObject()  # New path added to the OpenAPI Paths object
            for meth in method:
                self.swagger["paths"][path][meth.lower()] = OperationObject(
                    tags=[group] if group else None,
                    summary=name,
                    description=description,
                    security=[],
                    responses=ResponsesObject()
                )

                # Adding authentication to the Operation Object (If you are using more complex authentication please add to `.swagger` inside your application file)
                if authentication is not None:
                    self.swagger["paths"][path][meth.lower()]["security"] = [SecurityRequirementObject(
                        Apikey=authentication,
                        key=authentication
                    )]

        return decorator

    def authentication(self, apikey_required: bool = False, description: str = None):
        """
        Used to create authentication functions for the API.
        At the current time please use this to decorate at most one `Sync` and one `Async` authentication function.

        :param apikey_required: If a user is required to provide an apikey for the authentication function to be called.
            This can be implemented yourself inside your authentication function or similarly implemented for other security methods.
        :param description: A description of the security used (This is automatically added to the swagger.json).
            If you wish to have individual descriptions for each endpoint please add to the `.swagger` inside the request context.

        :usage:

            >>> from speedyapi import request
            >>>
            >>> app = ...  # Example app creation in the __init__ docstring
            >>>
            >>> @app.authentication(apikey_required=True, description="An Apikey can be generated by visiting ... with a verified ... account.")
            >>> def sync_auth():
            >>>     return "allowed" if request.apikey == "CorrectApikey" else None
            >>>
            >>> @app.authentication(apikey_required=True, description="An Apikey can be generated by visiting ... with a verified ... account.")
            >>> async def async_auth():
            >>>     return "allowed" if request.apikey == "CorrectApikey" else None
            >>>

            The above example shows the declaring of the two authentication functions.
            In this example it is for basic `apiKey` protection returning "allowed" / None depending on the apikey provided
            The authentication function should return a string / None indicating the allowed scope of the user. This can be used either by setting
                the authentication argument of the `.endpoint` decorator to the scope or by using `request.authentication` inside the request context
        """
        def decorator(f):
            if inspect.iscoroutinefunction(f):  # If the authentication function is `Async`
                self.async_auth_function = f
                self.async_auth_function_require_key = apikey_required
            else:
                self.auth_function = f  # if the authentication function is `Sync`
                self.auth_function_require_key = apikey_required

            # Add the security definition to the Swagger info object description to be accessed by Redoc
            self.swagger.info.description += "\n\n# Authentication\n\n<!-- ReDoc-Inject: <security-definitions> -->"

            if apikey_required:
                # If an apikey is being used standard apikey schemes are added to the security component of the swagger
                self.swagger.components.securitySchemes = Map(
                    Apikey=SecuritySchemeObject(type="apiKey", name="Apikey", _in="header", description=description),
                    key=SecuritySchemeObject(type="apiKey", name="key", _in="query", description=description)
                )

        return decorator

    def parameters(self, *args: PathParameter | QueryParameter | JsonBodyParameter | HeaderParameter | CookieParameter):
        """
        Used to handle and parse parameters from various parts of a request
        :param - You can pass as many Parameter objects as you wish

        This decorator handles the following:
            :PathParameter:
                e.g. /endpoint/<resource>
            :QueryParameter:
                e.g. /?text=hello
            :HeaderParameter:
                e.g. User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36
            :CookieParameter:
                e.g. session: 123456789

            :JsonBodyParameter:  - WARNING This is not a supported part of the OpenAPI specification or reasonable as a specification extension.
                e.g. {"users": ["Jack", "Jim", "Justin", "James"]}

        The JsonBodyParameter is not an allowed part of the OpenAPI specification however due to very frequent personal need I have added it here and parsed it as a query parameter to the swagger

        --- From the Parameter Docstring ---

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

        ------------------------------------

        :usage:

            >>> from speedyapi import request
            >>>
            >>> app = ...  # Example app creation in the __init__ docstring
            >>>
            >>> @app.endpoint(path=f"/maths/<method>", method="GET", name="Simple Maths", description="Simple operations between two given numbers.")
            >>> @app.parameters(PathParameter(name="method", options=["multiply", "divide", "add", "subtract"], default="add", description="Choose some maths stuff."),
            >>>                 QueryParameter(name="a", type=types.Number, required=True, description="First number to use."),
            >>>                 QueryParameter(name="b", type=types.Number, required=True, description="Second number to use."))
            >>> def maths_endpoint(method, a, b):
            >>>     methods = {"multiply": lambda x, y: x * y, "divide": lambda x, y: x / y, "add": lambda x, y: x + y, "subtract": lambda x, y: x - y}
            >>>     return respond.json({"result": methods[method](a, b)})
            >>>

            In the above example three parameters are handled and parsed:
                - The path parameter which tells the endpoint which maths operation is checked to confirm it is an allowed operation
                - Two query perameters are handled for the numbers `a` and `b`. These are checked to confirm they are numbers and converted to floats ready for usage in the function

            All parameters that are passed as kwargs to the endpoint function.

            If you do not wish to use this decorator to handle all input parameters feel free to still use the Flask `request` object
        """
        def decorator(f):
            if inspect.iscoroutinefunction(f):  # Endpoint using Async Flask
                @functools.wraps(f)
                async def async_decorated_function(**kwargs):
                    path_kwargs = kwargs
                    for parameter_object in args:
                        test_parameter_type(parameter_object)  # Confirm it is an allowed parameter type
                        parsed_inputs = input_handler(parameter=parameter_object, **path_kwargs)  # Find the values of the parameters and parse them to correct types
                        if type(parsed_inputs) == Response:
                            return parsed_inputs  # If a request response has been raised during parsing e.g. missing or malformed it needs to be returned here too
                        else:
                            kwargs = kwargs | parsed_inputs  # Add the newly parsed input parameters to kwargs
                    return await f(**kwargs)

            else:  # Endpoint using Standard Flask (not async)
                @functools.wraps(f)
                def decorated_function(**kwargs):
                    path_kwargs = kwargs
                    for parameter_object in args:
                        test_parameter_type(parameter_object)
                        parsed_inputs = input_handler(parameter=parameter_object, **path_kwargs)
                        if type(parsed_inputs) == Response:
                            return parsed_inputs
                        else:
                            kwargs = kwargs | parsed_inputs
                    return f(**kwargs)


            # We need to know the path and method of the endpoint from a higher up decorator so ast + inspect are used to visit the source
            path = get_decorators_args(f, is_async=inspect.iscoroutinefunction(f))[f.__name__]["endpoint"]["kwargs"]["path"]
            method = get_decorators_args(f, is_async=inspect.iscoroutinefunction(f))[f.__name__]["endpoint"]["kwargs"]["method"]

            # Each method for the endpoint needs to have parameters automatically added to its swagger.json
            if path in self.swagger["paths"]:
                for meth, meth_obj in self.swagger["paths"][path].copy().items():
                    if meth.lower() != method.lower():  # The method is not from this endpoint so is ignored
                        continue

                    meth_obj["parameters"] = []
                    for parameter_object in args:

                        # This is not a part of the specification however I like to show options in bold at the bottom of the description string
                        option_string = "" if parameter_object.options is None else f"\n\n**Options**: {', '.join(parameter_object.options)}"

                        # JsonBodyParameter edge case is added to the parameter name (Warning this is not allowed in the OpenAPI specification)
                        name_string = parameter_object.name if type(parameter_object) != JsonBodyParameter else f"Json Body: {{'{parameter_object.name}': <{parameter_object.type.__name__}>}}"
                        if type(parameter_object) == JsonBodyParameter:  # No longer requires separate Parameter Object creation (Will be removed)
                            meth_obj["parameters"].append(ParameterObject(
                                name=name_string,
                                description=parameter_object.description + option_string,
                                _in=convert_param_to_in(parameter_object),
                                schema={"type": parameter_object.type.__name__},
                                required=parameter_object.required
                            ))
                        else:
                            meth_obj["parameters"].append(ParameterObject(
                                name=name_string,
                                description=parameter_object.description + option_string,
                                _in=convert_param_to_in(parameter_object),
                                schema={"type": parameter_object.type.__name__},  # The name of the OpenAPI parameter object type is found
                                required=parameter_object.required
                            ))

            if inspect.iscoroutinefunction(f):
                return async_decorated_function
            else:
                return decorated_function
        return decorator

    def limits(self, user_limits: list = None, ip_limits: list = None, global_limits: list = None):
        """
        Add rate limits to the endpoint.

        :param user_limits: rate limit strings to be applied to individuals using the endpoint (distinguished by apikey)
        :param ip_limits: rate limit strings to be applied to each external address using endpoint (ipv4/6)
        :param global_limits: rate limits for all users using the endpoint (can be used to limit load or as a prevention for dumping via request spamming)

        rate limit strings must follow the following format:
            "<number>/<number> <time word>"

            e.g. "120/min" or "120/2 min"

            The following words and their corresponding time frames are supported:

                >>> {
                >>>     "day": 86400, "hour": 3600, "minute": 60, "second": 1,
                >>>     "min": 60, "sec": 1,
                >>>     "d": 86400, "h": 3600, "m": 60, "S": 1,
                >>>     "days": 86400, "hours": 3600, "minutes": 60, "seconds": 1
                >>> }
                >>>

            You may use an unlimited number of rate limit strings

        Rate limits are handled efficiently per time frame using floor division
        Wait times are calculated using modulus

        :usage:

            >>> from speedyapi import respond
            >>>
            >>> app = ...  # Example app creation in the __init__ docstring
            >>>
            >>> @app.endpoint(path=f"/limitcheck", method="GET", name="Test Rate Limit", description="Lets get throttled!")
            >>> @app.limits(user_limits=["10/min", "120/2 hours"], ip_limits=["30/min"], global_limits=["5000/5 min"])
            >>> def rate_limit_endpoint():
            >>>     return respond.nothing()
            >>>

            The above code will add 4 rate limits to the endpoint.
            The endpoint will return `201 No Content` unless the user is rate limited.

            The first rate limit to hit during 1 minute of testing will be once the user hits 11 requests

        You can add rate limits for the whole API in the app creation arguments.

        I have not implemented automatic generation of documentation for rate limits as it is generally advisable to not reveal rate limits to users
        If you do wish to reveal the rate limit then just add it to the authentication description.
        """
        def decorator(f):

            # We need to know the path and method of the endpoint from a higher up decorator so ast + inspect are used to visit the source
            path = get_decorators_args(f, is_async=inspect.iscoroutinefunction(f))[f.__name__]["endpoint"]["kwargs"]["path"]
            method = get_decorators_args(f, is_async=inspect.iscoroutinefunction(f))[f.__name__]["endpoint"]["kwargs"]["method"]

            # Rate limit locations are created for the endpoint
            self.rate_limits["paths"].setdefault(path, {})[method] = dict(
                user_limits={},
                ip_limits={},
                global_limits={}
            )

            if inspect.iscoroutinefunction(f):  # Endpoint using Async Flask
                @functools.wraps(f)
                async def async_decorated_function(**kwargs):
                    current_time_s = round(time.time())  # The recieve time is only created once per request

                    # Limits are checked for breaches for the per endpoint limits
                    user_res = update_limits(user_limits, current_time_s, self.rate_limits["paths"][path][method]["user_limits"], request.apikey)
                    addr_res = update_limits(ip_limits, current_time_s, self.rate_limits["paths"][path][method]["ip_limits"], request.remote_addr)
                    global_res = update_limits(global_limits, current_time_s, self.rate_limits["paths"][path][method]["global_limits"])

                    # Limits are checked for breaches for the whole API
                    overall_user_res = update_limits(self.user_limits, current_time_s, self.rate_limits["overall_limits"]["user_limits"], request.apikey)
                    overall_addr_res = update_limits(self.ip_limits, current_time_s, self.rate_limits["overall_limits"]["ip_limits"], request.remote_addr)
                    overall_global_res = update_limits(self.global_limits, current_time_s, self.rate_limits["overall_limits"]["global_limits"])

                    # A check is performed to see if any rate limits have been breached
                    # If a rate limit has been breached the max wait time of all breaches is returned to the user
                    if any(type(res) == int for res in [user_res, addr_res, global_res, overall_user_res, overall_addr_res, overall_global_res]):
                        return rate_limited(max([wt for wt in [user_res, addr_res, global_res, overall_user_res, overall_addr_res, overall_global_res] if type(wt) == int]))

                    return await f(**kwargs)

                return async_decorated_function
            else:  # Endpoint using Standard Flask (not async)
                @functools.wraps(f)
                def decorated_function(**kwargs):
                    current_time_s = round(time.time())

                    user_res = update_limits(user_limits, current_time_s, self.rate_limits["paths"][path][method]["user_limits"], request.apikey)
                    addr_res = update_limits(ip_limits, current_time_s, self.rate_limits["paths"][path][method]["ip_limits"], request.remote_addr)
                    global_res = update_limits(global_limits, current_time_s, self.rate_limits["paths"][path][method]["global_limits"])

                    overall_user_res = update_limits(self.user_limits, current_time_s, self.rate_limits["overall_limits"]["user_limits"], request.apikey)
                    overall_addr_res = update_limits(self.ip_limits, current_time_s, self.rate_limits["overall_limits"]["ip_limits"], request.remote_addr)
                    overall_global_res = update_limits(self.global_limits, current_time_s, self.rate_limits["overall_limits"]["global_limits"])

                    if any(type(res) == int for res in [user_res, addr_res, global_res, overall_user_res, overall_addr_res, overall_global_res]):
                        return rate_limited(max([wt for wt in [user_res, addr_res, global_res, overall_user_res, overall_addr_res, overall_global_res] if type(wt) == int]))

                    return f(**kwargs)

                return decorated_function

        return decorator

    def tests(self, *args: Test):
        """
        Run tests on your endpoints to make sure they function properly and to help generate accurate OpenAPI schema

        The tests decorator can take an unlimited number of `Test` objects:

            --- Test Object Docstring ---

                :param url: The path of the endpoint top be requested
                :param headers: Any headers to be sent with the request
                :param cookies: Any cookies to be sent with the request
                :param timeout: The timeout of the request
                :param json: A json body to send alongside POST requests
                :param expected_status_code: The status code to be expected for a successful response
                :param checks: A list of checks that are to be performed on the response json
                :param example: If the response should be used as an exammple field for the swagger schema (Warning example may be deprecated in the future)

                :usage:

                    >>> Test(
                    >>>     url="/maths/multiply?a=3&b=5",  # The path of the test with some query parameters
                    >>>     headers={"Apikey": "ThisIsAnApikey"},  # An apikey to be sent for the test
                    >>>     expected_status_code=200,  # We expect a 200 Ok response
                    >>>     checks=[
                    >>>         lambda x: x["result"] == 15  # A check is to be performed to make sure that a field `result` in the response has value `15`
                    >>>     ]
                    >>> )
                    >>>

            ----------------------------

        When the API is started if the `tests` argument of the `run` method is set to True then a thread is spawned for each test
        Tests are performed over localhost.

        The responses from tests are used to help generate OpenAPI operation schema.
        """
        def decorator(f):
            # We need to know the path and method of the endpoint from a higher up decorator so ast + inspect are used to visit the source
            path = get_decorators_args(f, is_async=inspect.iscoroutinefunction(f))[f.__name__]["endpoint"]["kwargs"]["path"]
            method = get_decorators_args(f, is_async=inspect.iscoroutinefunction(f))[f.__name__]["endpoint"]["kwargs"]["method"]

            if path not in self.endpoint_tests.keys():
                self.endpoint_tests[path] = {}
            self.endpoint_tests[path][method.lower()] = []

            for test in args:  # Prepare tests to be run
                self.endpoint_tests[path][method.lower()].append(test)
                self.test_count += 1
                if test.checks is not None:
                    self.test_count += len(test.checks)

            # Standard empty decorator handling
            if inspect.iscoroutinefunction(f):  # Endpoint using Async Flask
                @functools.wraps(f)
                async def async_decorated_function(**kwargs):
                    return await f(**kwargs)
                return async_decorated_function
            else:  # Endpoint using Standard Flask (not async)
                @functools.wraps(f)
                def decorated_function(**kwargs):
                    return f(**kwargs)
                return decorated_function

        return decorator

    def run(self, host: str = None, port: int = None, tests: bool = False, swagger: str = None, print_test_responses: bool = False,
            threaded: bool = False, debug: bool = None, load_dotenv: bool = True, **kwargs):
        """
        Runs the application on a local development server.

        Do not use run() in a production setting. It is not intended to meet security and performance requirements for a production server.
         Instead, see /deploying/index for WSGI server recommendations. (From Flask run() docstring) - I recommend gunicorn for new developers

        :param host: The hostname to listen on. Set this to `0.0.0.0` to have the server available externally as well.
        :param port: The port of the webserver. Defaults to `5000`
        :param tests: If tests should be run (tests will be declared inside the `tests` decorator of endpoint functions)
        :param swagger: Pass a path to a swagger.json file to be used instead of the automatically generated one
        :param threaded: If the API should be run threaded (For most use cases it is best to test with this True)
        :param debug: Enable or disable debug mode.
        :param load_dotenv: Load the nearest `.env` and `.flaskenv` files to set environment variables.

        If the debug flag is set the server will automatically reload for code changes and show a debugger in case an exception happened.

        If you want to run the application in debug mode, but disable the code execution on the interactive debugger, you can pass `use_evalex=False` as parameter.
        This will keep the debugger's traceback screen active, but disable code execution.
        """

        self.host, self.port = host, port

        def run_app():
            """ Run Flask development server inside thread """
            Flask.run(self, host=host, port=port, debug=debug, load_dotenv=load_dotenv, threaded=threaded, **kwargs)

        def test_thread(path, method, test):
            """ Thread for each endpoint test """
            nonlocal success_count, failed_count
            test_response, test_success_count, test_failed_count = test.run(method=method, port=port, print_test_responses=print_test_responses)  # Run the test
            success_count += test_success_count
            failed_count += test_failed_count
            if path in self.swagger.paths:
                response = self.swagger.paths[path][method].responses

                # Update the swagger.json to add the new Response Object based on the ran test
                response[str(test_response.status_code)] = ResponseObject(
                    description=responses[test_response.status_code] or "",
                    content=Map()
                )

                # Add schema to the Response Object using recursive generation
                content = response[str(test_response.status_code)].content
                content["application/json"] = MediaTypeObject(
                    schema=recursive_generation_of_json_response_schema(test_response.json())
                )

                # If an example is to be added it is set here (May be deprecated in future versions of the OpenAPI specification)
                if test.example:
                    content["application/json"].schema["example"] = test_response

        color_print("-" * 90, color="white")

        if tests:
            app_thread = Thread(target=run_app, daemon=False)
            app_thread.start()  # API started here
            t0 = time.time()
            success_count, failed_count = 0, 0

            test_threads = set()
            for path, methods in self.endpoint_tests.items():
                for method, tests in methods.items():
                    for test in tests:
                        # Each test has a thread spawned
                        test_threads.add(Thread(target=test_thread, kwargs=dict(path=path, method=method, test=test)))
            for test_thread in test_threads:
                # Each test is run in parallel
                test_thread.start()
            for test_thread in test_threads:
                # The program waits for all tests to finish
                test_thread.join()

            color_print(f" *  Tests Completed - - "
                        f"(Success: {Color(f'{success_count}/{self.test_count}', color='red' if failed_count else 'green')}) - "
                        f"[Time: {clean_time(round(time.time() - t0, 2))}]", color="white")
            color_print(" - " * 30, color="white")

            self.request_logging = True  # Logging is turned back on so external requests will log (It was turned off to prevent standard logging of tests)
            color_print(f" *  API Ready - - [{Color(f'Running on: http://{host}:{port}/', color='blue')}] - - "
                        f"({Color('Press CTRL+C to quit!', color='red')})", color="green")
            color_print("-" * 90, color="white")

            if swagger is None:  # Saves the automatically generated swagger.json file
                with open("swagger.json", "w") as swag_file:
                    swag_file.write(json_lib.dumps(self.swagger.json(), indent=4, sort_keys=False))
            else:  # Gets a previously generated/written swagger.json file
                with open(swagger, "r") as swag_file:
                    self.override_swagger = json_lib.load(swag_file)

            app_thread.join()  # No further code is executed after the app.run() in the current thread
        else:
            self.request_logging = True  # Requests will log in console / with whatever logging method has been setup
            color_print(f" *  API Ready - - [{Color(f'Running on: http://{host}:{port}/', color='blue')}] - - "
                        f"({Color('Press CTRL+C to quit!', color='red')})", color="green")
            color_print("-" * 90, color="white")

            if swagger is not None:  # Gets a previously generated/written swagger.json file
                with open(swagger, "r") as swag_file:
                    self.override_swagger = json_lib.load(swag_file)

            run_app()  # No further code is executed after the app.run()

    @property
    def server(self):
        """
        Returns the host and port the API is running on

        :return: host the API is running on e.g. 0.0.0.0
        :return: port the API is running on e.g. 443
        """
        return self.host, self.port
