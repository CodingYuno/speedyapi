import json as json_lib

from typing import Any
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from flask import redirect as redi, send_file, Response


def json(data: dict | list | tuple | str | int | float | bool | None, status_code: int = 200, success_key: bool = True) -> Response:
    """
    :param data: data to send as json
    :param status_code: status code of the response
    :param success_key: Add {"success": True} key/value pair to the response
    """
    if success_key:
        if type(data) == dict:
            data = {"success": True} | data  # Add `"success": True` to the response if not already added
        else:
            data = {"success": True, "data": data}  # Force `"success": True` to the response moving the data to "data" key
    return Response(
        response=json_lib.dumps(data).encode("utf-8"),
        status=status_code,
        mimetype='application/json'
    )


def text(text: str, status_code: int = 200) -> Response:
    """
    :param text: text to send
    :param status_code: status code of the response
    """
    return Response(
        response=text,
        status=status_code,
        mimetype="text/plain"
    )


def nothing(status_code: int = 201) -> Response:
    """
    :param status_code: status code of the response
    """
    return Response(
        response="",
        status=status_code,
        mimetype="text/plain"
    )


def html(html: str, status_code: int = 200) -> Response:
    """
    :param html: html to send
    :param status_code: status code of the response
    """
    return Response(
        response=html,
        status=status_code,
        mimetype="text/html"
    )


def file(path_or_file: str, attachment: bool = False, mimetype=None) -> send_file:
    """
    :param path_or_file: file to send
    :param attachment: send as an attachment
    :param mimetype: mimetype of response
    """
    return send_file(
        path_or_file=path_or_file,
        mimetype=mimetype,
        as_attachment=attachment
    )


def python(code: str, status_code: int = 200, color: bool = True, header_html: str = "", footer_html: str = "") -> send_file:
    """
    :param code: Python code to send
    :param status_code: status code of the response
    :param color: Should the code have python highlighting
    :param header_html: HTML to send at the top of the python code
    :param footer_html: HTML to send at the bottom of the python code
    """
    if color:
        return Response(
            response=header_html + highlight(code, PythonLexer(), HtmlFormatter(noclasses=True)) + footer_html,
            status=status_code,
            mimetype="text/html"
        )
    return Response(
        response=code,
        status=status_code,
        mimetype="text/plain"
    )


def image(path_or_file: str, attachment: bool = False) -> send_file:
    """
    :param path_or_file: file to send
    :param attachment: send as an attachment
    """
    return send_file(
        path_or_file=path_or_file,
        mimetype='image/gif',
        as_attachment=attachment
    )


def redirect(redirect_url: str) -> redi:
    """
    :param redirect_url: url to redirect user to
    """
    return redi(redirect_url)


def malformed(malformed_item: Any) -> Response:
    """
    :param malformed_item: input field that is malformed
    """
    return Response(
        response=json_lib.dumps({"success": False, "cause": f"Malformed [{malformed_item}]"}).encode("utf-8"),
        status=422,
        mimetype='application/json'
    )


def missing(missing_field: str | list) -> Response:
    """
    :param missing_field: required input field that has not been provided
    """
    missing_field = [missing_field] if type(missing_field) is str else missing_field
    return Response(
        response=json_lib.dumps({"success": False, "cause": f"Missing one or more fields [{' / '.join(missing_field)}]"}).encode("utf-8"),
        status=400,
        mimetype='application/json'
    )


def error(cause: str) -> Response:
    """
    :param cause: details of the error
    """
    return Response(
        response=json_lib.dumps({"success": False, "cause": cause}).encode("utf-8"),
        status=500,
        mimetype='application/json'
    )


def forbidden(cause: str) -> Response:
    """
    :param cause: why access has been denied
    """
    return Response(
        response=json_lib.dumps({"success": False, "cause": f"{cause}"}).encode("utf-8"),
        status=403,
        mimetype='application/json'
    )


def method_not_allowed() -> Response:
    return Response(
        response=json_lib.dumps({"success": False, "cause": f"method not allowed."}).encode("utf-8"),
        status=405,
        mimetype='application/json'
    )


def server_error() -> Response:
    return Response(
        response=json_lib.dumps({"success": False, "cause": "Server Error"}).encode("utf-8"),
        status=500,
        mimetype='application/json'
    )


def deprecated() -> Response:
    return Response(
        response=json_lib.dumps({"success": False, "cause": "Deprecated"}).encode("utf-8"),
        status=410,
        mimetype='application/json'
    )


def backend_down() -> Response:
    return Response(
        response=json_lib.dumps({"success": False, "cause": "Backend Connection Failed"}).encode("utf-8"),
        status=503,
        mimetype='application/json'
    )


def rate_limited(wait_time=None) -> Response:
    """
    :param wait_time: time to wait until access will be allowed again
    """
    if wait_time is None:
        return Response(
            response=json_lib.dumps({"success": False, "cause": f"Rate Limited"}).encode("utf-8"),
            status=429,
            mimetype='application/json'
        )
    else:
        return Response(
            response=json_lib.dumps({"success": False, "cause": f"Rate Limited - Try again in {wait_time} seconds."}).encode("utf-8"),
            status=429,
            mimetype='application/json',
            headers={"Retry-After": wait_time}
        )


def service_unavailable(wait_time: int) -> Response:
    """
    :param wait_time: time to wait until resource is ready
    """
    return Response(
        response=json_lib.dumps({"success": False, "cause": "Resource generating try again in a few seconds"}).encode("utf-8"),
        status=503,
        mimetype='application/json',
        headers={"Retry-After": wait_time}
    )


def exceeded_limits(item: str, limit: int) -> Response:
    """
    :param item: Item supplied in the request e.g. scores to be submitted
    :param limit: Max number of items allowed to be supplied e.g. max 10 scores per request
    """
    return Response(
        response=json_lib.dumps({"success": False, "cause": f"Max {limit} {item} allowed per request"}).encode("utf-8"),
        status=404,
        mimetype='application/json'
    )


def invalid(key: str, data: dict | list | tuple | str | int | float | bool | None = None, success: bool = True, status_code: int = 404) -> Response:
    """
    In most cases it is better to just use respond.json with a 400+ status code

    :param key: Item that was not considered valid e.g. user not in database
    :param data: Data to be returned (most likely None)
    :param success: Was the requests successful despite lack of data to return?
    :param status_code: Status code to return (most likely 404)
    """
    return Response(
        response=json_lib.dumps({"success": success, f"{key}": data}).encode("utf-8"),
        status=status_code,
        mimetype='application/json'
    )
