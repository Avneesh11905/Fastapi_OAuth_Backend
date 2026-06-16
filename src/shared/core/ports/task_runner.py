from typing import Callable, Protocol

class TaskRunnerPort(Protocol):
    """
    Abstracts background task execution so our business logic and adapters
    don't need to be coupled to asyncio.create_task or Celery.
    """
    def add_task[**P](self, task: Callable[P, object], *args: P.args, **kwargs: P.kwargs) -> None:
        ...
