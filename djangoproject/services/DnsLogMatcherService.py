import re
from re import Match

from djangoproject.constants.DnsMatchEnum import DnsMatchEnum


class DnsLogMatcherService:

    def match_line(self, line: str) -> tuple[DnsMatchEnum, Match[str]] | None:

        for enum in DnsMatchEnum:
            match = re.match(enum.get_regex(), line, re.IGNORECASE)
            if match:
                return enum, match

        return None
