"""The util module contains the functionality required for the script runner."""

import functools
import inspect
import json
import os
from typing import Any, Callable, Optional, cast

from hera.shared._pydantic import _PYDANTIC_VERSION
from hera.workflows import Artifact, Parameter
from hera.workflows.artifact import ArtifactLoader

try:
    from typing import Annotated, get_args, get_origin  # type: ignore
except ImportError:
    from typing_extensions import Annotated, get_args, get_origin  # type: ignore

if _PYDANTIC_VERSION == 2:
    from pydantic.type_adapter import TypeAdapter  # type: ignore
    from pydantic.v1 import parse_obj_as  # type: ignore
else:
    from pydantic import parse_obj_as


def ignore_unmatched_kwargs(f: Callable) -> Callable:
    """Make function ignore unmatched kwargs.

    If the function already has the catch all **kwargs, do nothing.
    """
    if _contains_var_kwarg(f):
        return f

    @functools.wraps(f)
    def inner(**kwargs):
        # filter out kwargs that are not part of the function signature
        # and transform them to the correct type
        filtered_kwargs = {key: _parse(value, key, f) for key, value in kwargs.items() if _is_kwarg_of(key, f)}
        return f(**filtered_kwargs)

    return inner


def _contains_var_kwarg(f: Callable) -> bool:
    """Tells whether the given callable contains a keyword argument."""
    return any(param.kind == inspect.Parameter.VAR_KEYWORD for param in inspect.signature(f).parameters.values())


def _is_kwarg_of(key: str, f: Callable) -> bool:
    """Tells whether the given `key` identifies a keyword argument of the given callable."""
    param = inspect.signature(f).parameters.get(key)
    return param is not None and (
        param.kind is inspect.Parameter.KEYWORD_ONLY or param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )


def _parse(value: str, key: str, f: Callable) -> Any:
    """Parse a value to the correct type.

    Args:
        value: The value to parse.
        key: The name of the kwarg.
        f: The function to parse the value for.

    Returns:
        The parsed value.

    """
    if _is_str_kwarg_of(key, f) or _is_artifact_loaded(key, f) or _is_output_kwarg(key, f):
        return value
    try:
        if os.environ.get("hera__script_annotations", None) is None:
            return json.loads(value)

        type_ = _get_unannotated_type(key, f)
        loaded_json_value = json.loads(value)

        if not type_:
            return loaded_json_value

        _pydantic_mode = int(os.environ.get("hera__pydantic_mode", _PYDANTIC_VERSION))
        if _pydantic_mode == 1:
            return parse_obj_as(type_, loaded_json_value)
        else:
            return TypeAdapter(type_).validate_python(loaded_json_value)
    except (json.JSONDecodeError, TypeError):
        return value


def _get_type(type_: type) -> type:
    if get_origin(type_) is None:
        return type_
    origin_type = cast(type, get_origin(type_))
    if origin_type is Annotated:
        return get_args(type_)[0]
    return origin_type


def _get_unannotated_type(key: str, f: Callable) -> Optional[type]:
    """Get the type of function param without the 'Annotated' outer type."""
    type_ = inspect.signature(f).parameters[key].annotation
    if type_ is inspect.Parameter.empty:
        return None
    if get_origin(type_) is None:
        return type_

    origin_type = cast(type, get_origin(type_))
    if origin_type is Annotated:
        return get_args(type_)[0]

    # Type could be a dict/list with subscript type
    return type_


def _is_str_kwarg_of(key: str, f: Callable) -> bool:
    """Check if param `key` of function `f` has a type annotation of a subclass of str."""
    func_param_annotation = inspect.signature(f).parameters[key].annotation
    if func_param_annotation is inspect.Parameter.empty:
        return False

    type_ = _get_type(func_param_annotation)
    return issubclass(type_, str)


def _is_artifact_loaded(key: str, f: Callable) -> bool:
    """Check if param `key` of function `f` is actually an Artifact that has already been loaded."""
    param = inspect.signature(f).parameters[key]
    return (
        get_origin(param.annotation) is Annotated
        and isinstance(get_args(param.annotation)[1], Artifact)
        and get_args(param.annotation)[1].loader == ArtifactLoader.json.value
    )


def _is_output_kwarg(key: str, f: Callable) -> bool:
    """Check if param `key` of function `f` is an output Artifact/Parameter."""
    param = inspect.signature(f).parameters[key]
    return (
        get_origin(param.annotation) is Annotated
        and isinstance(get_args(param.annotation)[1], (Artifact, Parameter))
        and get_args(param.annotation)[1].output
    )
