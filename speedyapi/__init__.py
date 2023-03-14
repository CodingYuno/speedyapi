
#      _____                         _                   _____  _____
#     / ____|                       | |           /\    |  __ \|_   _|
#    | (___   _ __    ___   ___   __| | _   _    /  \   | |__) | | |
#     \___ \ | '_ \  / _ \ / _ \ / _` || | | |  / /\ \  |  ___/  | |
#     ____) || |_) ||  __/|  __/| (_| || |_| | / ____ \ | |     _| |_
#    |_____/ | .__/  \___| \___| \__,_| \__, |/_/    \_\|_|    |_____|
#            | |                         __/ |
#            |_|                        |___/


"""
Easy Api Creation
~~~~~~~~~~~~~~~~~

Built on Flask / Async Flask with features for easily creating API endpoints

Features:
    - Authentication
    - Parameter Parsing and Checking
    - Rate Limiting
    - In depth Endpoint Testing
    - Automatic OpenAPI `swagger.json` Generation (access to full specification)
    - Common JSON Response Formatting
"""

__title__ = 'SpeedyAPI'
__description__ = 'Features for easily creating REST APIs'
__version__ = '2.0.1'
__author__ = 'CodingYuno'

from flask import request

from .main import API
from .parameters import PathParameter, QueryParameter, HeaderParameter, CookieParameter, JsonBodyParameter
from .respond import *
from .tests import Test
from .types import *
