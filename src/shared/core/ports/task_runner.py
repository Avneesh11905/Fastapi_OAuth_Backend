from typing import Protocol, Callable, Any, ParamSpec

P = ParamSpec("P")

class TaskRunnerPort(Protocol):
    """
    Abstracts background task execution so our business logic and adapters
    don't need to be coupled to asyncio.create_task or Celery.
    """
    def add_task(self, task: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> None:
        ...
