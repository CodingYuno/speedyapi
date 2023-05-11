import time

import requests

from .color import Color, color_print
from .util import clean_time
from .logging import log_color


class Test:
    def __init__(self, url: str = None, headers: dict = None, cookies: dict = None, timeout: int = 60,
                 json: str | dict | list | int | float = None, expected_status_code: int = 200, checks: list = None,
                 example: bool = None):
        """
        Run tests on your endpoints to make sure they function properly and to help generate accurate OpenAPI schema

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

        """
        self.url = url
        self.headers = headers
        self.cookies = cookies
        self.timeout = timeout
        self.json = json
        self.expected_status_code = expected_status_code
        self.checks = checks
        if example is None:
            self.example = True if str(expected_status_code)[0] in ["4", "5"] else False  # Examples are defaulted to being used for 4-- and 5-- status codes
        else:
            self.example = example

    def print_test_response(self, response: requests.Response, success: bool, message: str, elapsed: int | float, print_test_responses: bool = False) -> None:
        """
        Prints a log for a successful status code test

        :param response: The response object from the request
        :param success: If the test is considered a success
        :param message: The message to log for the test
        :param elapsed: The time taken to conduct the test
        """
        signal_color = 'green' if success else 'red'
        color_print(f" {Color('*', color=signal_color)}  Test on path `{Color(self.url.split('?')[0], f'- - {response.request.method}', color='white')}` "
                    f"{message} [Time: {clean_time(elapsed)}] - - {Color(response.text, color=signal_color) if print_test_responses or not success else ''}", color="white")

    def run(self, method: str, port: int, print_test_responses: bool = False) -> tuple:
        """
        Execute the test.

        :param method: The request method to use e.g. GET, POST ..
        :param port: The port to run the test on (host is assumed as localhost)

        :return response: The response is returned so it can be used to generate swagger schema
        :return success_count: The number of tests ran that were successful
        :return failed_count: The number of tests ran that failed
        """
        t0, success_count, failed_count = time.time(), 0, 0
        url = f"http://localhost:{port}{self.url}" if self.url[0] == "/" else f"http://localhost/{self.url}"
        requests_func = eval(f"requests.{method.lower()}")  # Select the correct method from the requests library
        try:
            response = requests_func(url=url, headers=self.headers, cookies=self.cookies, json=self.json or {}, timeout=self.timeout)
        except Exception as e:
            self.print_test_response(
                response=None,
                success=False,
                message=f"returned incorrect status code {Color(repr(e), color=log_color(500))} expecting "
                        f"{Color(self.expected_status_code, color=log_color(self.expected_status_code))}",
                elapsed=round(time.time() - t0, 2),
                print_test_responses=print_test_responses
            )
            return None, 0, 1 + len(self.checks)
        elapsed, status_code = round(time.time() - t0, 2), response.status_code
        if status_code != self.expected_status_code:  # Incorrect status code
            self.print_test_response(
                response=response,
                success=False,
                message=f"returned incorrect status code {Color(status_code, color=log_color(status_code))} expecting "
                        f"{Color(self.expected_status_code, color=log_color(self.expected_status_code))}",
                elapsed=elapsed,
                print_test_responses=print_test_responses
            )
            failed_count += 1
        else:  # Correct status code
            self.print_test_response(
                response=response,
                success=True,
                message=f"returned correct status code {Color(response.status_code, color=log_color(response.status_code))}",
                elapsed=elapsed,
                print_test_responses=print_test_responses
            )
            success_count += 1
        for check in self.checks or []:  # Run further tests on the response
            try:
                if check(response.json()):  # Test Succeeded
                    self.print_test_response(
                        response=response,
                        success=True,
                        message=f"{Color('Success', color='green')}",
                        elapsed=elapsed,
                        print_test_responses=print_test_responses
                    )
                    success_count += 1
                else:  # Test Failed
                    self.print_test_response(
                        response=response,
                        success=False,
                        message=f"{Color('Failed', color='red')}",
                        elapsed=elapsed,
                        print_test_responses=print_test_responses
                    )
                    failed_count += 1
            except Exception as error:  # Exception thrown during test
                self.print_test_response(
                    response=response,
                    success=False,
                    message=f"{Color(f'Failed with exception: {error}', color='darkred')}",
                    elapsed=elapsed,
                    print_test_responses=print_test_responses
                )
                failed_count += 1
        return response, success_count, failed_count
