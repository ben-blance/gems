from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask

class Command(BaseCommand):
    help = 'List all periodic tasks'

    def handle(self, *args, **options):
        tasks = PeriodicTask.objects.all()
        
        self.stdout.write(f'Total periodic tasks: {tasks.count()}\n')
        
        for task in tasks:
            self.stdout.write(f'Name: {task.name}')
            self.stdout.write(f'  Task: {task.task}')
            self.stdout.write(f'  Enabled: {task.enabled}')
            self.stdout.write(f'  Interval: {task.interval}')
            self.stdout.write(f'  Args: {task.args}')
            self.stdout.write('')