from careerpilot.models import Company, Job, JobSource
from careerpilot.repositories.jobs import JobRepository
from careerpilot.services.jobs.normalization import (
    classify_workplace,
    job_fingerprint,
    normalize_location,
    normalize_salary,
    plain_text,
)
from careerpilot.services.jobs.providers import create_job_provider, parse_datetime


class JobIngestionService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def sync(self, source: JobSource) -> dict[str, int]:
        rows = create_job_provider(source).fetch()
        created = updated = skipped = 0
        for row in rows:
            description = plain_text(str(row.get("description") or ""))
            title = str(row.get("title") or "").strip()
            company_name = str(row.get("company") or source.name).strip()
            url = str(row.get("url") or row.get("application_url") or "").strip()
            if not title or not url:
                skipped += 1
                continue
            location = str(row.get("location")) if row.get("location") else None
            fingerprint = job_fingerprint(company_name, title, location, description)
            company = self.repository.get_or_create_company(Company(name=company_name))
            existing = self.repository.by_external(source.provider, str(row["external_id"]))
            salary_min, salary_max, currency, period = normalize_salary(row)
            city, region, country = normalize_location(location)
            values = {
                "company_id": company.id,
                "source_provider": source.provider,
                "external_id": str(row["external_id"]),
                "title": title,
                "description": description,
                "canonical_url": url,
                "application_url": row.get("application_url"),
                "location_raw": location,
                "city": city,
                "region": region,
                "country": country,
                "workplace_type": classify_workplace(title, description, location),
                "employment_type": row.get("employment_type"),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_currency": currency,
                "salary_period": period,
                "posted_at": parse_datetime(row.get("posted_at")),
                "fingerprint": fingerprint,
                "search_text": plain_text(f"{title} {company_name} {location or ''} {description}"),
                "raw_payload": row.get("raw", row),
            }
            if existing:
                self.repository.update_job(existing, values)
                updated += 1
            elif self.repository.by_fingerprint(fingerprint):
                skipped += 1
            else:
                self.repository.add_job(Job(**values))
                created += 1
        self.repository.mark_synced(source)
        return {"discovered": len(rows), "created": created, "updated": updated, "skipped": skipped}

