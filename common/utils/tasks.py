from django.conf import settings


def enqueue_task(task, *args, **kwargs):
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return task.apply(args=args, kwargs=kwargs)
    return task.delay(*args, **kwargs)
