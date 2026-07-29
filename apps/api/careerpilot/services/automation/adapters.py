from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ATSAdapter:
    name: str
    hosts: tuple[str, ...]
    submit_labels: tuple[str, ...] = ("submit", "submit application")

    def matches(self, url: str) -> bool:
        host = urlparse(url).netloc.casefold()
        return any(value in host for value in self.hosts)

    def selectors(self) -> dict[str, str]:
        return {
            "fields": "input:not([type=password]), textarea, select",
            "resume": "input[type=file]",
            "submit": "button[type=submit], input[type=submit]",
        }


ADAPTERS = (
    ATSAdapter("greenhouse", ("greenhouse.io", "boards.greenhouse.io")),
    ATSAdapter("lever", ("lever.co", "jobs.lever.co")),
    ATSAdapter("ashby", ("ashbyhq.com",)),
    ATSAdapter("workday", ("myworkdayjobs.com", "workday.com")),
)
GENERIC = ATSAdapter("generic", ())


def adapter_for_url(url: str) -> ATSAdapter:
    return next((adapter for adapter in ADAPTERS if adapter.matches(url)), GENERIC)
