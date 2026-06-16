from typing import Callable

from src.shared.core.ports.task_runner import TaskRunnerPort

class CeleryTaskRunner(TaskRunnerPort):
    """
    Implements TaskRunnerPort by offloading tasks to Celery.
    Note: The 'task' passed here must be a registered Celery task (e.g. decorated with @celery_app.task)
    """
    def add_task[**P](self, task: Callable[P, object], *args: P.args, **kwargs: P.kwargs) -> None:
        if hasattr(task, "delay"):
            task.delay(*args, **kwargs)
        else:
            raise ValueError(f"Task {task} is not a Celery task. Please decorate it with @celery_app.task.")
