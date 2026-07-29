from collections.abc import Iterable
from pathlib import Path
from typing import Any

from playwright.async_api import Locator, Page, async_playwright

from careerpilot.services.automation.adapters import ATSAdapter


class PlaywrightRunner:
    """Supervised browser mechanics with an invariant: never click final submit."""

    async def inspect(
        self,
        url: str,
        adapter: ATSAdapter,
        storage_state: Path | None = None,
        *,
        headless: bool = False,
    ) -> list[dict[str, object]]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)
            state = str(storage_state) if storage_state and storage_state.exists() else None
            context = await browser.new_context(storage_state=state)
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            fields = await self._fields(page, adapter)
            await browser.close()
            return fields

    async def fill(
        self,
        page: Page,
        adapter: ATSAdapter,
        fields: Iterable[dict[str, object]],
    ) -> list[dict[str, str]]:
        """Fill mapped controls by stable selector, returning non-fatal compatibility issues."""
        issues: list[dict[str, str]] = []
        for field in fields:
            if field.get("value") is None or field.get("requires_review"):
                continue
            selector = str(field.get("selector", ""))
            if not selector:
                issues.append({"label": str(field.get("label")), "reason": "missing_selector"})
                continue
            control = page.locator(selector).first
            if await control.count() == 0 or not await control.is_visible():
                issues.append({"label": str(field.get("label")), "reason": "selector_drift"})
                continue
            try:
                await self._fill_control(control, field["value"])
            except Exception as error:  # Playwright reports site-specific incompatibilities.
                issues.append({
                    "label": str(field.get("label")),
                    "reason": type(error).__name__,
                })
        return issues

    @staticmethod
    async def upload(page: Page, adapter: ATSAdapter, path: Path) -> bool:
        if not path.is_file():
            raise FileNotFoundError(path)
        control = page.locator(adapter.selectors()["resume"]).first
        if await control.count() == 0:
            return False
        await control.set_input_files(str(path))
        return True

    @staticmethod
    async def detect_interruptions(page: Page) -> list[str]:
        text = (await page.locator("body").inner_text()).casefold()
        checks = {
            "captcha": ("captcha", "verify you are human", "security check"),
            "mfa": ("verification code", "two-factor", "multi-factor", "one-time code"),
            "authentication": ("sign in", "log in", "create an account"),
        }
        return [name for name, phrases in checks.items() if any(item in text for item in phrases)]

    @staticmethod
    async def _fill_control(control: Locator, value: Any) -> None:
        tag = await control.evaluate("(element) => element.tagName.toLowerCase()")
        kind = (await control.get_attribute("type") or "").casefold()
        if tag == "select":
            try:
                await control.select_option(label=str(value))
            except Exception:
                await control.select_option(value=str(value))
        elif kind in {"checkbox", "radio"}:
            wanted = value if isinstance(value, bool) else str(value).casefold() in {
                "1", "true", "yes", "on",
            }
            await control.set_checked(wanted)
        else:
            await control.fill(str(value))

    @classmethod
    async def _fields(cls, page: Page, adapter: ATSAdapter) -> list[dict[str, object]]:
        controls = page.locator(adapter.selectors()["fields"])
        values: list[dict[str, object]] = []
        for index in range(await controls.count()):
            control = controls.nth(index)
            if not await control.is_visible():
                continue
            label = await cls._label(page, control)
            tag = await control.evaluate("(element) => element.tagName.toLowerCase()")
            kind = (await control.get_attribute("type") or tag).casefold()
            values.append({
                "label": label or f"Field {index + 1}",
                "kind": kind,
                "required": (
                    await control.get_attribute("required") is not None
                    or await control.get_attribute("aria-required") == "true"
                ),
                "selector": await cls._stable_selector(control, index),
                "options": await control.locator("option").all_text_contents()
                if tag == "select" else [],
            })
        return values

    @staticmethod
    async def _label(page: Page, control: Locator) -> str:
        label = await control.get_attribute("aria-label")
        if label:
            return label.strip()
        labelled_by = await control.get_attribute("aria-labelledby")
        if labelled_by:
            text = await page.locator(f"#{labelled_by}").all_inner_texts()
            if text:
                return " ".join(text).strip()
        identifier = await control.get_attribute("id")
        if identifier:
            labels = page.locator(f'label[for="{identifier}"]')
            if await labels.count():
                return (await labels.first.inner_text()).strip()
        placeholder = await control.get_attribute("placeholder")
        if placeholder:
            return placeholder.strip()
        return (await control.get_attribute("name") or "").strip()

    @staticmethod
    async def _stable_selector(control: Locator, index: int) -> str:
        identifier = await control.get_attribute("id")
        if identifier:
            return f"#{identifier}"
        name = await control.get_attribute("name")
        if name:
            return f'[name="{name}"]'
        return f"input, textarea, select >> nth={index}"
