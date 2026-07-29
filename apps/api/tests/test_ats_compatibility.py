import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

from careerpilot.services.automation.adapters import ADAPTERS, GENERIC
from careerpilot.services.automation.runner import PlaywrightRunner

FORM = """
<!doctype html>
<html><body>
  <form>
    <label for="first">First name</label>
    <input id="first" name="first_name" required>
    <label for="email">Email</label>
    <input id="email" name="email" type="email" aria-required="true">
    <label for="country">Country</label>
    <select id="country" name="country">
      <option value="">Choose</option>
      <option value="US">United States</option>
      <option value="CA">Canada</option>
    </select>
    <label for="remote">Open to remote work</label>
    <input id="remote" name="remote" type="checkbox">
    <label for="resume">Resume</label>
    <input id="resume" name="resume" type="file">
    <label for="sponsor">Will you require sponsorship?</label>
    <textarea id="sponsor" name="sponsorship"></textarea>
    <button id="final-submit" type="submit">Submit application</button>
  </form>
  <script>
    window.submitted = false;
    document.querySelector("form").addEventListener("submit", event => {
      event.preventDefault();
      window.submitted = true;
    });
  </script>
</body></html>
"""


def test_supported_ats_contracts():
    async def validate() -> None:
        resume = Path(__file__).with_name(".ats-test-resume.pdf")
        resume.write_bytes(b"%PDF-1.4 test fixture")
        try:
            runner = PlaywrightRunner()
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                for adapter in (*ADAPTERS, GENERIC):
                    page = await browser.new_page()
                    await page.set_content(FORM)
                    fields = await runner._fields(page, adapter)
                    assert [item["label"] for item in fields[:3]] == [
                        "First name", "Email", "Country",
                    ]
                    mapped = []
                    values = {
                        "First name": "Ada",
                        "Email": "ada@example.test",
                        "Country": "United States",
                        "Open to remote work": True,
                    }
                    for item in fields:
                        mapped.append({
                            **item,
                            "value": values.get(str(item["label"])),
                            "requires_review": (
                                "sponsorship" in str(item["label"]).casefold()
                            ),
                        })
                    assert await runner.fill(page, adapter, mapped) == []
                    assert await page.locator("#first").input_value() == "Ada"
                    assert await page.locator("#email").input_value() == "ada@example.test"
                    assert await page.locator("#country").input_value() == "US"
                    assert await page.locator("#remote").is_checked()
                    assert await page.locator("#sponsor").input_value() == ""
                    assert await runner.upload(page, adapter, resume)
                    assert await page.locator("#resume").evaluate(
                        "(element) => element.files.length"
                    ) == 1
                    assert not await page.evaluate("window.submitted")
                    await page.close()
                await browser.close()
        finally:
            resume.unlink(missing_ok=True)

    asyncio.run(validate())


def test_interruption_detection():
    async def validate() -> None:
        runner = PlaywrightRunner()
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(
                "<body>Sign in. Enter your verification code. Verify you are human.</body>"
            )
            assert await runner.detect_interruptions(page) == [
                "captcha", "mfa", "authentication",
            ]
            await browser.close()

    asyncio.run(validate())
