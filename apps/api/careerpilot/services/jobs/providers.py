from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

import httpx

from careerpilot.models.jobs import JobSource


class JobProvider(ABC):
    def __init__(self, source: JobSource, timeout: float = 30) -> None:
        self.source = source
        self.timeout = timeout

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]: ...


class GreenhouseProvider(JobProvider):
    def fetch(self) -> list[dict[str, Any]]:
        response = httpx.get(
            f"https://boards-api.greenhouse.io/v1/boards/{self.source.external_key}/jobs",
            params={"content": "true"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [
            {
                "external_id": str(item["id"]),
                "title": item["title"],
                "company": self.source.name,
                "description": item.get("content", ""),
                "location": item.get("location", {}).get("name"),
                "url": item.get("absolute_url"),
                "application_url": item.get("absolute_url"),
                "posted_at": item.get("updated_at"),
                "raw": item,
            }
            for item in response.json().get("jobs", [])
        ]


class LeverProvider(JobProvider):
    def fetch(self) -> list[dict[str, Any]]:
        response = httpx.get(
            f"https://api.lever.co/v0/postings/{self.source.external_key}",
            params={"mode": "json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [
            {
                "external_id": item["id"],
                "title": item["text"],
                "company": self.source.name,
                "description": item.get("descriptionPlain") or item.get("description", ""),
                "location": item.get("categories", {}).get("location"),
                "employment_type": item.get("categories", {}).get("commitment"),
                "url": item.get("hostedUrl"),
                "application_url": item.get("applyUrl"),
                "raw": item,
            }
            for item in response.json()
        ]


class AshbyProvider(JobProvider):
    def fetch(self) -> list[dict[str, Any]]:
        response = httpx.get(
            f"https://api.ashbyhq.com/posting-api/job-board/{self.source.external_key}",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [
            {
                "external_id": item.get("id") or item["jobUrl"],
                "title": item["title"],
                "company": self.source.name,
                "description": item.get("descriptionHtml", ""),
                "location": item.get("location"),
                "employment_type": item.get("employmentType"),
                "url": item.get("jobUrl"),
                "application_url": item.get("applyUrl") or item.get("jobUrl"),
                "posted_at": item.get("publishedAt"),
                "raw": item,
            }
            for item in response.json().get("jobs", [])
        ]


class WorkdayProvider(JobProvider):
    def fetch(self) -> list[dict[str, Any]]:
        url = self.source.source_url or self.source.configuration.get("url")
        if not url:
            raise ValueError("Workday source requires source_url")
        response = httpx.get(str(url), timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("jobPostings") or payload.get("jobs") or []
        return [_generic_item(item, self.source.name) for item in items]


class GenericJSONProvider(JobProvider):
    def fetch(self) -> list[dict[str, Any]]:
        if not self.source.source_url:
            raise ValueError("JSON source requires source_url")
        response = httpx.get(self.source.source_url, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        items = payload if isinstance(payload, list) else payload.get("jobs", [])
        return [_generic_item(item, self.source.name) for item in items]


class RSSProvider(JobProvider):
    def fetch(self) -> list[dict[str, Any]]:
        if not self.source.source_url:
            raise ValueError("RSS source requires source_url")
        response = httpx.get(self.source.source_url, timeout=self.timeout)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        values = []
        for item in root.findall(".//item"):
            link = item.findtext("link") or ""
            values.append(
                {
                    "external_id": item.findtext("guid") or link,
                    "title": item.findtext("title") or "Untitled role",
                    "company": self.source.name,
                    "description": item.findtext("description") or "",
                    "location": None,
                    "url": link,
                    "application_url": link,
                    "posted_at": item.findtext("pubDate"),
                    "raw": {"feed": str(self.source.source_url)},
                }
            )
        return values


def _generic_item(item: dict[str, Any], company: str) -> dict[str, Any]:
    url = item.get("url") or item.get("jobUrl") or item.get("externalPath") or ""
    return {
        "external_id": str(item.get("id") or item.get("jobReqId") or url),
        "title": item.get("title") or item.get("jobTitle") or "Untitled role",
        "company": item.get("company") or company,
        "description": item.get("description") or item.get("descriptionHtml") or "",
        "location": item.get("location") or item.get("locationsText"),
        "employment_type": item.get("employment_type") or item.get("employmentType"),
        "url": url,
        "application_url": item.get("application_url") or item.get("applyUrl") or url,
        "posted_at": item.get("posted_at") or item.get("postedOn"),
        "salary_min": item.get("salary_min"),
        "salary_max": item.get("salary_max"),
        "salary_currency": item.get("salary_currency"),
        "salary_period": item.get("salary_period"),
        "raw": item,
    }


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


PROVIDERS = {
    "greenhouse": GreenhouseProvider,
    "lever": LeverProvider,
    "ashby": AshbyProvider,
    "workday": WorkdayProvider,
    "json": GenericJSONProvider,
    "rss": RSSProvider,
}


def create_job_provider(source: JobSource) -> JobProvider:
    return PROVIDERS[source.provider](source)

