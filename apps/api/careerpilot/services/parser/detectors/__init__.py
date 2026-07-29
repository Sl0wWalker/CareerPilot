import re

SECTION_ALIASES = {
    "summary": {"summary", "profile", "professional summary", "objective"},
    "experience": {"experience", "work experience", "professional experience", "employment"},
    "education": {"education", "academic background"},
    "skills": {"skills", "technical skills", "core competencies", "technologies"},
    "projects": {"projects", "selected projects"},
    "certifications": {"certifications", "licenses & certifications", "certificates"},
    "awards": {"awards", "achievements", "honors"},
    "volunteer": {"volunteer", "volunteer experience"},
    "publications": {"publications", "research"},
}


class SectionDetector:
    def detect(self, text: str) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {"unclassified": []}
        current = "unclassified"
        aliases = {alias: name for name, values in SECTION_ALIASES.items() for alias in values}
        for line in text.splitlines():
            heading = re.sub(r"[^a-z& ]", "", line.lower()).strip()
            if heading in aliases:
                current = aliases[heading]
                sections.setdefault(current, [])
            elif line:
                sections.setdefault(current, []).append(line)
        return sections
