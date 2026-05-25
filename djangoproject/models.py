from django.db import models

class InfectedMachine(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    last_handshake_at = models.DateTimeField(null=True)
    dns_identifier = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=100)

class Job(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    infected_machine = models.ForeignKey(InfectedMachine, on_delete=models.CASCADE)
    raw_command = models.TextField()
    finished = models.BooleanField(default=False)
    finished_at = models.DateTimeField(null=True)
