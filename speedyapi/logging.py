import time

from flask import request

from .color import color_print, Color


log_color = lambda x: [82, 87, 226, 207][int(str(x)[0]) - 2]  # Colors for each type of status code


def api_logging(response, log_file: str = None, print_logs: bool = True) -> None:
    """
    :param response: A flask Response object
    :param log_file: The path of the file where logs should be recorded
    :param print_logs: If logs should be printed (Use when using a production WSGI server)
    """
    log_string_date_time = f"{dict(request.headers).get('X-Forwarded-For', request.remote_addr)} - - [{time.strftime('%d-%m-%Y %H:%M:%S', time.gmtime())}] \""
    log_string_path = f"{request.method} {request.full_path} {str(request.scheme).upper()}"
    log_string_status = f"\" {response.status_code} -"

    if log_file is not None:
        with open(log_file, 'a') as output:
            output.write(f"{log_string_date_time}{log_string_path}{log_string_status}\n")

    if print_logs:

        try:
            _log_color = log_color(response.status_code)
        except IndexError:
            _log_color = 4  # 500+ status code

        color_print(
            Color(log_string_date_time, color="white"),
            Color(log_string_path, color=_log_color),
            Color(log_string_status, color="white")
        )
