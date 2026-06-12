from typing import Callable, Any, ParamSpec
from src.shared.core.ports.task_runner import TaskRunnerPort

P = ParamSpec("P")

class CeleryTaskRunner(TaskRunnerPort):
    """
    Implements TaskRunnerPort by offloading tasks to Celery.
    Note: The 'task' passed here must be a registered Celery task (e.g. decorated with @celery_app.task)
    """
    def add_task(self, task: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> None:
        if hasattr(task, "delay"):
            task.delay(*args, **kwargs)
        else:
            raise ValueError(f"Task {task} is not a Celery task. Please decorate it with @celery_app.task.")
