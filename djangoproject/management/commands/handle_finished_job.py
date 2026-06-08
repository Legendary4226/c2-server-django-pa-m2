import base64

from django.core.management.base import BaseCommand
from django.utils import timezone

from djangoproject.models import JobEndQueue


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        queue = JobEndQueue.objects.filter(processable_at__lte=timezone.now(), processed=False).order_by('created_at').first()
        if not queue:
            print("No pending queue")
            return

        print(f"Processing queue element #{queue.id} Job #{queue.job_id}")

        try:
            job = queue.job
            data_folder = job.data_folder_path()

            job.finished_at = timezone.now()
            job.save()

            chunks = job.get_sorted_chunks()
            with open(f"{data_folder}/extracted", "w") as extracted:
                for chunkFile in chunks:
                    with open(f"{data_folder}/{chunkFile}", "r") as chunk:
                        data = chunk.read().upper()
                        if (len(data) % 8) > 0:
                            data += '=' * (len(data) % 8)
                        extracted.write(
                            base64.b32decode(data).decode('UTF-8')
                        )

            print(f"End process queue #{queue.id} Job #{queue.job_id}: {len(chunks)} chunks merged in extracted")
        except Exception as e:
            print(f"Failed to process merge of chunks for queue #{queue.id} Job #{queue.job_id} {e}")

        queue.processed = True
        queue.save()
