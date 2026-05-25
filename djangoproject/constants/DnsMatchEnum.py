from enum import Enum


class DnsMatchEnum(Enum):
    GET_JOB = 1
    RETURN_JOB_FRAGMENT = 2
    JOB_FINISHED = 3

    def get_regex(self) -> str:
        if self == DnsMatchEnum.GET_JOB:
            return "^job.([a-z]+).tm-it.fr$"
        elif self == DnsMatchEnum.RETURN_JOB_FRAGMENT:
            return "^([a-z0-9]+).data.([0-9]+).job.([a-z]+).tm-it.fr$"
        elif self == DnsMatchEnum.JOB_FINISHED:
            return "^finished.([0-9]+).job.([a-z]+).tm-it.fr$"

        raise Exception("Unknown DnsMatchEnum")
