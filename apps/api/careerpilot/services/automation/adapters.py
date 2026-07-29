from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ATSAdapter:
    name: str
    hosts: tuple[str, ...]
    submit_labels: tuple[str, ...] = ("submit", "submit application", "apply")
    field_selectors: tuple[str, ...] = (
        "input:not([type=hidden]):not([type=password]):not([type=submit])",
        "textarea",
        "select",
    )
    file_selectors: tuple[str, ...] = ("input[type=file]",)

    def matches(self, url: str) -> bool:
        host = (urlparse(url).hostname or "").casefold()
        return any(host == value or host.endswith(f".{value}") for value in self.hosts)

    def selectors(self) -> dict[str, str]:
        return {
            "fields": ", ".join(self.field_selectors),
            "resume": ", ".join(self.file_selectors),
            "submit": "button[type=submit], input[type=submit]",
        }


ADAPTERS = (
    ATSAdapter("greenhouse", ("greenhouse.io",)),
    ATSAdapter("lever", ("lever.co",)),
    ATSAdapter("ashby", ("ashbyhq.com",)),
    ATSAdapter("workday", ("myworkdayjobs.com", "workday.com")),
    ATSAdapter("smartrecruiters", ("smartrecruiters.com",)),
    ATSAdapter("icims", ("icims.com",)),
    ATSAdapter("taleo", ("taleo.net",)),
    ATSAdapter("successfactors", ("successfactors.com", "successfactors.eu")),
)
GENERIC = ATSAdapter("generic", ())


def adapter_for_url(url: str) -> ATSAdapter:
    return next((adapter for adapter in ADAPTERS if adapter.matches(url)), GENERIC)
