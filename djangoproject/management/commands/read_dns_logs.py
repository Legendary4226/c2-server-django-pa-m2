from django.core.management.base import BaseCommand

from djangoproject.services.DnsLogMatcherService import DnsLogMatcherService
from djangoproject.services.DnsLogParserService import DnsLogParserService
from djangoproject.services.ExecService import ExecService


def read_new_lines() -> list[str]:
    import os, json
    from decouple import config

    logfile = config('DNS_LOG_FILE')
    dns_pointer_file = config('DNS_POINTER_FILE')

    # Load state
    try:
        with open(dns_pointer_file, 'r') as f:
            state = json.load(f)
    except:
        state = {'inode': None, 'line': 0}

    # Check if rotated
    current_inode = os.stat(logfile).st_ino
    if current_inode != state['inode']:
        state = {'inode': current_inode, 'line': 0}

    lines = []
    # Read from pointer
    with open(logfile, 'r') as f:
        for i, line in enumerate(f, 1):
            if i > state['line']:
                lines.append(line)
        state['line'] = i

    # Save state
    with open(dns_pointer_file, 'w') as f:
        json.dump(state, f)

    return lines

class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.dnsLogParser = DnsLogParserService()
        self.dnsLogMatcher = DnsLogMatcherService()
        self.exec = ExecService()

    def handle(self, *args, **kwargs):
        lines = read_new_lines()

        if len(lines) == 0:
            self.stdout.write('No new lines to process')
            return

        self.stdout.write('Processing ' + str(len(lines)) + ' lines...')

        for longLine in lines:
            line = longLine[63:]
            parsed = self.dnsLogParser.parse_line(line)
            if not parsed:
                continue

            client_ip, domain, _ = parsed
            matched = self.dnsLogMatcher.match_line(domain)
            if not matched:
                continue

            match_type, match = matched
            self.exec.process(match_type, match, client_ip)

        self.stdout.write('End of process')
