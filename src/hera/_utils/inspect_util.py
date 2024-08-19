import inspect
from typing import Callable, Optional


def inspect_callable_param_annotation(f: Callable, key: str) -> Optional[type]:
    func_param_annotation = inspect.signature(f).parameters[key].annotation
    if func_param_annotation is inspect.Parameter.empty:
        return None
    return func_param_annotation
