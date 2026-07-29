from collections.abc import Iterable
from pathlib import Path

from playwright.async_api import Page, async_playwright

from careerpilot.services.automation.adapters import ATSAdapter


class PlaywrightRunner:
    """Visible-browser runner that never submits without a separate approved action."""

    async def inspect(self, url: str, adapter: ATSAdapter, storage_state: Path | None = None):
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            state = (
                str(storage_state)
                if storage_state and storage_state.exists()
                else None
            )
            context = await browser.new_context(
                storage_state=state
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            fields = await self._fields(page, adapter)
            await browser.close()
            return fields

    async def fill(self, page: Page, adapter: ATSAdapter,
                   fields: Iterable[dict[str, object]]) -> None:
        selectors = adapter.selectors()
        controls = page.locator(selectors["fields"])
        for index, field in enumerate(fields):
            if field.get("value") is None or field.get("requires_review"):
                continue
            control = controls.nth(index)
            if await control.is_visible():
                await control.fill(str(field["value"]))
        # Intentionally no submit action here. Submission is a separate, approved workflow.

    @staticmethod
    async def _fields(page: Page, adapter: ATSAdapter) -> list[dict[str, object]]:
        controls = page.locator(adapter.selectors()["fields"])
        values = []
        for index in range(await controls.count()):
            control = controls.nth(index)
            if not await control.is_visible():
                continue
            label = await control.get_attribute("aria-label")
            if not label:
                identifier = await control.get_attribute("id")
                label_node = page.locator(f'label[for="{identifier}"]') if identifier else None
                label = (
                    await label_node.inner_text()
                    if label_node and await label_node.count()
                    else ""
                )
            kind = await control.get_attribute("type")
            if not kind:
                kind = await control.evaluate("(e) => e.tagName")
            values.append({
                "label": label or await control.get_attribute("name") or f"Field {index + 1}",
                "kind": kind,
                "required": await control.get_attribute("required") is not None,
            })
        return values
