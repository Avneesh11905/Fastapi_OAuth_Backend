import asyncio
import functools
from typing import Callable, Any, ParamSpec
from src.shared.core.ports.task_runner import TaskRunnerPort

P = ParamSpec("P")

class AsyncioTaskRunner(TaskRunnerPort):
    """
    Implements TaskRunnerPort by offloading synchronous functions 
    to a background thread pool.
    """
    def __init__(self):
        self._background_tasks = set()

    def add_task(self, task: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> None:
        loop = asyncio.get_running_loop()
        func = functools.partial(task, *args, **kwargs)
        future = loop.run_in_executor(None, func)
        self._background_tasks.add(future)
        future.add_done_callback(self._background_tasks.discard)
