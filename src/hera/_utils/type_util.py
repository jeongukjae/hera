"""Module that handles types and annotations."""

from typing import Any, Iterable, Optional, Type, TypeAlias, TypeVar, Union, cast

try:
    from typing import Annotated, get_args, get_origin  # type: ignore
except ImportError:
    from typing_extensions import Annotated, get_args, get_origin  # type: ignore


def is_annotated(annotation: Any):
    """Check annotation has Annotated type or not."""
    return get_origin(annotation) is Annotated


_Types: TypeAlias = Union[type, tuple["_Types", ...]]


def has_annotated_metadata(annotation: Any, t: _Types) -> bool:
    args = get_args(annotation)
    for arg in args[1:]:
        if isinstance(arg, t):
            return True
    return False


def consume_annotated_type(annotation: Any) -> type:
    if is_annotated(annotation):
        return get_args(annotation)[0]
    return annotation


T = TypeVar("T")


def consume_annotated_metadata(annotation: Any, type_: Union[Type[T], tuple[Type[T], ...]]) -> Optional[T]:
    args = get_args(annotation)
    for arg in args[1:]:
        if isinstance(type_, Iterable):
            for t in type_:
                if isinstance(arg, type_):
                    return arg
        else:
            if isinstance(arg, type_):
                return arg
    return None


def may_cast_subscripted_type(t: type) -> type:
    if origin_type := get_origin(t):
        return cast(type, origin_type)
    return t


def can_consume_primitive(annotation: type, target: type) -> bool:
    casted = may_cast_subscripted_type(annotation)
    if casted is Union:
        return any(can_consume_primitive(arg, target) for arg in get_args(annotation))
    return issubclass(casted, target)


def is_subscripted(t: type) -> bool:
    return get_origin(t) is not None
