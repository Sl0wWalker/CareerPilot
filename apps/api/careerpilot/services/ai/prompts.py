from importlib.resources import files


def render_prompt(name: str, context: str) -> str:
    template = (
        files("careerpilot.services.ai.prompt_templates")
        .joinpath(f"{name}.md")
        .read_text(encoding="utf-8")
    )
    return template.replace("{{PROFILE}}", context)
