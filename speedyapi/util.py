import inspect
import ast
import sys

from threading import Lock
from copy import deepcopy


import tokenize
from inspect import EndOfBlock


class PatchedBlockFinder:
    """
    Patch of the inspect python module `BlockFinder` class to fix decorator lambda issues

    My Bug report: https://github.com/python/cpython/issues/102647 (Was Fixed 3.10.10)
    """
    def __init__(self):
        self.indent = 0
        self.islambda = False
        self.started = False
        self.passline = False
        self.indecorator = False
        self.decoratorhasargs = False
        self.last = 1
        self.body_col0 = None
        self.decorator_open_bracket = False  # Added to track state of decorator own brackets
        self.decorator_args_open_bracket = 0  # Added to track state of decorator argument brackets

    def tokeneater(self, type, token, srowcol, erowcol, line):
        if not self.started and not self.indecorator:
            # skip any decorators
            if token == "@":
                self.indecorator = True
            # look for the first "def", "class" or "lambda"
            elif token in ("def", "class", "lambda"):
                if token == "lambda":
                    self.islambda = True
                self.started = True
            self.passline = True    # skip to the end of the line
        elif token == "(":
            if self.indecorator:
                self.decoratorhasargs = True
                if self.decorator_open_bracket:  # Inside decorator own brackets
                    self.decorator_args_open_bracket += 1  # A positive number shows we are inside argument brackets
                else:
                    self.decorator_open_bracket = True
        elif token == ")":
            if self.indecorator and self.decorator_args_open_bracket:  # Inside decorator argument brackets
                self.decorator_args_open_bracket -= 1  # Closing one level of decorator argument brackets
            elif self.indecorator:
                self.indecorator = False
                self.decorator_open_bracket = False  # No longer inside decorator
                self.decoratorhasargs = False
        elif type == tokenize.NEWLINE:
            self.passline = False   # stop skipping when a NEWLINE is seen
            self.last = srowcol[0]
            if self.islambda:       # lambdas always end at the first NEWLINE
                raise EndOfBlock
            # hitting a NEWLINE when in a decorator without args
            # ends the decorator
            if self.indecorator and not self.decoratorhasargs:
                self.indecorator = False
        elif self.passline:
            pass
        elif type == tokenize.INDENT:
            if self.body_col0 is None and self.started:
                self.body_col0 = erowcol[1]
            self.indent = self.indent + 1
            self.passline = True
        elif type == tokenize.DEDENT:
            self.indent = self.indent - 1
            # the end of matching indent/dedent pairs end a block
            # (note that this only works for "def"/"class" blocks,
            #  not e.g. for "if: else:" or "try: finally:" blocks)
            if self.indent <= 0:
                raise EndOfBlock
        elif type == tokenize.COMMENT:
            if self.body_col0 is not None and srowcol[1] >= self.body_col0:
                # Include comments if indented at least as much as the block
                self.last = srowcol[0]
        elif self.indent == 0 and type not in (tokenize.COMMENT, tokenize.NL):
            # any other token on the same indentation level end the previous
            # block as well, except the pseudo-tokens COMMENT and NL.
            raise EndOfBlock


if sys.version_info[1] < 10 or sys.version_info[2] < 10:
    inspect.BlockFinder = PatchedBlockFinder  # Patch of the above class


def clean_time(seconds: int | float) -> str:
    """
    :param seconds: time in seconds that is to be converted
    :return: time string e.g. 5m10s
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d:
        return f"{d}d{h}h"
    elif h:
        return f"{h}h{m}m"
    elif m:
        return f"{m}m{s}s"
    else:
        return f"{s}s"


def remove_none(dictionary: dict) -> dict:
    """ Remove key, value pairs if the value is None (Used to clean up swagger files) """
    for key, value in dictionary.copy().items():
        if value is None:
            dictionary.pop(key)
    return dictionary


def get_decorators_args(target, is_async: bool = False):
    """
    Uses ast + inspect to visit the source code of functions to find decorator arguments.
    This is used to allow a decorator to see the arguments of other decorators above or below it decorating the same function

    I have only written the code to parse kwargs at this time

    :param target: The target function that has been decorated
    :param is_async: If the target function is async (This is required as async visitation is ast is different from sync)
    """
    decorators = {}  # decorator arg storage

    def visit_func(node):
        decorators[node.name] = {}
        for n in node.decorator_list:
            if isinstance(n, ast.Call):  # Find the name of the decorator
                name = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
            else:
                name = n.attr if isinstance(n, ast.Attribute) else n.id
            decorators[node.name][name] = {"kwargs": {}, "args": {}}
            for kw in n.keywords:
                if "value" in vars(vars(kw)["value"]):  # Standard kwargs
                    decorators[node.name][name]["kwargs"][vars(kw)["arg"]] = vars(kw)["value"].value
                else:
                    try:  # List kwargs 1
                        decorators[node.name][name]["kwargs"][vars(kw)["arg"]] = [x.value for x in vars(kw)["value"].values][0]
                    except AttributeError:  # List kwargs 2
                        decorators[node.name][name]["kwargs"][vars(kw)["arg"]] = [x.value for x in vars(kw)["value"].elts]

    node_iter = ast.NodeVisitor()

    if is_async:
        node_iter.visit_AsyncFunctionDef = visit_func  # Async the visiting functon above to be used
    else:
        node_iter.visit_FunctionDef = visit_func  # Async the visiting functon above to be used

    try:
        node_iter.visit(ast.parse(inspect.getsource(target)))  # Run the visit
    except SyntaxError:  # The above patch should prevent this causing issues again
        raise SyntaxError("Please do not use lambda functions inside decorators due to limitations of builtin inspect module.")

    return decorators


def str_to_seconds(string: str) -> tuple:
    """
    Converts rate limit strings to usable integer values

    e.g. converts `120/min` to `120` and `60`

    :praram string: The rate limit string to be parsed
    :return: two integers: The count per minute allowed and the time frame of that count
    """
    count, frame = string.lower().split("/")
    converts = {
        "day": 86400, "hour": 3600, "minute": 60, "second": 1,
        "min": 60, "sec": 1,
        "d": 86400, "h": 3600, "m": 60, "S": 1,
        "days": 86400, "hours": 3600, "minutes": 60, "seconds": 1
    }

    try:
        if " " in frame:  # Time frame is a multiple of a standard frame
            return int(count), int(frame.split(" ")[0]) * converts[frame.split(" ")[1]]
        else:
            return int(count), int(converts[frame])
    except (IndexError, KeyError):
        raise TypeError(f"Invalid rate limit string: {string}")


class ThreadSafeDict(dict):
    """
    Threadsafe version of the built-in dictionary (dict).

    ThreadSafeDict() -> new empty ThreadSafeDict
    ThreadSafeDict(iterable) -> new ThreadSafeDict initialized as if via:
        d = {}
        for k, v in iterable:
            d[k] = v
    ThreadSafeDict(**kwargs) -> new ThreadSafeDict initialized with the name=value pairs
        in the keyword argument list.  For example:  ThreadSafeDict(one=1, two=2)
    """

    def __init__(self, seq=None, **kwargs):
        self.lock = Lock()
        if seq is not None:
            super().__init__(seq)
        else:
            super().__init__(**kwargs)

    def clear(self) -> None:
        """ D.clear() -> None.  Remove all items from D. """
        with self.lock:
            super().clear()

    def copy(self) -> 'ThreadSafeDict':
        """ D.copy() -> a shallow copy of D """
        with self.lock:
            return ThreadSafeDict(super().copy())

    def deepcopy(self) -> 'ThreadSafeDict':
        """ D.deepcopy() -> a deep copy of D """
        with self.lock:
            return ThreadSafeDict(deepcopy(super()))

    def fromkeys(self, __iterable: iter, __value=None) -> 'ThreadSafeDict':
        """ Create a new dictionary with keys from iterable and values set to value. """
        with self.lock:
            return ThreadSafeDict(super().fromkeys(__iterable=__iterable, __value=__value))

    def get(self, __key, default=None):
        """ Return the value for key if key is in the dictionary, else default. """
        with self.lock:
            return super().get(__key, default)

    def items(self) -> dict.items:
        """ D.items() -> a set-like object providing a view on D's items """
        with self.lock:
            return super().items()

    def keys(self) -> dict.keys:
        """ D.keys() -> a set-like object providing a view on D's keys """
        with self.lock:
            return super().keys()

    def pop(self, __key):
        """
        D.pop(k[,d]) -> v, remove specified key and return the corresponding value.

        If the key is not found, return the default if given; otherwise,
        raise a KeyError.
        """
        with self.lock:
            return super().pop(__key)

    def popitem(self) -> tuple:
        """
        Remove and return a (key, value) pair as a 2-tuple.

        Pairs are returned in LIFO (last-in, first-out) order.
        Raises KeyError if the dict is empty.
        """
        with self.lock:
            return super().popitem()

    def setdefault(self, __key, __default=None):
        """
        Insert key with a value of default if key is not in the dictionary.

        Return the value for key if key is in the dictionary, else default.
        """
        with self.lock:
            return super().setdefault(__key, __default)

    def update(self, __m, **kwargs) -> None:
        """
        D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
        If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
        If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
        In either case, this is followed by: for k in F:  D[k] = F[k]
        """
        with self.lock:
            super().update(__m, **kwargs)

    def values(self) -> dict.values:
        """ D.values() -> an object providing a view on D's values """
        with self.lock:
            return super().values()

    def __getitem__(self, k):
        """ x.__getitem__(y) <==> x[y] """
        with self.lock:
            return super().__getitem__(k)

    def __len__(self) -> int:
        """ Return len(self). """
        with self.lock:
            return super().__len__()

    def __eq__(self, other: 'ThreadSafeDict') -> bool:
        """ Return self==value. """
        with self.lock:
            return super().__eq__(other)

    def __ne__(self, other: 'ThreadSafeDict') -> bool:
        """ Return self!=value. """
        with self.lock:
            return super().__ne__(other)

    def __repr__(self) -> str:
        """ Return repr(self). """
        with self.lock:
            return super().__repr__()

    def __setitem__(self, __key, __value):
        """ Set self[key] to value. """
        with self.lock:
            return super().__setitem__(__key, __value)

    def set(self, __key, __value):
        with self.lock:
            return super().__setitem__(__key, __value)

    def snapshot(self) -> dict:
        """ Return dict(ThreadSafeDict()) """
        with self.lock:
            return {x: y for x, y in super().items()}

    def __contains__(self, item):
        """ True if the dictionary has the specified key, else False. """
        with self.lock:
            super().__contains__(item)
