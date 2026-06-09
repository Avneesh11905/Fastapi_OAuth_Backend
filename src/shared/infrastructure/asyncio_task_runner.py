import asyncio
from typing import Callable, Any, ParamSpec
import typing
from src.shared.core.ports.task_runner import TaskRunnerPort

P = ParamSpec("P")

class AsyncioTaskRunner(TaskRunnerPort):
    """
    Implements TaskRunnerPort using asyncio.create_task.
    This allows us to run background operations synchronously without 
    coupling the caller to the asyncio library.
    """
    def add_task(self, task: Callable[P, typing.Coroutine[Any, Any, Any]], *args: P.args, **kwargs: P.kwargs) -> None:
        asyncio.create_task(task(*args, **kwargs))
