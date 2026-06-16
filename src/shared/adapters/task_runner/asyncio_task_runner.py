import asyncio
import functools
import inspect
from typing import Callable

from src.shared.core.ports.task_runner import TaskRunnerPort

class AsyncioTaskRunner(TaskRunnerPort):
    """
    Implements TaskRunnerPort.
    - Async callables (coroutine functions) → scheduled as asyncio.create_task (runs in event loop)
    - Sync callables → offloaded to thread pool via run_in_executor (original behaviour)
    """
    def __init__(self):
        self._background_tasks: set = set()

    def add_task[**P](self, task: Callable[P, object], *args: P.args, **kwargs: P.kwargs) -> None:
        loop = asyncio.get_running_loop()
        if inspect.iscoroutinefunction(task):
            # Async task: runs in the event loop, can await anything freely
            t = loop.create_task(task(*args, **kwargs)) # type: ignore
            self._background_tasks.add(t)
            t.add_done_callback(self._background_tasks.discard)
        else:
            # Sync task: offloaded to thread pool (legacy behaviour)
            func = functools.partial(task, *args, **kwargs)
            future = loop.run_in_executor(None, func) # type: ignore
            self._background_tasks.add(future)
            future.add_done_callback(self._background_tasks.discard)
