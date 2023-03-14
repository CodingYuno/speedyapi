import traceback

from .respond import error
from flask import Response


def handle_error(error_code, print_traceback: bool = True) -> Response:
    if print_traceback:
        traceback.print_exc()
    return error(cause=type(error_code).__name__)


def request_handler(f, print_traceback: bool = True, *args, **kwargs) -> Response:
    """
    :param f: The Endpoint Function
    :param print_traceback: Should python traceback be printed when Exceptions are thrown during handling of incoming requests
    :return: Response object
    """
    try:
        response = f(*args, **kwargs)
        if response is None:  # A valid response must be returned by all endpoints.
            raise TypeError(f"The view function for {f.__name__} did not return a valid response. "
                            f"The function either returned None or ended without a return statement.")
        return response
    except Exception as error_code:
        return handle_error(error_code, print_traceback=print_traceback)


async def async_request_handler(f, print_traceback: bool = True, *args, **kwargs) -> Response:
    """
    Async variant of `request_handler` for async endpoints using Async Flask

    :param f: The Endpoint Function
    :param print_traceback: Should python traceback be printed when Exceptions are thrown during handling of incoming requests
    :return: Response object
    """
    try:
        response = await f(*args, **kwargs)
        if response is None:  # A valid response must be returned by all endpoints.
            raise TypeError(f"The view function for {f.__name__} did not return a valid response. "
                            f"The function either returned None or ended without a return statement.")
        return response
    except Exception as error_code:
        return handle_error(error_code, print_traceback=print_traceback)

