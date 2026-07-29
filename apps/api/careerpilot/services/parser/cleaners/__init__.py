import re


class TextCleaner:
    def clean(self, text: str) -> str:
        lines = []
        for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
            normalized = re.sub(r"[ \t]+", " ", line).strip()
            lines.append(normalized)
        return "\n".join(lines).strip()
