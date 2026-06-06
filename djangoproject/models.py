from __future__ import annotations

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
