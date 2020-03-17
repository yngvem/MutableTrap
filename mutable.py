from copy import copy, deepcopy
from functools import wraps
from inspect import getfullargspec
from typing import Any, NamedTuple, Callable, List, Tuple


__author__ = "Yngve Mardal Moe"


class Parameter(NamedTuple):
    name: str
    idx: int
    default_val: Any


class KWParameter(NamedTuple):
    name: str
    default_val: Any


def _get_default_args(f: Callable) -> tuple:
    """Returns the default argument tuple of `f`.
    """
    defaults = getfullargspec(f).defaults

    if defaults is None:
        defaults = ()
    return defaults


def _get_default_kwargs(f: Callable) -> dict:
    """Returns the default keyword arguments of `f`
    """
    kwdefaults = getfullargspec(f).kwonlydefaults

    if kwdefaults is None:
        kwdefaults = {}
    return kwdefaults


def _get_arginfo(argument: str, f: Callable) -> Parameter:
    """Returns a Parameter instance for the specified argument.
    """
    f_arguments = getfullargspec(f).args
    defaults = _get_default_args(f)

    start_defaults_idx = len(f_arguments) - len(defaults)
    current_argument_idx = f_arguments.index(argument)
    default_val = defaults[current_argument_idx - start_defaults_idx]
    return Parameter(argument, current_argument_idx, default_val)


def _get_kwonly_arginfo(argument: str, f: Callable) -> KWParameter:
    """Returns a KWParameter instance for the specified keyword only argument.
    """
    kwdefaults = _get_default_kwargs(f)
    default_val = kwdefaults[argument]
    return KWParameter(argument, default_val)


def _get_arguments_with_defaults(f: Callable) -> list:
    """Returns a list with the names of all arguments that have default values.
    """
    f_arguments = getfullargspec(f).args
    defaults = _get_default_args(f)

    numargs = len(f_arguments)
    first_default_idx = numargs - len(defaults)

    args_with_defaults = f_arguments[first_default_idx:]

    return [_get_arginfo(arg, f) for arg in args_with_defaults]


def _get_kwonly_arguments_with_defaults(f: Callable) -> List[KWParameter]:
    """Returns a list with the names of all kwonly args that have default values
    """
    kwdefaults = _get_default_kwargs(f)
    return [_get_kwonly_arginfo(arg, f) for arg in kwdefaults.keys()]


def _get_argument_lists(
    args: List[str], f: Callable
) -> Tuple[List[Parameter], List[KWParameter]]:
    """Separates args into two lists.

    If args is empty then a list of all arguments with default values and
    all kwonly arguments with default are returned.

    One of the lists contain the elements of `args` that are arguments of `f`
    and the other contain the elements of `args` that are keyword-only arguments
    of `f`. An error is raised if any element of `args` is neither an argument
    nor a keyword-only argument of f.
    """
    if len(args) == 0:
        arguments = _get_arguments_with_defaults(f)
        kwonly_arguments = _get_kwonly_arguments_with_defaults(f)
        return arguments, kwonly_arguments

    f_arguments = getfullargspec(f).args
    f_kwonlyargs = getfullargspec(f).kwonlyargs
    defaults = _get_default_args(f)
    kwdefaults = _get_default_kwargs(f)

    arguments = []
    kwonly_arguments = []

    for arg in args:
        if arg in f_arguments:
            arguments.append(_get_arginfo(arg, f))
        elif arg in f_kwonlyargs:
            kwonly_arguments.append(_get_kwonly_arginfo(arg, f))
        else:
            raise ValueError(f"{arg} is not a valid argument of {f}")
    return arguments, kwonly_arguments


def _arg_supplied_to_call(argument: Parameter, args: tuple, kwargs: tuple) -> bool:
    """Returns whether or not the argument is supplied
    """
    return (len(args) > argument.idx) or (argument.name in kwargs)


def mutable(*args, use_deepcopy=False, copyfunction=None):
    """Removes mutable default traps of the specified inputs.

    Arguments:
    ----------
    *args : str
        A sequence of strings, each string signalling that the specified
        argument has a mutable default
    deepcopy : bool (optional, keyword only)
        If true, a deepcopy of the default argument is performed
    copyfunction : function (optional, keyword only)
        Sometimes, the builtin deepcopy doesn't perform a "deep enough" copy,
        because of this, the option of supplying your own copy function is
        provided.

    Examples:
    ---------
    Simple example:

    >>> @mutable('b')
    >>> def f(a, b=[]):
    >>>     b.append(a)
    >>>     return b
    >>> print(f(1))
    [1]
    >>> print(f(1)) 
    [1]
    >>> # Without the decorator, this would be equal to [1, 1]


    It works with keyword only arguments too:

    >>> @mutable('b', 'd')
    >>> def g(a, b=[], *args, c, d={}):
    >>>     b.append(a)
    >>>     d[a] = c
    >>>     return b, d
    >>> print(g(1, c=2))
    [1], {1: 2}
    >>> print(g(2, c=3))
    [2], {2: 3}
    >>> # Without the decorator, this would be equal to [1, 2], {1: 2, 2: 3}


    If no arguments are supplied to the decorator, all defaults are copied

    >>> @mutable
    >>> def g(a, b=[], *args, c, d={}):
    >>>     b.append(a)
    >>>     d[a] = c
    >>>     return b, d
    >>> print(g(1, c=2))
    [1], {1: 2}
    >>> print(g(2, c=3))
    [2], {2: 3}
    >>> # Without the decorator, this would be equal to [1, 2], {1: 2, 2: 3}
    """
    if deepcopy:
        _copy = deepcopy
        if copyfunction is not None:
            raise ValueError("Cannot specify copyfunction if deepcopy is True")
    else:
        _copy = copy
    if copyfunction is not None:
        _copy = copyfunction

    def mutable_decorator(f):
        """The actual decorator that removes default traps.
        """
        arguments, kwonly_arguments = _get_argument_lists(args, f)

        @wraps(f)
        def safe_f(*_args, **_kwargs):
            kwargs_dict = {}

            for arg in arguments:
                if not _arg_supplied_to_call(arg, _args, _kwargs):
                    kwargs_dict[arg.name] = _copy(arg.default_val)

            for arg in kwonly_arguments:
                if arg.name not in _kwargs:
                    kwargs_dict[arg.name] = _copy(arg.default_val)

            return f(*_args, **_kwargs, **kwargs_dict)

        return safe_f

    # If used directly as a decorator
    if len(args) == 1:
        if callable(args[0]):
            f = args[0]
            args = ()
            return mutable_decorator(f)

    return mutable_decorator
