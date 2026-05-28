import re

class DnsLogParserService:

    def parse_line(self, line: str) -> tuple|None:
        match = re.match(
            r'([0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3})#[0-9]{1,7} \([A-Za-z0-9.]+\.data\.tm-it\.fr\): query: ([A-Za-z0-9.]+\.data\.tm-it\.fr) IN (A|TXT)',
            line[63:]
        )
        if not match:
            return None

        client_ip, domain, qtype = match.groups()
        return client_ip, domain, qtype
