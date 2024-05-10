from typing import Any, Callable

from astroid import InferenceError, NodeNG
from astroid.typing import InferenceResult


def _infer(node: NodeNG) -> InferenceResult | None:
    try:
        return list(node.infer())[0]
    except InferenceError:
        return None


def default_return(default_value: Any = None):
    def wrapper(func: Callable) -> Callable:

        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return default_value

        return inner

    return wrapper
