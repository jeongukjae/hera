"""The script_annotations_util module contains actual entrypoint function to run hera in Argo."""

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, cast

from hera.shared._pydantic import _PYDANTIC_VERSION
from hera.shared.serialization import serialize
from hera.workflows._runner.script_annotations_util import (
    map_argo_inputs_to_function,
    save_annotated_return_outputs,
    save_dummy_outputs,
)
from hera.workflows._runner.util import ignore_unmatched_kwargs
from hera.workflows.io.v1 import (
    Output as OutputV1,
)
from hera.workflows.script import _extract_return_annotation_output

if _PYDANTIC_VERSION == 2:
    from hera.workflows.io.v2 import (  # type: ignore
        Output as OutputV2,
    )
else:
    from hera.workflows.io.v1 import (  # type: ignore
        Output as OutputV2,
    )


def _runner(entrypoint: str, kwargs_list: List[dict]) -> Any:
    """Run the function defined by the entrypoint with the given list of kwargs.

    Args:
        entrypoint: The module path to the script within the container to execute. "package.submodule:function"
        kwargs_list: A list of dicts with "name" and "value" keys, representing the kwargs of the function.

    Returns:
        The result of the function or `None` if the outputs are to be saved.
    """
    # import the module and get the function
    module, function_name = entrypoint.split(":")
    function: Callable = getattr(importlib.import_module(module), function_name)
    # if the function is wrapped, unwrap it
    # this may happen if the function is decorated with @script
    if hasattr(function, "wrapped_function"):
        function = function.wrapped_function
    # convert the kwargs list to a dict
    kwargs: Dict[str, str] = {}
    for kwarg in kwargs_list:
        if "name" not in kwarg or "value" not in kwarg:
            continue
        # sanitize the key for python
        key = cast(str, serialize(kwarg["name"]))
        value = kwarg["value"]
        kwargs[key] = value

    if os.environ.get("hera__script_annotations", None) is None:
        # Do a simple replacement for hyphens to get valid Python parameter names.
        kwargs = {key.replace("-", "_"): value for key, value in kwargs.items()}
    else:
        kwargs = map_argo_inputs_to_function(function, kwargs)

    # The imported validate_arguments uses smart union by default just in case clients do not rely on it. This means that if a function uses a union
    # type for any of its inputs, then this will at least try to map those types correctly if the input object is
    # not a pydantic model with smart_union enabled
    _pydantic_mode = int(os.environ.get("hera__pydantic_mode", _PYDANTIC_VERSION))
    if _pydantic_mode == 2:
        from pydantic import validate_call  # type: ignore

        function = validate_call(function)
    else:
        if _PYDANTIC_VERSION == 1:
            from pydantic import validate_arguments
        else:
            from pydantic.v1 import validate_arguments  # type: ignore
        function = validate_arguments(function, config=dict(smart_union=True, arbitrary_types_allowed=True))  # type: ignore

    function = ignore_unmatched_kwargs(function)

    if os.environ.get("hera__script_annotations", None) is not None:
        output_annotations = _extract_return_annotation_output(function)

        if output_annotations:
            # This will save outputs returned from the function only. Any function parameters/artifacts marked as
            # outputs should be written to within the function itself.
            try:
                output = save_annotated_return_outputs(function(**kwargs), output_annotations)
            except Exception as e:
                save_dummy_outputs(output_annotations)
                raise e
            return output or None

    return function(**kwargs)


def _parse_args() -> argparse.Namespace:
    """Creates an argparse for the runner function.

    The returned argparse takes a module and function name as flags and a path to a json file as an argument.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--entrypoint", "-e", type=str, required=True)
    parser.add_argument("args_path", type=Path)
    return parser.parse_args()


def run() -> None:
    """Runs a function from a specific path using parsed arguments from Argo.

    Note that this prints the result of the function to stdout, which is the normal mode of operation for Argo. Any
    output of a Python function submitted via a `Script.source` field results in outputs sent to stdout.
    """
    args = _parse_args()
    # 1. Protect against trying to json.loads on empty files with inner `or r"[]`
    # 2. Protect against files containing `null` as text with outer `or []` (as a result of using
    #    `{{inputs.parameters}}` where the parameters key doesn't exist in `inputs`)
    kwargs_list = json.loads(args.args_path.read_text() or r"[]") or []
    assert isinstance(kwargs_list, List)
    result = _runner(args.entrypoint, kwargs_list)
    if not result:
        return

    if isinstance(result, (OutputV1, OutputV2)):
        print(serialize(result.result))
        exit(result.exit_code)

    print(serialize(result))
