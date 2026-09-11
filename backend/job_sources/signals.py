import json

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from .models import JobSource


@receiver(post_save, sender=JobSource)
def sync_periodic_task(sender, instance, **kwargs):
    task_name = f'poll-source-{instance.id}'

    if not instance.enabled:
        PeriodicTask.objects.filter(name=task_name).delete()
        return

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=instance.poll_interval_minutes, period=IntervalSchedule.MINUTES,
    )
    PeriodicTask.objects.update_or_create(
        name=task_name,
        defaults={
            'task': 'ingestion.tasks.poll_source_task',
            'interval': schedule,
            'args': json.dumps([instance.id]),
        },
    )


@receiver(post_delete, sender=JobSource)
def remove_periodic_task(sender, instance, **kwargs):
    PeriodicTask.objects.filter(name=f'poll-source-{instance.id}').delete()